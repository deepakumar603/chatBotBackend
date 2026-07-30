from fastapi import FastAPI
from app.routers import router

app = FastAPI(title="ChatBot Backend", version="0.1.0")
app.include_router(router)


@app.get("/", tags=["root"])
def read_root():
    return {"message": "ChatBot Backend is running"}
