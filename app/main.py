from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "QuizBlast running"}

@app.get("/health")
def health():
    return {"ok": True}