import time
from fastapi import HTTPException
from redis import Redis
from app.config import get_settings

settings = get_settings()
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class RateLimiter:
    @staticmethod
    def hit(key: str, limit: int, window_seconds: int) -> None:
        now = int(time.time())
        bucket = now // window_seconds
        redis_key = f"rl:{key}:{bucket}"
        count = redis_client.incr(redis_key)
        if count == 1:
            redis_client.expire(redis_key, window_seconds + 2)
        if count > limit:
            raise HTTPException(status_code=429, detail="Çok fazla istek gönderildi")
