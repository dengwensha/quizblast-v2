from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import os
import json

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
clients: list[WebSocket] = []

questions_file = os.path.join(BASE_DIR, "data", "questions.json")

with open(questions_file, "r", encoding="utf-8") as f:
    questions = json.load(f)

current_question_index = 0


def get_current_question():
    if 0 <= current_question_index < len(questions):
        q = questions[current_question_index]
        return {
            "question": q["question"],
            "options": q["options"]
        }
    return {
        "question": "Soru yok",
        "options": ["-", "-", "-", "-"]
    }


@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static/index.html"))


@app.get("/host")
def host():
    return FileResponse(os.path.join(BASE_DIR, "static/host.html"))


@app.get("/health")
def health():
    return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_question_index

    await websocket.accept()
    clients.append(websocket)

    try:
        await websocket.send_text(json.dumps({
            "type": "question",
            "data": get_current_question()
        }))

        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            if data["type"] == "next_question":
                if current_question_index < len(questions) - 1:
                    current_question_index += 1

                payload = json.dumps({
                    "type": "question",
                    "data": get_current_question()
                })

                disconnected = []
                for client in clients:
                    try:
                        await client.send_text(payload)
                    except Exception:
                        disconnected.append(client)

                for dc in disconnected:
                    if dc in clients:
                        clients.remove(dc)

            elif data["type"] == "restart_quiz":
                current_question_index = 0

                payload = json.dumps({
                    "type": "question",
                    "data": get_current_question()
                })

                disconnected = []
                for client in clients:
                    try:
                        await client.send_text(payload)
                    except Exception:
                        disconnected.append(client)

                for dc in disconnected:
                    if dc in clients:
                        clients.remove(dc)

            elif data["type"] == "answer":
                payload = json.dumps({
                    "type": "answer_info",
                    "player_answer": data["answer"]
                })

                disconnected = []
                for client in clients:
                    try:
                        await client.send_text(payload)
                    except Exception:
                        disconnected.append(client)

                for dc in disconnected:
                    if dc in clients:
                        clients.remove(dc)

    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)