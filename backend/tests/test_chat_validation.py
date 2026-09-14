from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


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
