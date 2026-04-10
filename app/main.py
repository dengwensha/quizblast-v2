from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/host")
def host():
    return FileResponse("static/host.html")

@app.get("/health")
def health():
    return {"ok": True}