from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class CreateRoomRequest(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    question_time: int = Field(default=20, ge=5, le=120)


class JoinRoomRequest(BaseModel):
    room_code: str = Field(min_length=4, max_length=12)
    player_name: str = Field(min_length=1, max_length=50)


class QuestionCreateRequest(BaseModel):
    text: str = Field(min_length=5, max_length=300)
    choice_a: str = Field(min_length=1, max_length=255)
    choice_b: str = Field(min_length=1, max_length=255)
    choice_c: str = Field(min_length=1, max_length=255)
    choice_d: str = Field(min_length=1, max_length=255)
    correct_index: int = Field(ge=0, le=3)
    category: str = Field(default="Genel", max_length=100)
    hint: str = Field(default="", max_length=255)


class SubmitAnswerRequest(BaseModel):
    room_code: str
    player_id: int
    choice_index: int = Field(ge=0, le=3)
