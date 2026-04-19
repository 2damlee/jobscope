from fastapi import APIRouter, Body

from app.schemas import RagAskRequest, RagAskResponse
from app.services.rag_service import ask_question

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ask", response_model=RagAskResponse)
def ask_rag(request: RagAskRequest = Body(...)):
    return ask_question(
        question=request.question,
        category=request.category,
        location=request.location,
        seniority=request.seniority,
        top_k=request.top_k,
    )