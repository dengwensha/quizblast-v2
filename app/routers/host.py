from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import User, Room, Question, Player, Answer
from app.schemas import CreateRoomRequest
from app.security import decode_access_token
from app.services.game_service import GameService
from app.websocket_manager import manager

router = APIRouter(prefix="/api/host", tags=["host"])


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Oturum gerekli")

    user_id = int(decode_access_token(access_token))
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")

    return user


@router.post("/rooms")
async def create_room(
    payload: CreateRoomRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = Room(
        code=GameService.make_room_code(),
        title=payload.title,
        question_time=payload.question_time,
        host_user_id=user.id,
        status="lobby",
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    return {"room_code": room.code, "title": room.title}


@router.post("/rooms/{room_code}/start")
async def start_room(
    room_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = db.execute(
        select(Room).where(
            Room.code == room_code.upper(),
            Room.host_user_id == user.id,
        )
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    question = db.execute(
        select(Question).where(Question.is_active.is_(True)).order_by(Question.id.asc())
    ).scalars().first()

    if not question:
        raise HTTPException(status_code=400, detail="Aktif soru bulunamadı")

    GameService.open_question(db, room, question.id)
    payload = GameService.public_room_state(db, room)
    await manager.broadcast(room.code, payload)

    return {"ok": True}


@router.post("/rooms/{room_code}/reveal")
async def reveal_answer(
    room_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = db.execute(
        select(Room).where(
            Room.code == room_code.upper(),
            Room.host_user_id == user.id,
        )
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    live = GameService.get_live_state(room.code)
    if not live or not live.get("question_id"):
        raise HTTPException(status_code=400, detail="Aktif soru yok")

    question = db.get(Question, int(live["question_id"]))
    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    room.status = "reveal"
    db.add(room)

    answers = db.execute(
        select(Answer).where(
            Answer.room_id == room.id,
            Answer.question_id == question.id,
        )
    ).scalars().all()

    awarded_players: set[int] = set()
    for answer in answers:
        if answer.is_correct and answer.player_id not in awarded_players:
            player = db.get(Player, answer.player_id)
            if player:
                player.score += 100
                db.add(player)
                awarded_players.add(answer.player_id)

    db.commit()

    payload = GameService.public_room_state(db, room)
    await manager.broadcast(room.code, payload)

    return {"ok": True}


@router.post("/rooms/{room_code}/next")
async def next_question(
    room_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = db.execute(
        select(Room).where(
            Room.code == room_code.upper(),
            Room.host_user_id == user.id,
        )
    ).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    question = GameService.next_question_for_room(db, room)

    if not question:
        room.status = "finished"
        db.add(room)
        db.commit()

        payload = GameService.public_room_state(db, room)
        await manager.broadcast(room.code, payload)
        return {"ok": True, "finished": True}

    GameService.open_question(db, room, question.id)
    payload = GameService.public_room_state(db, room)
    await manager.broadcast(room.code, payload)

    return {"ok": True, "finished": False}
