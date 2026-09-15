import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings

from backend.app.auth.models import User as DemoUser
from backend.app.db.models import User as DBUser
from backend.app.auth.authorization import PermissionService
from backend.app.rag.vector_store import VectorStoreManager
from backend.app.rag.retriever import StandardRetriever


# ============================================================================
# 1. PERMISSION SERVICE FILTER GENERATION TESTS
# ============================================================================

def test_1_admin_filter_contains_own_company_only():
    """Test 1: Admin filter generates company_id equality filter."""
    user = DBUser(id="admin_1", company_id="comp_alpha", role="admin", email="admin@alpha.com", full_name="Admin Alpha")
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {"company_id": "comp_alpha"}


def test_2_engineer_filter_contains_company_and_role_flag():
    """Test 2: Engineer filter generates company_id + role_engineer=True."""
    user = DBUser(id="eng_1", company_id="comp_alpha", role="engineer", email="eng@alpha.com", full_name="Eng Alpha")
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {
        "$and": [
            {"company_id": "comp_alpha"},
            {"role_engineer": True},
        ]
    }


def test_3_hr_filter_contains_company_and_role_flag():
    """Test 3: HR filter generates company_id + role_hr=True."""
    user = DBUser(id="hr_1", company_id="comp_alpha", role="hr", email="hr@alpha.com", full_name="HR Alpha")
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {
        "$and": [
            {"company_id": "comp_alpha"},
            {"role_hr": True},
        ]
    }


def test_4_sales_filter_contains_company_and_role_flag():
    """Test 4: Sales filter generates company_id + role_sales=True."""
    user = DBUser(id="sales_1", company_id="comp_alpha", role="sales", email="sales@alpha.com", full_name="Sales Alpha")
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {
        "$and": [
            {"company_id": "comp_alpha"},
            {"role_sales": True},
        ]
    }


def test_5_support_filter_contains_company_and_role_flag():
    """Test 5: Support filter generates company_id + role_support=True."""
    user = DBUser(id="sup_1", company_id="comp_alpha", role="support", email="sup@alpha.com", full_name="Support Alpha")
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {
        "$and": [
            {"company_id": "comp_alpha"},
            {"role_support": True},
        ]
    }


def test_6_invalid_role_fails_closed():
    """Test 6: Invalid/unknown employee role fails closed with unmatchable filter."""
    user = DBUser(id="bad_1", company_id="comp_alpha", role="unauthorized_role", email="bad@alpha.com", full_name="Bad User")
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {"company_id": "INVALID_ROLE_DENY"}


def test_7_missing_user_fails_closed():
    """Test 7: None user fails closed with unmatchable filter."""
    filter_dict = PermissionService.get_retrieval_filter(None)
    assert filter_dict == {"company_id": "UNAUTHENTICATED_DENY"}


def test_8_missing_company_id_fails_closed():
    """Test 8: User missing company_id fails closed."""
    user = DemoUser(id="no_comp", name="No Comp", role="engineer", department="engineering")
    user.company_id = ""
    filter_dict = PermissionService.get_retrieval_filter(user)
    assert filter_dict == {"company_id": "UNAUTHENTICATED_DENY"}


# ============================================================================
# 2. CHROMADB PRE-RETRIEVAL INTEGRATION TESTS
# ============================================================================

@pytest.fixture
def mock_chroma_store():
    """Fixture providing a persistent in-memory Chroma instance with multi-tenant role-flagged chunks."""
    emb = FakeEmbeddings(size=384)
    db = Chroma(collection_name="test_phase5_pre_retrieval", embedding_function=emb)

    docs = [
        Document(
            page_content="Comp A Eng Doc Content",
            metadata={
                "document_id": "doc_a_1",
                "company_id": "comp_a",
                "allowed_roles": "engineer",
                "role_engineer": True,
                "role_hr": False,
                "role_sales": False,
                "role_support": False,
            },
        ),
        Document(
            page_content="Comp A HR Doc Content",
            metadata={
                "document_id": "doc_a_2",
                "company_id": "comp_a",
                "allowed_roles": "hr",
                "role_engineer": False,
                "role_hr": True,
                "role_sales": False,
                "role_support": False,
            },
        ),
        Document(
            page_content="Comp B Eng Doc Content",
            metadata={
                "document_id": "doc_b_1",
                "company_id": "comp_b",
                "allowed_roles": "engineer",
                "role_engineer": True,
                "role_hr": False,
                "role_sales": False,
                "role_support": False,
            },
        ),
        Document(
            page_content="Legacy Chunk Without Role Flags",
            metadata={
                "document_id": "doc_legacy",
                "company_id": "comp_a",
                "allowed_roles": "engineer",
            },
        ),
    ]
    db.add_documents(docs)

    manager = MagicMock(spec=VectorStoreManager)
    manager.vector_store = db
    # Delegate similarity_search_with_score to real Chroma vector store
    manager.similarity_search_with_score.side_effect = lambda query, top_k=5, filter=None: db.similarity_search_with_score(query=query, k=top_k, filter=filter)
    return manager


def test_9_cross_company_chunks_excluded_by_chroma_filter(mock_chroma_store):
    """Test 9: Comp A engineer search never retrieves Comp B chunks at the Chroma vector level."""
    user = DBUser(id="eng_a", company_id="comp_a", role="engineer", email="eng@compa.com", full_name="Eng A")
    retriever = StandardRetriever(vector_store_manager=mock_chroma_store)

    results = retriever.retrieve("Doc Content", user=user, top_k=10)
    contents = [r["content"] for r in results]

    assert "Comp A Eng Doc Content" in contents
    assert "Comp B Eng Doc Content" not in contents


def test_10_same_company_unauthorized_role_chunks_excluded(mock_chroma_store):
    """Test 10: Comp A engineer search never retrieves Comp A HR chunks."""
    user = DBUser(id="eng_a", company_id="comp_a", role="engineer", email="eng@compa.com", full_name="Eng A")
    retriever = StandardRetriever(vector_store_manager=mock_chroma_store)

    results = retriever.retrieve("Doc Content", user=user, top_k=10)
    contents = [r["content"] for r in results]

    assert "Comp A Eng Doc Content" in contents
    assert "Comp A HR Doc Content" not in contents


def test_11_same_company_authorized_chunks_retrieved(mock_chroma_store):
    """Test 11: Comp A HR user search retrieves Comp A HR chunks."""
    user = DBUser(id="hr_a", company_id="comp_a", role="hr", email="hr@compa.com", full_name="HR A")
    retriever = StandardRetriever(vector_store_manager=mock_chroma_store)

    results = retriever.retrieve("Doc Content", user=user, top_k=10)
    contents = [r["content"] for r in results]

    assert "Comp A HR Doc Content" in contents
    assert "Comp A Eng Doc Content" not in contents


def test_12_admin_retrieves_same_company_documents_regardless_of_role_flags(mock_chroma_store):
    """Test 12: Admin retrieves all same-company documents regardless of role flags."""
    user = DBUser(id="admin_a", company_id="comp_a", role="admin", email="admin@compa.com", full_name="Admin A")
    retriever = StandardRetriever(vector_store_manager=mock_chroma_store)

    results = retriever.retrieve("Doc Content", user=user, top_k=10)
    contents = [r["content"] for r in results]

    assert "Comp A Eng Doc Content" in contents
    assert "Comp A HR Doc Content" in contents
    assert "Comp B Eng Doc Content" not in contents


def test_13_retrieval_passes_authorization_filter_into_vector_search_api():
    """Test 13: Verify retriever passes filter directly INTO VectorStoreManager.similarity_search_with_score."""
    mock_manager = MagicMock(spec=VectorStoreManager)
    mock_manager.similarity_search_with_score.return_value = []

    user = DBUser(id="eng_a", company_id="comp_a", role="engineer", email="eng@a.com", full_name="Eng A")
    retriever = StandardRetriever(vector_store_manager=mock_manager)

    retriever.retrieve("search query", user=user, top_k=5)

    expected_filter = {
        "$and": [
            {"company_id": "comp_a"},
            {"role_engineer": True},
        ]
    }
    mock_manager.similarity_search_with_score.assert_called_once_with(
        query="search query",
        top_k=5,
        filter=expected_filter,
    )


def test_14_no_broad_search_candidate_retrieval_used(mock_chroma_store):
    """Test 14: Verify retrieval queries Chroma with top_k=5 (no candidate_k expansion for post-filtering)."""
    mock_manager = MagicMock(spec=VectorStoreManager)
    mock_manager.similarity_search_with_score.return_value = []

    user = DBUser(id="eng_a", company_id="comp_a", role="engineer", email="eng@a.com", full_name="Eng A")
    retriever = StandardRetriever(vector_store_manager=mock_manager)

    retriever.retrieve("query", user=user, top_k=5)
    mock_manager.similarity_search_with_score.assert_called_once_with(
        query="query",
        top_k=5,
        filter={"$and": [{"company_id": "comp_a"}, {"role_engineer": True}]},
    )


def test_15_legacy_chunks_without_role_flags_excluded_for_employees(mock_chroma_store):
    """Test 15: Chunks without role_engineer=True metadata flag are safely excluded by Chroma pre-retrieval filter."""
    user = DBUser(id="eng_a", company_id="comp_a", role="engineer", email="eng@a.com", full_name="Eng A")
    retriever = StandardRetriever(vector_store_manager=mock_chroma_store)

    results = retriever.retrieve("Legacy Chunk", user=user, top_k=10)
    contents = [r["content"] for r in results]

    assert "Legacy Chunk Without Role Flags" not in contents
