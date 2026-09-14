from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check_returns_200():
    """Test GET /health returns status 200 and ok payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
