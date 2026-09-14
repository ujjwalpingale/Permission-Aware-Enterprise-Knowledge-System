import logging
from pathlib import Path
from typing import Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.rag.loaders import DocumentLoader
from backend.app.rag.chunker import DocumentChunker
from backend.app.rag.embeddings import get_embedding_function
from backend.app.rag.vector_store import VectorStoreManager

logger = logging.getLogger("ingestion_service")


class IngestionService:
    """Service to handle loading, chunking, embedding, and indexing documents into ChromaDB."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent / "data")
        self.chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def run_ingestion(self) -> Dict[str, Any]:
        """Runs the document ingestion pipeline."""
        logger.info(f"Starting ingestion from data directory: {self.data_dir}")
        
        # 1. Load documents
        raw_documents = DocumentLoader.load_directory(self.data_dir)
        doc_count = len(raw_documents)
        logger.info(f"Loaded {doc_count} raw documents.")

        if doc_count == 0:
            return {"status": "success", "documents_loaded": 0, "chunks_created": 0, "vectors_stored": 0}

        # 2. Chunk documents
        chunks = self.chunker.split_documents(raw_documents)
        chunk_count = len(chunks)
        logger.info(f"Created {chunk_count} chunks.")

        # 3. Embeddings & Vector Store
        embedding_fn = get_embedding_function(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_EMBEDDING_MODEL,
        )

        vector_store_manager = VectorStoreManager(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=embedding_fn,
        )

        # 4. Add documents to vector store
        added_count = vector_store_manager.add_documents(chunks)
        logger.info(f"Stored {added_count} vectors in ChromaDB successfully.")

        return {
            "status": "success",
            "documents_loaded": doc_count,
            "chunks_created": chunk_count,
            "vectors_stored": added_count,
            "total_collection_count": vector_store_manager.count(),
        }
