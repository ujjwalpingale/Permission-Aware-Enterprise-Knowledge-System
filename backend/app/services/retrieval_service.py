from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.rag.embeddings import get_embedding_function
from backend.app.rag.vector_store import VectorStoreManager
from backend.app.rag.retriever import StandardRetriever


class RetrievalService:
    """Service encapsulating retrieval pipeline for user queries."""

    def __init__(self, vector_store_manager: VectorStoreManager = None):
        if vector_store_manager:
            self.vector_store_manager = vector_store_manager
        else:
            embedding_fn = get_embedding_function(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_EMBEDDING_MODEL,
            )
            self.vector_store_manager = VectorStoreManager(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=embedding_fn,
            )
        
        self.retriever = StandardRetriever(vector_store_manager=self.vector_store_manager)

    def retrieve_chunks(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        k = top_k if top_k is not None else settings.TOP_K
        return self.retriever.retrieve(query=query, top_k=k)
