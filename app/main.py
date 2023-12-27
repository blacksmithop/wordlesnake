from typing import List, Any
from pydantic import BaseModel
from fastapi import FastAPI, Request
from starlette.websockets import WebSocket, WebSocketDisconnect
import coloredlogs
import logging
from uuid import uuid4
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


coloredlogs.install(level="DEBUG")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


MIN_USERS = 4


class Payload(BaseModel):
    message: str
    id: str


class User(BaseModel):
    id: str
    username: str
    connection: Any


class Message(BaseModel):
    username: str
    message: str


class Notifier:
    def __init__(self):
        self.connections: List[User] = []
        self.generator = self.get_notification_generator()

    async def get_notification_generator(self):
        while True:
            message, id = yield
            await self._notify(message, id)

    async def push(self, id: str, msg: str):
        logger.error(f"ID: {id} | Message: {msg}")
        await self.generator.asend((msg, id))

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        data = await websocket.receive_json()
        username = data["username"]
        userID = uuid4().hex
        user = User(id=userID, username=username, connection=websocket)
        logger.debug(f"User: {username} ({userID})")
        await websocket.send_json({"id": userID})
        self.connections.append(user)

    def remove(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def _notify(self, message: str, id: str):
        logger.warning(f"Connections: {len(self.connections)}")
        living_connections = []
        userMatch: User = next(
            (item for item in self.connections if item.id == id),
            None,
        )
        if userMatch == None:
            return
        userID = userMatch.id
        username = userMatch.username
        while len(self.connections) > 0:
            # Looping like this is necessary in case a disconnection is handled
            user: User = self.connections.pop()
            if user.id == userID:  # don't send to self, handled in frontend
                logger.error(userID)
                continue
            websocket: WebSocket = user.connection
            await websocket.send_json(
                {"id": userID, "username": username, "message": message}
            )
            living_connections.append(user)
        self.connections = living_connections


notifier = Notifier()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Payload: {data}")
            resp = Message(**data)
            await websocket.send_json({"message": resp.message, "username": resp.username})
    except WebSocketDisconnect:
        notifier.remove(websocket)


@app.get("/push/{id}/{message}")
async def push_to_connected_websockets(id: str, message: str):
    logger.debug(f"Message: {message} from {id}")
    await notifier.push(id, message)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")


@app.on_event("startup")
async def startup():
    logger.debug(f"Starting API ✅")
    # Prime the push notification generator
    await notifier.generator.asend(None)
