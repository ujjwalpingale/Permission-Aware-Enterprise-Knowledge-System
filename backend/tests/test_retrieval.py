from unittest.mock import MagicMock
from langchain_core.documents import Document
from backend.app.rag.retriever import StandardRetriever


def test_retriever_returns_chunks_with_metadata_and_scores():
    """Test retriever formats search results with content, metadata, and distance scores."""
    mock_vector_store = MagicMock()

    sample_doc = Document(
        page_content="The team committed to delivering the payment integration by September 25, 2026.",
        metadata={
            "document_id": "doc_project_alpha",
            "title": "Project Alpha",
            "source_type": "project_document",
        },
    )
    mock_vector_store.similarity_search_with_score.return_value = [(sample_doc, 0.123)]

    retriever = StandardRetriever(vector_store_manager=mock_vector_store)
    results = retriever.retrieve("What delivery date was promised to ABC Corp?", top_k=5)

    assert len(results) == 1
    assert "September 25, 2026" in results[0]["content"]
    assert results[0]["metadata"]["document_id"] == "doc_project_alpha"
    assert results[0]["metadata"]["title"] == "Project Alpha"
    assert results[0]["score"] == 0.123
    mock_vector_store.similarity_search_with_score.assert_called_once_with(
        query="What delivery date was promised to ABC Corp?",
        top_k=5,
    )
