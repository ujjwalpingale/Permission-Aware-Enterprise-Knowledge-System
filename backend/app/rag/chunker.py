from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Document chunker wrapping LangChain splitters while preserving all permission metadata."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits a list of Documents into smaller chunks, preserving all metadata including permission fields."""
        chunks = self.text_splitter.split_documents(documents)
        
        REQUIRED_KEYS = [
            "source_type",
            "source_file",
            "document_id",
            "title",
            "department",
            "account",
            "access_level",
            "allowed_roles",
            "allowed_users",
        ]

        # Ensure metadata consistency across chunks
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            for req_key in REQUIRED_KEYS:
                if req_key not in chunk.metadata:
                    if req_key == "access_level":
                        chunk.metadata[req_key] = "restricted"  # Fail-closed default
                    elif req_key in ["allowed_roles", "allowed_users"]:
                        chunk.metadata[req_key] = ""
                    else:
                        chunk.metadata[req_key] = "unknown"

        return chunks
