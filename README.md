# QuizBlast V2

## Local
1. Copy `.env.example` to `.env`
2. Create and activate a virtualenv
3. Install requirements
4. Run migrations
5. Start server

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
# quizblast_v2
