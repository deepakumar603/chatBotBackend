from fastapi import APIRouter
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Placeholder implementation. Replace with actual chat logic.
    return {"response": f"Echo: {request.message}"}
