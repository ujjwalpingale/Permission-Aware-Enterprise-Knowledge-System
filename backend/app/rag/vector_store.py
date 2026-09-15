import hashlib
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings


class VectorStoreManager:
    """Manages ChromaDB vector store operations including document indexing and similarity search."""

    def __init__(
        self,
        persist_directory: str,
        embedding_function: Embeddings,
        collection_name: str = "enterprise_knowledge",
    ):
        self.persist_directory = str(Path(persist_directory).resolve())
        self.embedding_function = embedding_function
        self.collection_name = collection_name
        self.vector_store: Optional[Chroma] = None
        self._init_vector_store()

    def _init_vector_store(self):
        """Initializes or loads the persistent Chroma vector store using langchain-chroma."""
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory,
        )

    def generate_chunk_id(self, chunk: Document, idx: int) -> str:
        """Generates a deterministic unique ID for a document chunk."""
        doc_id = chunk.metadata.get("document_id", "doc")
        content_hash = hashlib.md5(chunk.page_content.encode("utf-8")).hexdigest()[:8]
        return f"{doc_id}_chunk_{idx}_{content_hash}"

    def add_documents(self, documents: List[Document]) -> int:
        """Adds documents to Chroma vector store idempotently."""
        if not documents:
            return 0

        ids = [self.generate_chunk_id(doc, i) for i, doc in enumerate(documents)]
        
        # Add or upsert documents
        self.vector_store.add_documents(documents=documents, ids=ids)
        return len(documents)

    def similarity_search_with_score(
        self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Performs vector similarity search with pre-retrieval ChromaDB metadata filter."""
        if not self.vector_store:
            return []
        
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filter,
        )
        return results

    def count(self) -> int:
        """Returns total document count in collection."""
        if not self.vector_store:
            return 0
        try:
            return self.vector_store._collection.count()
        except Exception:
            return 0
