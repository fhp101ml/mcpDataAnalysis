from fastapi.testclient import TestClient
import pytest
from src.main import app

client = TestClient(app)

def test_health_check():
    """Prueba que el endpoint de salud responde correctamente."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "running" in data["message"]
