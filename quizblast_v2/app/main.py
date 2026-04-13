from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
import os

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static/index.html"))

@app.get("/player")
def player():
    return FileResponse(os.path.join(BASE_DIR, "static/player.html"))

@app.get("/host")
def host():
    return FileResponse(os.path.join(BASE_DIR, "static/host.html"))

@app.get("/admin")
def admin():
    return FileResponse(os.path.join(BASE_DIR, "static/admin.html"))

@app.get("/health")
def health():
    return {"ok": True}
