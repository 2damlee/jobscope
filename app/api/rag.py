import time
from collections import defaultdict, deque

from fastapi import APIRouter, Body, HTTPException, Request, status

from app.config import RAG_RATE_LIMIT_REQUESTS, RAG_RATE_LIMIT_WINDOW_SECONDS
from app.schemas import RagAskRequest, RagAskResponse
from app.services.rag_service import ask_question

router = APIRouter(prefix="/rag", tags=["rag"])

_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request) -> None:
    now = time.monotonic()
    key = _client_key(request)
    hits = _hits[key]

    while hits and now - hits[0] > RAG_RATE_LIMIT_WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= RAG_RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many RAG requests. Please try again later.",
        )

    hits.append(now)


@router.post("/ask", response_model=RagAskResponse)
def ask_rag(request: Request, payload: RagAskRequest = Body(...)):
    _check_rate_limit(request)

    return ask_question(
        question=payload.question,
        category=payload.category,
        location=payload.location,
        seniority=payload.seniority,
        top_k=payload.top_k,
    )
