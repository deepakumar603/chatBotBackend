from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    model: str | None = None
    provider: str | None = None


class ModelInfo(BaseModel):
    provider: str
    model: str


class ChatResponse(BaseModel):
    response: str
