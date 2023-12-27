from fastapi import FastAPI, WebSocket
from pydantic import BaseModel


class Message(BaseModel):
    message: str


app = FastAPI()


@app.websocket("/ws/message")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        resp: dict = await websocket.receive_json()
        resp = Message(**resp)
        message = resp.message
        print(f"Message: {message}")
        await websocket.send_json({"message": message})
