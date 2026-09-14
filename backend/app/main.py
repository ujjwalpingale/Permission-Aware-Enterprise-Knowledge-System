import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas.chat import HealthResponse
from backend.app.api.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Permission-Aware Enterprise RAG API",
    description="Phase 1 - Basic RAG Enterprise Knowledge Assistant Backend",
    version="1.0.0",
)

# Enable CORS for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.include_router(chat_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")
