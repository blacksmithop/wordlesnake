from typing import List, Any
from pydantic import BaseModel
from fastapi import FastAPI
from starlette.websockets import WebSocket, WebSocketDisconnect
import coloredlogs
import logging
from uuid import uuid4

coloredlogs.install(level="DEBUG")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

app = FastAPI()

MIN_USERS = 4

class Payload(BaseModel):
    message: str
    id: str


class User(BaseModel):
    id: str
    username: str
    connection: Any


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
        living_connections = []
        userMatch: User = next(
            (item for item in self.connections if item.id == id),
            None,
        )
        if userMatch == None:
            return
        userID = userMatch.id
        while len(self.connections) > 0:
            # Looping like this is necessary in case a disconnection is handled
            # during await websocket.send_text(message)
            user: User = self.connections.pop()
            websocket = user.connection
            await websocket.send_json(
                {"id": userID, "username": user.username, "message": message}
            )
            living_connections.append(user)
        self.connections = living_connections


notifier = Notifier()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Message:{data}")
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        notifier.remove(websocket)


@app.get("/push/{id}/{message}")
async def push_to_connected_websockets(id: str, message: str):
    logger.debug(f"Message: {message} from {id}")
    await notifier.push(id, message)


@app.on_event("startup")
async def startup():
    logger.debug(f"Starting API ✅")
    # Prime the push notification generator
    await notifier.generator.asend(None)
