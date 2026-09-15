import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import RAGService
from backend.app.auth.authentication import get_current_user
from backend.app.db.models import User as DBUser
from backend.app.core.config import settings

logger = logging.getLogger("chat_api")
router = APIRouter()

# Global rag_service instance initialized on demand
_rag_service = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY is not properly configured in backend/.env.",
            )
        _rag_service = RAGService()
    return _rag_service


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: DBUser = Depends(get_current_user),
):
    """Permission-aware chat endpoint requiring valid JWT authenticated user."""
    try:
        # Process query strictly using authenticated JWT user
        service = get_rag_service()
        response = service.answer_question(question=request.question, user=current_user)
        return response
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Unhandled server error: {err_msg}", exc_info=True)
        if "getaddrinfo failed" in err_msg or "ConnectError" in err_msg or "ConnectTimeout" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network Connection Error: Unable to reach Google Gemini API servers. Please check your internet connection and try again.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while processing your request: {err_msg}",
        )

