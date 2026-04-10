from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static/index.html"))

@app.get("/host")
def host():
    return FileResponse(os.path.join(BASE_DIR, "static/host.html"))

@app.get("/health")
def health():
    return {"ok": True}
from fastapi import WebSocket

clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            for client in clients:
                await client.send_text(data)
    except:
        clients.remove(websocket)