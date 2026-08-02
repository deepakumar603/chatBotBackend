from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse, ModelInfo
from app.services import ChatService

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/models", response_model=list[ModelInfo])
def list_models():
    service = ChatService()
    return service.get_integrated_models()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    service = ChatService()
    content = service.get_response(request.message, request.model, request.provider)
    return {"response": content}
