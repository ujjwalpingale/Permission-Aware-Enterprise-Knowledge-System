import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth.authentication import get_current_user
from backend.app.db.models import User as DBUser

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """Mock get_current_user dependency for schema validation tests."""
    mock_user = DBUser(id="val_usr", company_id="val_comp", email="val@test.com", role="engineer")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_empty_question_returns_validation_error():
    """Test POST /chat with empty string question returns HTTP 422 validation error."""
    response = client.post("/chat", json={"question": ""})
    assert response.status_code == 422


def test_whitespace_question_returns_validation_error():
    """Test POST /chat with whitespace question returns HTTP 422 validation error."""
    response = client.post("/chat", json={"question": "   \n\t  "})
    assert response.status_code == 422


def test_missing_question_field_returns_validation_error():
    """Test POST /chat without question field returns HTTP 422 validation error."""
    response = client.post("/chat", json={})
    assert response.status_code == 422
