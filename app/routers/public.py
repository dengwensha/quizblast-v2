import time
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import Room, Player, Answer, Question
from app.schemas import JoinRoomRequest, SubmitAnswerRequest
from app.services.game_service import GameService
from app.websocket_manager import manager
from app.rate_limit import RateLimiter
from app.utils import get_client_ip
from app.config import get_settings

router = APIRouter(prefix="/api/public", tags=["public"])
settings = get_settings()


@router.get("/rooms/{room_code}")
def get_room(
    room_code: str,
    db: Session = Depends(get_db),
):
    room = db.execute(
        select(Room).where(Room.code == room_code.upper())
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    return GameService.public_room_state(db, room)


@router.get("/rooms/{room_code}/recover")
def recover_room_player(
    room_code: str,
    player_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    room = db.execute(
        select(Room).where(Room.code == room_code.upper())
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    if not player_session:
        raise HTTPException(status_code=401, detail="Oyuncu oturumu yok")

    player = db.execute(
        select(Player).where(
            Player.room_id == room.id,
            Player.session_token == player_session,
        )
    ).scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Oyuncu oturumu bulunamadı")

    return {
        "player_id": player.id,
        "player_name": player.name,
        "room_code": room.code,
        "score": player.score,
    }


@router.post("/rooms/join")
def join_room(
    payload: JoinRoomRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    client_ip = get_client_ip(request)
    RateLimiter.hit(
        f"join:{client_ip}:{payload.room_code.upper()}",
        limit=15,
        window_seconds=60,
    )

    room = db.execute(
        select(Room).where(Room.code == payload.room_code.upper())
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    existing_session = request.cookies.get("player_session")
    if existing_session:
        existing_player = db.execute(
            select(Player).where(
                Player.room_id == room.id,
                Player.session_token == existing_session,
            )
        ).scalar_one_or_none()

        if existing_player:
            return {
                "player_id": existing_player.id,
                "room_code": room.code,
                "recovered": True,
            }

    session_token = secrets.token_urlsafe(24)
    player = Player(
        room_id=room.id,
        name=payload.player_name.strip(),
        session_token=session_token,
    )

    db.add(player)
    db.commit()
    db.refresh(player)

    response.set_cookie(
        key="player_session",
        value=session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )

    return {
        "player_id": player.id,
        "room_code": room.code,
        "recovered": False,
    }


@router.post("/answers")
async def submit_answer(
    payload: SubmitAnswerRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = get_client_ip(request)
    RateLimiter.hit(
        f"answer:{client_ip}:{payload.room_code.upper()}:{payload.player_id}",
        limit=12,
        window_seconds=30,
    )

    room = db.execute(
        select(Room).where(Room.code == payload.room_code.upper())
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    live = GameService.get_live_state(room.code)
    if not live or room.status != "live":
        raise HTTPException(status_code=400, detail="Şu anda cevap kabul edilmiyor")

    now_ms = int(time.time() * 1000)
    if now_ms > int(live["closes_at_ms"]):
        GameService.auto_reveal_if_needed(db, room)
        payload_state = GameService.public_room_state(db, room)
        await manager.broadcast(room.code, payload_state)
        raise HTTPException(status_code=400, detail="Süre doldu")

    player = db.get(Player, payload.player_id)
    if not player or player.room_id != room.id:
        raise HTTPException(status_code=404, detail="Oyuncu bulunamadı")

    question = db.get(Question, int(live["question_id"]))
    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    existing = db.execute(
        select(Answer).where(
            Answer.room_id == room.id,
            Answer.question_id == question.id,
            Answer.player_id == player.id,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Bu soru zaten cevaplandı")

    response_ms = max(0, now_ms - int(live["opened_at_ms"]))

    answer = Answer(
        room_id=room.id,
        question_id=question.id,
        player_id=player.id,
        choice_index=payload.choice_index,
        is_correct=(payload.choice_index == question.correct_index),
        response_ms=response_ms,
    )

    db.add(answer)
    db.commit()

    payload_state = GameService.public_room_state(db, room)
    await manager.broadcast(room.code, payload_state)

    return {"ok": True}
