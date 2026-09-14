import logging
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, status, UploadFile, File

from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import RAGService
from backend.app.services.ingestion_service import IngestionService
from backend.app.auth.authentication import UserService
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
async def chat_endpoint(request: ChatRequest):
    """Permission-aware chat endpoint requiring valid authenticated user_id."""
    # 1. Authenticate user
    user = UserService.get_user_by_id(request.user_id)
    if not user:
        logger.warning(f"Authentication failure: Unknown user_id='{request.user_id}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication Failed: User ID '{request.user_id}' is not recognized.",
        )

    try:
        # 2. Process query for authenticated user
        service = get_rag_service()
        response = service.answer_question(question=request.question, user=user)
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


@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Endpoint to upload documents (.md, .txt, .json) and ingest them into ChromaDB."""
    try:
        data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "project_docs"
        data_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for file in files:
            file_path = data_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)

        # Trigger ingestion service
        ingestion_service = IngestionService()
        result = ingestion_service.run_ingestion()

        # Invalidate global rag_service to force reload vector store on next query
        global _rag_service
        _rag_service = None

        return {
            "status": "success",
            "message": f"Successfully uploaded and ingested {len(saved_files)} document(s).",
            "saved_files": saved_files,
            "ingestion_result": result,
        }
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and ingest uploaded documents: {str(e)}",
        )
