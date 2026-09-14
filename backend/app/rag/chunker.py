from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Document chunker wrapping LangChain splitters while preserving metadata."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits a list of Documents into smaller chunks, preserving all metadata."""
        chunks = self.text_splitter.split_documents(documents)
        
        # Ensure metadata consistency across chunks
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            # Ensure required keys exist
            for req_key in ["source_type", "source_file", "document_id", "title"]:
                if req_key not in chunk.metadata:
                    chunk.metadata[req_key] = "unknown"

        return chunks
