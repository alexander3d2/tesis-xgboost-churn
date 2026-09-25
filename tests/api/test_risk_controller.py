from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_risk_repository
from app.main import app


class _FakeRiskRepository:
    """Doble de prueba: evita depender de una BD real para probar el endpoint."""

    def __init__(self, score: dict | None):
        self._score = score

    def get_latest_score(self, affiliate_id: int) -> dict | None:
        return self._score


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def test_get_risk_score_returns_200_when_found():
    scored_at = datetime(2026, 9, 1, 10, 30)
    score = {
        "affiliate_id": 1,
        "risk_score": 0.82,
        "risk_level": "Alto",
        "model_version": "v1",
        "scored_at": scored_at.isoformat(),
    }
    app.dependency_overrides[get_risk_repository] = lambda: _FakeRiskRepository(score)
    client = TestClient(app)

    response = client.get("/api/v1/risk/1")

    assert response.status_code == 200
    assert response.json() == score


def test_get_risk_score_returns_404_when_not_found():
    app.dependency_overrides[get_risk_repository] = lambda: _FakeRiskRepository(None)
    client = TestClient(app)

    response = client.get("/api/v1/risk/999")

    assert response.status_code == 404
    assert "999" in response.json()["detail"]
