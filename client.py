# gradio_app.py
import gradio as gr
from websockets.sync.client import connect
from json import dumps

ws = connect("ws://localhost:8000/ws")

PAYLOAD = {
    "username": "Abhinav"
}
ws.send(dumps(PAYLOAD))

def send_message(input_text):
    ws.send(input_text)
    response = ws.recv()
    return response

iface = gr.Interface(fn=send_message, inputs="text", outputs="text", live=True)
iface.launch()
