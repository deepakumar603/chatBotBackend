from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.services import ChatService

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    service = ChatService()
    content = service.get_response(request.message)
    return {"response": content}
