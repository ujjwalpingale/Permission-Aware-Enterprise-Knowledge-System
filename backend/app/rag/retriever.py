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
        """Retrieves top_k authorized chunks for the given user with similarity scores.
        
        Fail-Closed: If user is None or unauthenticated, returns empty list [].
        """
        if not user:
            logger.warning("Unauthenticated retrieval attempt. Returning empty result.")
            return []

        # Retrieve a broader candidate set to ensure top_k authorized items remain after filtering
        candidate_k = max(top_k * 3, 15)
        search_results = self.vector_store_manager.similarity_search_with_score(
            query=query,
            top_k=candidate_k,
        )

        authorized_results = []
        for doc, score in search_results:
            is_allowed = PermissionService.is_authorized(user=user, doc_metadata=doc.metadata)
            doc_id = doc.metadata.get("document_id", "unknown")

            if is_allowed:
                authorized_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
                if len(authorized_results) >= top_k:
                    break
            else:
                logger.info(f"Filtered out unauthorized chunk during retrieval: doc_id={doc_id} user={user.id}")

        logger.info(f"Retrieval complete for user={user.id}: {len(authorized_results)} authorized chunk(s) selected from {len(search_results)} candidates.")
        return authorized_results
