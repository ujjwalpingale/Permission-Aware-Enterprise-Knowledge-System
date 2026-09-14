import time
import logging
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.app.core.config import settings
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
    """Orchestrates RAG pipeline: retrieval -> context construction -> Gemini LLM completion -> citations."""

    def __init__(self, retrieval_service: RetrievalService = None):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_CHAT_MODEL,
            temperature=0.0,
        )

    def answer_question(self, question: str, top_k: int = None) -> ChatResponse:
        logger.info(f"Processing question: {question}")
        
        # 1. Retrieve chunks with automatic 1-retry on network blip
        chunks = []
        for attempt in range(2):
            try:
                chunks = self.retrieval_service.retrieve_chunks(question, top_k=top_k)
                break
            except Exception as e:
                if attempt == 0 and ("getaddrinfo failed" in str(e) or "Connect" in str(e)):
                    logger.warning("Network connection blip during retrieval, retrying in 1s...")
                    time.sleep(1.0)
                else:
                    raise

        # 2. Check if any chunks retrieved
        if not chunks:
            logger.info("No chunks retrieved from vector store.")
            return ChatResponse(answer=NO_ANSWER_MESSAGE, citations=[])

        best_score = min([c.get("score", 999.0) for c in chunks]) if chunks else 999.0
        logger.info(f"Retrieved {len(chunks)} chunks. Best distance score: {best_score:.4f}")

        # 3. Construct context string
        context_str = build_context_string(chunks)

        # 4. Invoke Gemini LLM with 1-retry on network blip
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

        # 5. Extract citations if valid answer generated
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
