from typing import List, Dict, Any
from backend.app.rag.vector_store import VectorStoreManager


class StandardRetriever:
    """Retriever component for performing vector similarity search against vector store."""

    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant chunks with metadata and similarity score."""
        search_results = self.vector_store_manager.similarity_search_with_score(
            query=query,
            top_k=top_k,
        )

        formatted_results = []
        for doc, score in search_results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            })

        return formatted_results
