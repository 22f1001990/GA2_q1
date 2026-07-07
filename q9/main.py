from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import time
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

T = 53
RATE_LIMIT = 17
WINDOW_SECONDS = 10

idempotency_store = {}
client_requests = {}

@app.post("/orders", status_code=201)
async def create_order(
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key")

    if idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]

    order_id = str(uuid.uuid4())
    body = {"id": order_id, "status": "created"}
    idempotency_store[idempotency_key] = body
    return body

@app.get("/orders")
async def list_orders(limit: int = 10, cursor: Optional[str] = None):
    if limit < 1:
        limit = 1

    start_id = 1
    if cursor:
        try:
            start_id = int(cursor) + 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    end_id = min(T, start_id + limit - 1)
    items = [{"id": order_id, "status": "catalog"} for order_id in range(start_id, end_id + 1)]

    next_cursor = str(end_id) if end_id < T else None
    return {"items": items, "next_cursor": next_cursor}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        window_start = now - WINDOW_SECONDS

        timestamps = client_requests.get(client_id, [])
        timestamps = [ts for ts in timestamps if ts >= window_start]

        if len(timestamps) >= RATE_LIMIT:
            retry_after = max(1, int(WINDOW_SECONDS - (now - timestamps[0])))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)
        client_requests[client_id] = timestamps

    return await call_next(request)
