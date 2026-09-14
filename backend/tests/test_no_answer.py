from unittest.mock import MagicMock
from backend.app.services.rag_service import RAGService
from backend.app.rag.prompts import NO_ANSWER_MESSAGE


def test_no_answer_returned_when_no_chunks_retrieved():
    """Test RAG service returns exact no-answer message when vector retriever finds 0 matching chunks."""
    mock_retrieval_service = MagicMock()
    mock_retrieval_service.retrieve_chunks.return_value = []

    rag_service = RAGService(retrieval_service=mock_retrieval_service)
    response = rag_service.answer_question("What was the company revenue in 2024?")

    assert response.answer == NO_ANSWER_MESSAGE
    assert len(response.citations) == 0
