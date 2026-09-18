from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()

    assert "/health" in data["paths"]
    assert "/api/locations" in data["paths"]
    assert "/api/weather" in data["paths"]
    assert "/api/pipeline-runs" in data["paths"]
    assert "/api/auth/register" in data["paths"]


def test_dashboard():
    response = client.get("/")

    assert response.status_code == 200
    assert "PipelineIQ" in response.text


def test_static_css():
    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert "body" in response.text
