from fastapi import FastAPI, Request
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from collections import deque
import time
import uuid
import logging
import json

app = FastAPI()

startup_time = time.time()

# Prometheus counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# Keep last 1000 logs
logs = deque(maxlen=1000)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    http_requests_total.inc()

    entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    }

    logs.append(entry)

    logger.info(json.dumps(entry))

    return response


@app.get("/work")
def work(n: int):
    # simulate work
    total = 0
    for i in range(n):
        total += i

    return {
        "email": "22f1001990@ds.study.iitm.ac.in",
        "done": n
    }


@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "uptime_s": time.time() - startup_time
    }


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/logs/tail")
def tail(limit: int = 10):
    return list(logs)[-limit:]