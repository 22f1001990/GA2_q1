from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict

EMAIL = "22f1001990@ds.study.iitm.ac.in"
API_KEY = "ak_lqbhgayvofswd4wxa5v0wdw7"

app = FastAPI()

# Allow the grader's browser to call your endpoint
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or the exam domain if specified
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Event(BaseModel):
    user: str
    amount: float
    ts: int


class AnalyticsRequest(BaseModel):
    events: list[Event]


@app.post("/analytics")
def analytics(
    payload: AnalyticsRequest,
    x_api_key: str | None = Header(
    default=None,
    alias="X-API-Key"
)
):
    print("Received X-API-Key:", x_api_key)
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    total_events = len(payload.events)

    unique_users = len({e.user for e in payload.events})

    revenue = sum(e.amount for e in payload.events if e.amount > 0)

    totals = defaultdict(float)
    for e in payload.events:
        if e.amount > 0:
            totals[e.user] += e.amount

    top_user = max(totals, key=totals.get) if totals else ""

    return {
        "email": EMAIL,
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user,
    }