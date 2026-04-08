from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router

load_dotenv()

app = FastAPI(
    title="LangGraph Agent Platform",
    version="1.0.0",
    description="Modular multi-agent framework — drop a file in /agents or /tools to extend.",
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
