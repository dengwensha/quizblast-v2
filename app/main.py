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
players = {}
answered_players = set()


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


def get_correct_letter():
    correct_index = questions[current_question_index]["correct"]
    return ["A", "B", "C", "D"][correct_index]


async def broadcast(payload: dict):
    disconnected = []
    for client in clients:
        try:
            await client.send_text(json.dumps(payload))
        except Exception:
            disconnected.append(client)

    for dc in disconnected:
        if dc in clients:
            clients.remove(dc)


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
    global current_question_index, answered_players

    await websocket.accept()
    clients.append(websocket)

    try:
        await websocket.send_text(json.dumps({
            "type": "question",
            "data": get_current_question()
        }))

        await websocket.send_text(json.dumps({
            "type": "leaderboard",
            "players": players
        }))

        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            if data["type"] == "join":
                player_name = data["name"].strip()
                if player_name and player_name not in players:
                    players[player_name] = 0

                await broadcast({
                    "type": "leaderboard",
                    "players": players
                })

            elif data["type"] == "next_question":
                if current_question_index < len(questions) - 1:
                    current_question_index += 1

                answered_players = set()

                await broadcast({
                    "type": "question",
                    "data": get_current_question()
                })

            elif data["type"] == "restart_quiz":
                current_question_index = 0
                answered_players = set()
                for name in players:
                    players[name] = 0

                await broadcast({
                    "type": "question",
                    "data": get_current_question()
                })

                await broadcast({
                    "type": "leaderboard",
                    "players": players
                })

            elif data["type"] == "answer":
                player_name = data["name"].strip()
                answer = data["answer"]

                if player_name in answered_players:
                    await websocket.send_text(json.dumps({
                        "type": "info",
                        "message": "Bu soruya zaten cevap verdin."
                    }))
                    continue

                answered_players.add(player_name)

                correct_letter = get_correct_letter()
                is_correct = answer == correct_letter

                if player_name not in players:
                    players[player_name] = 0

                if is_correct:
                    players[player_name] += 10

                await websocket.send_text(json.dumps({
                    "type": "answer_result",
                    "correct": is_correct,
                    "correct_answer": correct_letter,
                    "your_answer": answer,
                    "score": players[player_name]
                }))

                await broadcast({
                    "type": "leaderboard",
                    "players": players
                })

                await broadcast({
                    "type": "host_answer_info",
                    "player": player_name,
                    "answer": answer,
                    "correct": is_correct
                })

            elif data["type"] == "show_answer":
                await broadcast({
                    "type": "show_answer",
                    "correct_answer": get_correct_letter()
                })

    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)