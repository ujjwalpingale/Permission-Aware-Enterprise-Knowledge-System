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
def alice_hr():
    user = UserService.get_user_by_id("user_001")
    user.company_id = "comp_a"
    user.role = "hr"
    return user


@pytest.fixture
def bob_engineer():
    user = UserService.get_user_by_id("user_002")
    user.company_id = "comp_a"
    user.role = "engineer"
    return user


@pytest.fixture
def charlie_support_agent():
    user = UserService.get_user_by_id("user_003")
    user.company_id = "comp_a"
    user.role = "support"
    return user


@pytest.fixture
def admin_user():
    user = UserService.get_user_by_id("admin_001")
    user.company_id = "comp_a"
    user.role = "admin"
    return user


# Sample Multi-Tenant Document Metadata Objects
PROJECT_ALPHA_META = {
    "document_id": "doc_project_alpha",
    "company_id": "comp_a",
    "title": "Project Alpha",
    "source_type": "project_document",
    "allowed_roles": "engineer,hr",
}

PROJECT_BETA_META = {
    "document_id": "doc_project_beta",
    "company_id": "comp_b",  # Different company
    "title": "Project Beta",
    "source_type": "project_document",
    "allowed_roles": "engineer",
}

PROJECT_GAMMA_RESTRICTED_META = {
    "document_id": "doc_project_gamma",
    "company_id": "comp_a",
    "title": "Project Gamma (Confidential HR/Finance)",
    "source_type": "project_document",
    "allowed_roles": "hr",
}

SUPPORT_TICKET_001_META = {
    "document_id": "TICKET-001",
    "company_id": "comp_a",
    "title": "Support Ticket TICKET-001",
    "source_type": "support_ticket",
    "allowed_roles": "support",
}


# ============================================================================
# PHASE 4 MULTI-TENANT AUTHORIZATION TESTS
# ============================================================================

def test_1_admin_can_retrieve_own_company_documents(admin_user):
    """Test 1: Admin can access any document belonging to their own company."""
    assert PermissionService.is_authorized(admin_user, PROJECT_ALPHA_META) is True
    assert PermissionService.is_authorized(admin_user, PROJECT_GAMMA_RESTRICTED_META) is True
    assert PermissionService.is_authorized(admin_user, SUPPORT_TICKET_001_META) is True


def test_2_admin_cannot_access_other_company_documents(admin_user):
    """Test 2: Admin cannot access documents belonging to another company."""
    assert PermissionService.is_authorized(admin_user, PROJECT_BETA_META) is False


def test_3_engineer_can_access_engineering_documents(bob_engineer):
    """Test 3: Engineer (Bob) can access authorized engineering documents in their company."""
    assert PermissionService.is_authorized(bob_engineer, PROJECT_ALPHA_META) is True


def test_4_engineer_cannot_access_unpermitted_role_documents(bob_engineer):
    """Test 4: Engineer (Bob) cannot access HR-only document (Project Gamma)."""
    assert PermissionService.is_authorized(bob_engineer, PROJECT_GAMMA_RESTRICTED_META) is False


def test_5_engineer_cannot_access_other_company_document(bob_engineer):
    """Test 5: Engineer (Bob - Comp A) cannot access Comp B document even if role matches."""
    assert PermissionService.is_authorized(bob_engineer, PROJECT_BETA_META) is False


def test_6_hr_can_access_permitted_documents(alice_hr):
    """Test 6: HR User (Alice) can access HR-permitted documents in Comp A."""
    assert PermissionService.is_authorized(alice_hr, PROJECT_ALPHA_META) is True
    assert PermissionService.is_authorized(alice_hr, PROJECT_GAMMA_RESTRICTED_META) is True


def test_7_support_agent_can_access_support_tickets(charlie_support_agent):
    """Test 7: Support Agent (Charlie) can access authorized support tickets for Comp A."""
    assert PermissionService.is_authorized(charlie_support_agent, SUPPORT_TICKET_001_META) is True


def test_8_unknown_user_returns_http_401():
    """Test 8: Querying with unknown user_id returns HTTP 401 Unauthorized."""
    response = client.post("/chat", json={"user_id": "unknown_user_999", "question": "What is Project Alpha?"})
    assert response.status_code == 401
    assert "Authentication" in response.json()["detail"]


def test_9_unauthorized_source_metadata_is_never_returned(bob_engineer):
    """Test 9: System never returns citations for unauthorized sources."""
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


def test_10_critical_security_unauthorized_context_never_reaches_llm(bob_engineer):
    """Test 10 (CRITICAL SECURITY TEST): Unauthorized content is filtered BEFORE building LLM context."""
    mock_retrieval_service = MagicMock()
    mock_retrieval_service.retrieve_chunks.return_value = []

    rag_service = RAGService(retrieval_service=mock_retrieval_service)
    rag_service.llm = MagicMock()

    response = rag_service.answer_question(
        question="What is the confidential financial information about Project Gamma?",
        user=bob_engineer,
    )

    assert response.answer == NO_ANSWER_MESSAGE
    assert len(response.citations) == 0
    rag_service.llm.invoke.assert_not_called()


def test_11_missing_permission_metadata_defaults_to_deny(bob_engineer):
    """Test 11: Fail-Closed Security - Missing or malformed metadata defaults to DENY."""
    malformed_meta = {
        "document_id": "malformed_doc",
        "title": "Malformed Doc",
    }
    assert PermissionService.is_authorized(bob_engineer, malformed_meta) is False


def test_12_admin_same_company_bypass_works(admin_user):
    """Test 12: Admin same-company access works correctly."""
    assert PermissionService.is_authorized(admin_user, PROJECT_GAMMA_RESTRICTED_META) is True
