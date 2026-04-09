from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="host"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("choice_a", sa.String(length=255), nullable=False),
        sa.Column("choice_b", sa.String(length=255), nullable=False),
        sa.Column("choice_c", sa.String(length=255), nullable=False),
        sa.Column("choice_d", sa.String(length=255), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="Genel"),
        sa.Column("hint", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="lobby"),
        sa.Column("question_time", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("host_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rooms_code", "rooms", ["code"], unique=True)

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("session_token", sa.String(length=128), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_players_room_id", "players", ["room_id"], unique=False)
    op.create_index("ix_players_session_token", "players", ["session_token"], unique=True)

    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("choice_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("response_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_answers_room_id", "answers", ["room_id"], unique=False)
    op.create_index("ix_answers_question_id", "answers", ["question_id"], unique=False)
    op.create_index("ix_answers_player_id", "answers", ["player_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_answers_player_id", table_name="answers")
    op.drop_index("ix_answers_question_id", table_name="answers")
    op.drop_index("ix_answers_room_id", table_name="answers")
    op.drop_table("answers")

    op.drop_index("ix_players_session_token", table_name="players")
    op.drop_index("ix_players_room_id", table_name="players")
    op.drop_table("players")

    op.drop_index("ix_rooms_code", table_name="rooms")
    op.drop_table("rooms")

    op.drop_table("questions")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
