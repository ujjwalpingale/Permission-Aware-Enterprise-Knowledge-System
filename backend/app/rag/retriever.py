import logging
from typing import List, Dict, Any, Optional
from backend.app.rag.vector_store import VectorStoreManager
from backend.app.auth.models import User
from backend.app.auth.authorization import PermissionService

logger = logging.getLogger("retriever")


class StandardRetriever:
    """Permission-aware retriever component.
    
    Security Principle:
    Authorization filtering happens BEFORE candidate chunks are passed to RAG service or LLM context.
    """

    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager

    def retrieve(self, query: str, user: Optional[User], top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top_k authorized chunks for the given user with pre-retrieval ChromaDB metadata filtering.

        Fail-Closed: If user is None or unauthenticated, returns empty list [].
        """
        if not user:
            logger.warning("Unauthenticated retrieval attempt. Returning empty result.")
            return []

        # 1. Generate authoritative pre-retrieval ChromaDB filter
        auth_filter = PermissionService.get_retrieval_filter(user)

        # 2. Execute similarity search with filter applied directly inside ChromaDB BEFORE results are returned
        search_results = self.vector_store_manager.similarity_search_with_score(
            query=query,
            top_k=top_k,
            filter=auth_filter,
        )

        authorized_results = []
        for doc, score in search_results:
            # Defensive check using PermissionService.can_access_document
            if PermissionService.can_access_document(user=user, document=doc.metadata):
                authorized_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
            else:
                doc_id = doc.metadata.get("document_id", "unknown")
                user_id = getattr(user, "id", "unknown")
                logger.warning(f"Defensive check filtered unauthorized chunk: doc_id={doc_id} user={user_id}")

        user_id = getattr(user, "id", "unknown")
        logger.info(f"Pre-retrieval vector search complete for user={user_id}: {len(authorized_results)} chunk(s) returned.")
        return authorized_results
