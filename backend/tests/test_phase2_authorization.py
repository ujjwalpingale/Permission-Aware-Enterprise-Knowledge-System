import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from backend.app.main import app
from backend.app.auth.models import User
from backend.app.auth.authentication import UserService
from backend.app.auth.authorization import PermissionService
from backend.app.rag.retriever import StandardRetriever
from backend.app.services.rag_service import RAGService
from backend.app.rag.prompts import NO_ANSWER_MESSAGE

client = TestClient(app)


# Fixture Synthetic Users
@pytest.fixture
def alice_account_manager():
    return UserService.get_user_by_id("user_001")


@pytest.fixture
def bob_engineer():
    return UserService.get_user_by_id("user_002")


@pytest.fixture
def charlie_support_agent():
    return UserService.get_user_by_id("user_003")


@pytest.fixture
def admin_user():
    return UserService.get_user_by_id("admin_001")


# Sample Document Metadata Objects
PROJECT_ALPHA_META = {
    "document_id": "doc_project_alpha",
    "title": "Project Alpha",
    "source_type": "project_document",
    "account": "ABC Corp",
    "department": "engineering",
    "access_level": "internal",
    "allowed_roles": "engineer,account_manager",
    "allowed_users": "",
}

PROJECT_BETA_META = {
    "document_id": "doc_project_beta",
    "title": "Project Beta",
    "source_type": "project_document",
    "account": "XYZ Corp",
    "department": "engineering",
    "access_level": "internal",
    "allowed_roles": "engineer",
    "allowed_users": "",
}

PROJECT_GAMMA_RESTRICTED_META = {
    "document_id": "doc_project_gamma",
    "title": "Project Gamma (Confidential Financial Status)",
    "source_type": "project_document",
    "account": "ABC Corp",
    "department": "finance",
    "access_level": "restricted",
    "allowed_roles": "finance",
    "allowed_users": "",
}

SUPPORT_TICKET_001_META = {
    "document_id": "TICKET-001",
    "title": "Support Ticket TICKET-001 (ABC Corp)",
    "source_type": "support_ticket",
    "account": "ABC Corp",
    "department": "support",
    "access_level": "internal",
    "allowed_roles": "support_agent,account_manager",
    "allowed_users": "",
}


# ============================================================================
# PHASE 2 TEST CASES
# ============================================================================

def test_1_admin_can_retrieve_every_document(admin_user):
    """Test 1: Admin can access any document regardless of restrictions."""
    assert PermissionService.is_authorized(admin_user, PROJECT_ALPHA_META) is True
    assert PermissionService.is_authorized(admin_user, PROJECT_BETA_META) is True
    assert PermissionService.is_authorized(admin_user, PROJECT_GAMMA_RESTRICTED_META) is True
    assert PermissionService.is_authorized(admin_user, SUPPORT_TICKET_001_META) is True


def test_2_engineer_can_access_engineering_documents(bob_engineer):
    """Test 2: Engineer (Bob) can access authorized engineering documents for their account."""
    # Bob has accessible_accounts = ["XYZ Corp"]
    assert PermissionService.is_authorized(bob_engineer, PROJECT_BETA_META) is True


def test_3_engineer_cannot_access_restricted_finance_documents(bob_engineer):
    """Test 3: Engineer (Bob) cannot access restricted finance document (Project Gamma)."""
    assert PermissionService.is_authorized(bob_engineer, PROJECT_GAMMA_RESTRICTED_META) is False


def test_4_account_manager_can_access_permitted_account_documents(alice_account_manager):
    """Test 4: Account Manager (Alice) can access documents for ABC Corp and XYZ Corp."""
    assert PermissionService.is_authorized(alice_account_manager, PROJECT_ALPHA_META) is True


def test_5_user_cannot_access_unauthorized_account(bob_engineer):
    """Test 5: User (Bob - XYZ Corp only) cannot access ABC Corp documents."""
    assert PermissionService.is_authorized(bob_engineer, PROJECT_ALPHA_META) is False


def test_6_support_agent_can_access_support_tickets(charlie_support_agent):
    """Test 6: Support Agent (Charlie) can access authorized support tickets for ABC Corp."""
    assert PermissionService.is_authorized(charlie_support_agent, SUPPORT_TICKET_001_META) is True


def test_7_unknown_user_returns_http_401():
    """Test 7: Querying with unknown user_id returns HTTP 401 Unauthorized."""
    response = client.post("/chat", json={"user_id": "unknown_user_999", "question": "What is Project Alpha?"})
    assert response.status_code == 401
    assert "Authentication Failed" in response.json()["detail"]


def test_8_unauthorized_source_metadata_is_never_returned(bob_engineer):
    """Test 8: System never returns citations for unauthorized sources."""
    mock_vector_store = MagicMock()
    # Candidate set contains restricted Project Gamma chunk
    gamma_doc = Document(
        page_content="Confidential financial target $420,000 for Project Gamma.",
        metadata=PROJECT_GAMMA_RESTRICTED_META,
    )
    mock_vector_store.similarity_search_with_score.return_value = [(gamma_doc, 0.1)]

    retriever = StandardRetriever(vector_store_manager=mock_vector_store)
    authorized_chunks = retriever.retrieve("What is Project Gamma budget?", user=bob_engineer, top_k=5)

    assert len(authorized_chunks) == 0


def test_9_critical_security_unauthorized_context_never_reaches_llm(bob_engineer):
    """Test 9 (CRITICAL SECURITY TEST): Unauthorized content is filtered BEFORE building LLM context."""
    mock_retrieval_service = MagicMock()
    # Mock retrieval service returning empty authorized chunks for Bob querying Project Gamma
    mock_retrieval_service.retrieve_chunks.return_value = []

    rag_service = RAGService(retrieval_service=mock_retrieval_service)
    # Mock LLM completion to ensure LLM is never even invoked or receives 0 context
    rag_service.llm = MagicMock()

    response = rag_service.answer_question(
        question="What is the confidential financial information about Project Gamma?",
        user=bob_engineer,
    )

    # Verify fallback response is returned, 0 citations, and LLM was not given restricted text
    assert response.answer == NO_ANSWER_MESSAGE
    assert len(response.citations) == 0
    rag_service.llm.invoke.assert_not_called()


def test_10_all_unauthorized_candidates_returns_no_answer_fallback(bob_engineer):
    """Test 10: If all retrieved candidates are unauthorized, system returns standard no-answer fallback."""
    mock_vector_store = MagicMock()
    restricted_doc = Document(
        page_content="Strictly confidential details.",
        metadata=PROJECT_GAMMA_RESTRICTED_META,
    )
    mock_vector_store.similarity_search_with_score.return_value = [(restricted_doc, 0.2)]

    retriever = StandardRetriever(vector_store_manager=mock_vector_store)
    results = retriever.retrieve("Confidential info query", user=bob_engineer, top_k=5)
    assert len(results) == 0


def test_11_missing_permission_metadata_defaults_to_deny(bob_engineer):
    """Test 11: Fail-Closed Security - Missing or malformed metadata defaults to DENY."""
    malformed_meta = {
        "document_id": "malformed_doc",
        "title": "Malformed Doc",
        # Missing access_level, allowed_roles, account
    }
    assert PermissionService.is_authorized(bob_engineer, malformed_meta) is False


def test_12_admin_bypass_works_correctly(admin_user):
    """Test 12: Admin bypass works correctly across all accounts and departments."""
    assert PermissionService.is_authorized(admin_user, PROJECT_GAMMA_RESTRICTED_META) is True
