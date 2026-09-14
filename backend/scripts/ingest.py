import sys
import site
from pathlib import Path

# Ensure user site packages are accessible
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Add workspace root to sys.path to enable backend package imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.rag.loaders import DocumentLoader
from backend.app.rag.chunker import DocumentChunker
from backend.app.rag.embeddings import get_embedding_function
from backend.app.rag.vector_store import VectorStoreManager


def main():
    print("=" * 50)
    print("Starting Enterprise Data Ingestion Pipeline (Gemini)")
    print("=" * 50)

    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        print("\nERROR: GEMINI_API_KEY is not set in backend/.env!")
        print("Please configure your GEMINI_API_KEY before running ingestion.\n")
        sys.exit(1)

    data_dir = ROOT_DIR / "backend" / "data"

    # Step 1: Loading
    print("\nLoading documents...")
    documents = DocumentLoader.load_directory(data_dir)
    print(f"Loaded {len(documents)} documents.")

    if not documents:
        print("No documents found to ingest.")
        sys.exit(0)

    # Step 2: Chunking
    print("\nCreating chunks...")
    chunker = DocumentChunker(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    chunks = chunker.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    # Step 3: Embeddings & Vector Storage
    print("\nGenerating Gemini embeddings...")
    embedding_fn = get_embedding_function(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_EMBEDDING_MODEL,
    )
    print(f"Using embedding model: {settings.GEMINI_EMBEDDING_MODEL}")

    print("\nStoring vectors in ChromaDB...")
    vector_store_manager = VectorStoreManager(
        persist_directory=str(ROOT_DIR / "backend" / "chroma_db"),
        embedding_function=embedding_fn,
    )
    added_count = vector_store_manager.add_documents(chunks)
    print(f"Stored {added_count} vectors into ChromaDB at {vector_store_manager.persist_directory}.")
    print("Ingestion completed successfully.\n")


if __name__ == "__main__":
    main()
