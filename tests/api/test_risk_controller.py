from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_risk_repository
from app.main import app


class _FakeRiskRepository:
    def __init__(self, score: dict | None):
        self._score = score

    def get_latest_score(self, affiliate_id: int) -> dict | None:
        return self._score

    def get_latest_scores(self, limit: int, offset: int, order: str) -> tuple[list[dict], int]:
        return self._score or [], len(self._score or [])


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


def test_list_risk_scores_returns_paginated_contract():
    scores = [
        {
            "affiliate_id": 1,
            "risk_score": 0.82,
            "risk_level": "Alto",
            "model_version": "v1",
            "scored_at": "2026-09-01T10:30:00",
        }
    ]
    app.dependency_overrides[get_risk_repository] = lambda: _FakeRiskRepository(scores)

    response = TestClient(app).get("/api/v1/risk?limit=10&offset=2&order=asc")

    assert response.status_code == 200
    assert response.json() == {"items": scores, "limit": 10, "offset": 2, "total": 1}


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "order=invalid"])
def test_list_risk_scores_rejects_invalid_query_values(query):
    app.dependency_overrides[get_risk_repository] = lambda: _FakeRiskRepository([])

    response = TestClient(app).get(f"/api/v1/risk?{query}")

    assert response.status_code == 422
