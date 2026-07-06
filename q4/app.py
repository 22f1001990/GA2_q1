from fastapi import FastAPI, HTTPException
import redis

app = FastAPI()

# Connect to Redis service in docker-compose
r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)


@app.post("/hit/{key}")
def hit(key: str):
    count = r.incr(key)
    return {
        "key": key,
        "count": count
    }


@app.get("/count/{key}")
def count(key: str):
    value = r.get(key)
    return {
        "key": key,
        "count": int(value) if value else 0
    }


@app.get("/healthz")
def health():
    try:
        r.ping()
        return {
            "status": "ok",
            "redis": "up"
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable"
        )