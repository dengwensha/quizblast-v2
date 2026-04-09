from collections import defaultdict
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, room_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[room_code].append(websocket)

    def disconnect(self, room_code: str, websocket: WebSocket) -> None:
        if websocket in self.connections.get(room_code, []):
            self.connections[room_code].remove(websocket)

    async def broadcast(self, room_code: str, payload: dict) -> None:
        alive: list[WebSocket] = []
        for ws in self.connections.get(room_code, []):
            try:
                await ws.send_json(payload)
                alive.append(ws)
            except Exception:
                pass
        self.connections[room_code] = alive


manager = WebSocketManager()
