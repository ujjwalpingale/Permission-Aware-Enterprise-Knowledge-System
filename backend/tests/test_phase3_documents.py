import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal, engine
from backend.app.db.models import Company, User, Document, DocumentPermission

client = TestClient(app)


def unique_str(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_setup():
    """Fixture providing created company, admin, employee, and headers."""
    db = SessionLocal()

    c_name = unique_str("Phase3Comp")
    admin_email = unique_str("admin") + "@p3test.com"
    emp_email = unique_str("emp") + "@p3test.com"
    password = "SecurePassword123!"

    # 1. Register Company & Admin
    reg_comp_res = client.post(
        "/auth/register-company",
        json={
            "company_name": c_name,
            "admin_name": "P3 Admin",
            "admin_email": admin_email,
            "password": password,
        },
    )
    assert reg_comp_res.status_code in [200, 201], reg_comp_res.json()
    comp_data = reg_comp_res.json()
    company_id = comp_data["company_id"]
    invite_code = comp_data["invite_code"]
    admin_id = comp_data["admin_id"]

    # 1b. Login Admin to obtain JWT token
    login_admin_res = client.post(
        "/auth/login",
        json={"email": admin_email, "password": password},
    )
    assert login_admin_res.status_code == 200
    admin_token = login_admin_res.json()["access_token"]

    # 2. Register Employee
    reg_emp_res = client.post(
        "/auth/register",
        json={
            "full_name": "P3 Engineer",
            "email": emp_email,
            "password": password,
            "company_id": company_id,
            "role": "engineer",
            "invite_code": invite_code,
        },
    )
    assert reg_emp_res.status_code in [200, 201], reg_emp_res.json()

    # 3. Login Employee
    login_emp_res = client.post(
        "/auth/login",
        json={"email": emp_email, "password": password},
    )
    assert login_emp_res.status_code == 200
    emp_token = login_emp_res.json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    yield {
        "company_id": company_id,
        "admin_email": admin_email,
        "emp_email": emp_email,
        "admin_headers": admin_headers,
        "emp_headers": emp_headers,
        "admin_user_id": admin_id,
    }

    db.close()


def test_1_admin_can_upload_supported_document(test_setup):
    """Test 1: Admin can successfully upload a supported document (.md)."""
    headers = test_setup["admin_headers"]
    file_content = b"# Engineering Guidelines\n\n1. Write tests.\n2. Verify security."

    with patch("backend.app.api.documents.VectorStoreManager") as mock_vstore:
        mock_vstore.return_value.add_documents.return_value = 1
        res = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Eng Guidelines", "allowed_roles": "engineer,hr"},
            files={"file": ("guidelines.md", file_content, "text/markdown")},
        )

    assert res.status_code == 201, res.json()
    body = res.json()
    assert body["message"] == "Document uploaded and indexed successfully."
    assert body["document"]["title"] == "Eng Guidelines"
    assert body["document"]["company_id"] == test_setup["company_id"]
    assert body["document"]["is_indexed"] is True
    assert set(body["document"]["allowed_roles"]) == {"engineer", "hr"}


def test_2_employee_cannot_upload(test_setup):
    """Test 2: Employee user is rejected with HTTP 403 Forbidden."""
    headers = test_setup["emp_headers"]
    file_content = b"Employee upload attempt"

    res = client.post(
        "/documents/upload",
        headers=headers,
        data={"title": "Unauth Upload", "allowed_roles": "engineer"},
        files={"file": ("doc.txt", file_content, "text/plain")},
    )
    assert res.status_code == 403
    assert "Only admin users can upload documents" in res.json()["detail"]


def test_3_unauthenticated_user_cannot_upload():
    """Test 3: Unauthenticated user without JWT is rejected with HTTP 401."""
    res = client.post(
        "/documents/upload",
        data={"title": "No Auth", "allowed_roles": "engineer"},
        files={"file": ("doc.txt", b"test", "text/plain")},
    )
    assert res.status_code == 401


def test_4_and_5_uploaded_file_stored_and_retrieved_from_mysql(test_setup):
    """Test 4 & 5: Uploaded file is stored in MySQL file_data (LONGBLOB) and matches original bytes."""
    headers = test_setup["admin_headers"]
    original_bytes = b"BINARY_LONGBLOB_PAYLOAD_\x00\x01\x02_PDF_OR_TEXT"

    with patch("backend.app.api.documents.VectorStoreManager"):
        res = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Blob Test Doc", "allowed_roles": "engineer"},
            files={"file": ("blob.txt", original_bytes, "text/plain")},
        )
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]

    # Verify directly from MySQL database
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter_by(id=doc_id).first()
        assert db_doc is not None
        assert isinstance(db_doc.file_data, bytes)
        assert db_doc.file_data == original_bytes
    finally:
        db.close()


def test_6_7_8_company_id_created_by_from_admin_anti_tampering(test_setup):
    """Test 6, 7 & 8: company_id and created_by come strictly from authenticated Admin."""
    headers = test_setup["admin_headers"]
    fake_company_id = "fake_company_9999"

    with patch("backend.app.api.documents.VectorStoreManager"):
        res = client.post(
            "/documents/upload",
            headers=headers,
            data={
                "title": "Anti Tamper Doc",
                "allowed_roles": "engineer",
                "company_id": fake_company_id,  # Attempted override
            },
            files={"file": ("test.txt", b"sample data", "text/plain")},
        )
    assert res.status_code == 201
    doc_data = res.json()["document"]
    assert doc_data["company_id"] == test_setup["company_id"]
    assert doc_data["company_id"] != fake_company_id
    assert doc_data["created_by"] == test_setup["admin_user_id"]


def test_9_allowed_roles_stored_in_document_permissions(test_setup):
    """Test 9: Allowed roles are stored correctly in document_permissions table."""
    headers = test_setup["admin_headers"]
    roles_input = "engineer,sales,support"

    with patch("backend.app.api.documents.VectorStoreManager"):
        res = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Multi Role Doc", "allowed_roles": roles_input},
            files={"file": ("doc.txt", b"data", "text/plain")},
        )
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]

    db = SessionLocal()
    try:
        perms = db.query(DocumentPermission).filter_by(document_id=doc_id).all()
        stored_roles = {p.allowed_role for p in perms}
        assert stored_roles == {"engineer", "sales", "support"}
    finally:
        db.close()


def test_10_admin_role_rejected_in_allowed_roles(test_setup):
    """Test 10: Role 'admin' is rejected when attempted as an employee document permission."""
    headers = test_setup["admin_headers"]

    res = client.post(
        "/documents/upload",
        headers=headers,
        data={"title": "Admin Role Test", "allowed_roles": "admin,engineer"},
        files={"file": ("doc.txt", b"data", "text/plain")},
    )
    assert res.status_code == 400
    assert "admin" in res.json()["detail"].lower()


def test_11_unsupported_file_type_rejected(test_setup):
    """Test 11: Unsupported file extension (.exe) is rejected with HTTP 400."""
    headers = test_setup["admin_headers"]

    res = client.post(
        "/documents/upload",
        headers=headers,
        data={"title": "Bad Executable", "allowed_roles": "engineer"},
        files={"file": ("malicious.exe", b"MZ...", "application/x-msdownload")},
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_12_13_14_is_indexed_lifecycle(test_setup):
    """Test 12, 13 & 14: is_indexed toggles to True on Chroma success, remains False on Chroma failure."""
    headers = test_setup["admin_headers"]

    # Case A: Ingestion Failure -> is_indexed remains False
    with patch("backend.app.api.documents.VectorStoreManager") as mock_vstore:
        mock_vstore.return_value.add_documents.side_effect = RuntimeError("Chroma connection timeout")
        res_fail = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Failing Index Doc", "allowed_roles": "engineer"},
            files={"file": ("fail.txt", b"data", "text/plain")},
        )
        assert res_fail.status_code == 500
        assert "vector indexing failed" in res_fail.json()["detail"]

    # Verify document in MySQL has is_indexed == False
    db = SessionLocal()
    try:
        failed_doc = db.query(Document).filter_by(company_id=test_setup["company_id"], title="Failing Index Doc").first()
        assert failed_doc is not None
        assert failed_doc.is_indexed is False
    finally:
        db.close()

    # Case B: Ingestion Success -> is_indexed toggles to True
    with patch("backend.app.api.documents.VectorStoreManager") as mock_vstore:
        mock_vstore.return_value.add_documents.return_value = 1
        res_ok = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Success Index Doc", "allowed_roles": "engineer"},
            files={"file": ("ok.txt", b"data", "text/plain")},
        )
        assert res_ok.status_code == 201
        assert res_ok.json()["document"]["is_indexed"] is True


def test_15_chroma_metadata_contains_required_fields(test_setup):
    """Test 15: Chunks submitted to ChromaDB contain document_id, company_id, allowed_roles."""
    headers = test_setup["admin_headers"]

    with patch("backend.app.api.documents.VectorStoreManager") as mock_vstore:
        mock_inst = MagicMock()
        mock_vstore.return_value = mock_inst

        res = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Metadata Check Doc", "allowed_roles": "engineer,hr"},
            files={"file": ("meta.txt", b"Some text content for chunking", "text/plain")},
        )
        assert res.status_code == 201

        # Inspect chunks passed to VectorStoreManager.add_documents
        assert mock_inst.add_documents.called
        chunks_added = mock_inst.add_documents.call_args[0][0]
        assert len(chunks_added) > 0
        first_chunk_meta = chunks_added[0].metadata

        assert "document_id" in first_chunk_meta
        assert first_chunk_meta["company_id"] == test_setup["company_id"]
        assert first_chunk_meta["allowed_roles"] == "engineer,hr"


def test_16_multi_company_document_isolation(test_setup):
    """Test 16: Two companies uploading documents maintain strict multi-tenant isolation."""
    # Register Company B
    comp_b_name = unique_str("CompanyB")
    admin_b_email = unique_str("adminB") + "@compb.com"

    reg_b_res = client.post(
        "/auth/register-company",
        json={
            "company_name": comp_b_name,
            "admin_name": "Admin B",
            "admin_email": admin_b_email,
            "password": "Password123!",
        },
    )
    assert reg_b_res.status_code in [200, 201]

    login_b_res = client.post(
        "/auth/login",
        json={"email": admin_b_email, "password": "Password123!"},
    )
    token_b = login_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Upload Doc for Company A
    with patch("backend.app.api.documents.VectorStoreManager"):
        client.post(
            "/documents/upload",
            headers=test_setup["admin_headers"],
            data={"title": "Company A Secret", "allowed_roles": "engineer"},
            files={"file": ("docA.txt", b"Secret A", "text/plain")},
        )
        # Upload Doc for Company B
        client.post(
            "/documents/upload",
            headers=headers_b,
            data={"title": "Company B Secret", "allowed_roles": "engineer"},
            files={"file": ("docB.txt", b"Secret B", "text/plain")},
        )

    # Get Documents for Company A
    get_a_res = client.get("/documents", headers=test_setup["admin_headers"])
    assert get_a_res.status_code == 200
    titles_a = [d["title"] for d in get_a_res.json()]
    assert "Company A Secret" in titles_a
    assert "Company B Secret" not in titles_a

    # Get Documents for Company B
    get_b_res = client.get("/documents", headers=headers_b)
    assert get_b_res.status_code == 200
    titles_b = [d["title"] for d in get_b_res.json()]
    assert "Company B Secret" in titles_b
    assert "Company A Secret" not in titles_b


def test_17_original_file_remains_in_mysql_independently(test_setup):
    """Test 17: Original document binary payload is stored in MySQL independent of vector store."""
    headers = test_setup["admin_headers"]
    payload = b"ORIGINAL_MYSQL_BINARY_PAYLOAD_TEST_17"

    with patch("backend.app.api.documents.VectorStoreManager"):
        res = client.post(
            "/documents/upload",
            headers=headers,
            data={"title": "Test 17 Doc", "allowed_roles": "engineer"},
            files={"file": ("test17.txt", payload, "text/plain")},
        )
    assert res.status_code == 201

    db = SessionLocal()
    try:
        docs_with_blob = db.query(Document).filter(Document.file_data.isnot(None)).all()
        assert len(docs_with_blob) > 0
        found = False
        for doc in docs_with_blob:
            assert isinstance(doc.file_data, bytes)
            if doc.file_data == payload:
                found = True
        assert found is True
    finally:
        db.close()


def test_18_no_permanent_local_file_path_used():
    """Test 18: Verify Document model has no file_path attribute."""
    assert not hasattr(Document, "file_path")


def test_19_and_20_mysql_is_active_and_no_sqlite():
    """Test 19 & 20: Confirm active engine is MySQL dialect and no SQLite is used."""
    assert engine.dialect.name == "mysql"
    assert engine.dialect.driver == "pymysql"


def test_legacy_upload_route_removed_and_not_found():
    """Regression Test: Confirm legacy POST /upload endpoint is removed and returns HTTP 404."""
    res = client.post(
        "/upload",
        files={"files": ("legacy.txt", b"legacy data", "text/plain")},
    )
    assert res.status_code == 404, f"Expected 404 Not Found, got {res.status_code}"
