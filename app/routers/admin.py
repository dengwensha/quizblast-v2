from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import User, Question
from app.schemas import QuestionCreateRequest
from app.security import decode_access_token

router = APIRouter(prefix="/api/admin", tags=["admin"])


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


@router.get("/questions")
def list_questions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    questions = db.execute(
        select(Question).order_by(Question.id.desc())
    ).scalars().all()

    return [
        {
            "id": q.id,
            "text": q.text,
            "choices": [q.choice_a, q.choice_b, q.choice_c, q.choice_d],
            "correct_index": q.correct_index,
            "category": q.category,
            "hint": q.hint,
            "is_active": q.is_active,
        }
        for q in questions
    ]


@router.post("/questions")
def create_question(
    payload: QuestionCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question = Question(
        text=payload.text.strip(),
        choice_a=payload.choice_a.strip(),
        choice_b=payload.choice_b.strip(),
        choice_c=payload.choice_c.strip(),
        choice_d=payload.choice_d.strip(),
        correct_index=payload.correct_index,
        category=payload.category.strip(),
        hint=payload.hint.strip(),
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return {"ok": True, "id": question.id}
