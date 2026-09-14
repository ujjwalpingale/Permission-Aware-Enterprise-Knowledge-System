import time
import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.app.core.config import settings
from backend.app.auth.models import User
from backend.app.schemas.chat import Citation, ChatResponse
from backend.app.services.retrieval_service import RetrievalService
from backend.app.rag.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    NO_ANSWER_MESSAGE,
    build_context_string,
)

logger = logging.getLogger("rag_service")


class RAGService:
    """Orchestrates permission-aware RAG pipeline: authorization -> retrieval -> context construction -> Gemini LLM completion -> authorized citations."""

    def __init__(self, retrieval_service: RetrievalService = None):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_CHAT_MODEL,
            temperature=0.0,
        )

    def answer_question(self, question: str, user: Optional[User], top_k: int = None) -> ChatResponse:
        """Answers user question strictly using authorized context chunks."""
        if not user:
            logger.warning("RAG question requested without valid user. Returning no-answer fallback.")
            return ChatResponse(answer=NO_ANSWER_MESSAGE, citations=[])

        logger.info(f"Processing question for user={user.id} (role={user.role}): '{question}'")
        
        # 1. Retrieve authorized chunks (pre-LLM permission filtering)
        chunks = []
        for attempt in range(2):
            try:
                chunks = self.retrieval_service.retrieve_chunks(query=question, user=user, top_k=top_k)
                break
            except Exception as e:
                if attempt == 0 and ("getaddrinfo failed" in str(e) or "Connect" in str(e)):
                    logger.warning("Network connection blip during retrieval, retrying in 1s...")
                    time.sleep(1.0)
                else:
                    raise

        # 2. Check if any authorized chunks retrieved
        if not chunks:
            logger.info(f"No authorized chunks retrieved for user={user.id}. Returning fail-closed no-answer response.")
            return ChatResponse(answer=NO_ANSWER_MESSAGE, citations=[])

        best_score = min([c.get("score", 999.0) for c in chunks]) if chunks else 999.0
        logger.info(f"Retrieved {len(chunks)} authorized chunks. Best distance score: {best_score:.4f}")

        # 3. Construct context string (Contains ONLY authorized chunks)
        context_str = build_context_string(chunks)

        # 4. Invoke Gemini LLM
        formatted_system = SYSTEM_PROMPT.format(no_answer_message=NO_ANSWER_MESSAGE)
        formatted_user = USER_PROMPT_TEMPLATE.format(question=question, context=context_str)

        messages = [
            SystemMessage(content=formatted_system),
            HumanMessage(content=formatted_user),
        ]

        response = None
        for attempt in range(2):
            try:
                response = self.llm.invoke(messages)
                break
            except Exception as e:
                if attempt == 0 and ("getaddrinfo failed" in str(e) or "Connect" in str(e)):
                    logger.warning("Network connection blip during LLM completion, retrying in 1s...")
                    time.sleep(1.0)
                else:
                    raise

        answer_text = response.content.strip() if response and response.content else NO_ANSWER_MESSAGE

        # 5. Extract citations (Contains ONLY authorized source metadata)
        citations = []
        if NO_ANSWER_MESSAGE not in answer_text:
            seen_docs = set()
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                doc_id = meta.get("document_id", "unknown")
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    citations.append(
                        Citation(
                            document_id=doc_id,
                            title=meta.get("title", "Untitled Document"),
                            source_type=meta.get("source_type", "document"),
                        )
                    )

        return ChatResponse(answer=answer_text, citations=citations)
