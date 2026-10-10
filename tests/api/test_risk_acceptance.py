"""Alternate-flow, error-flow and regression tests for the read-only risk API.

Each test name carries the acceptance criterion it verifies, taken from the Gherkin
tables of Chapter III (HU-01/CU-01 consult one score, HU-02/CU-02 list scores).
The happy paths and the basic 404/422 cases live in test_risk_controller.py and
are not repeated here.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_risk_repository
from app.main import app


def _score(risk_score: float, affiliate_id: int = 1) -> dict:
    return {
        "affiliate_id": affiliate_id,
        "risk_score": risk_score,
        "risk_level": "Alto",
        "model_version": "v1",
        "scored_at": "2026-09-01T10:30:00",
    }


class _RecordingRiskRepository:
    def __init__(self, score: dict | None = None, items: list[dict] | None = None):
        self._score = score
        self._items = items or []
        self.list_calls: list[dict] = []
        self.lookup_calls: list[int] = []

    def get_latest_score(self, affiliate_id: int) -> dict | None:
        self.lookup_calls.append(affiliate_id)
        return self._score

    def get_latest_scores(self, limit: int, offset: int, order: str) -> tuple[list[dict], int]:
        self.list_calls.append({"limit": limit, "offset": offset, "order": order})
        return self._items, len(self._items)


class _FailingRiskRepository:
    def get_latest_score(self, affiliate_id: int):
        raise RuntimeError("results database unavailable")

    def get_latest_scores(self, limit: int, offset: int, order: str):
        raise RuntimeError("results database unavailable")


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def _use(repository) -> None:
    app.dependency_overrides[get_risk_repository] = lambda: repository


@pytest.mark.parametrize("risk_score", [0.0, 1.0])
def test_hu01_cu01_score_at_closed_boundaries_is_returned_unchanged(risk_score):
    """HU-01 happy path / RF-01: risk_score belongs to [0, 1], both ends included."""
    _use(_RecordingRiskRepository(score=_score(risk_score)))

    response = TestClient(app).get("/api/v1/risk/1")

    assert response.status_code == 200
    assert response.json() == _score(risk_score)


@pytest.mark.parametrize("risk_score", [-0.01, 1.01])
def test_hu01_cu01_score_outside_range_is_never_returned_to_the_client(risk_score):
    """HU-01 error flow / RF-01: an out-of-range stored value yields 500, not a score."""
    _use(_RecordingRiskRepository(score=_score(risk_score)))

    response = TestClient(app, raise_server_exceptions=False).get("/api/v1/risk/1")

    assert response.status_code == 500
    assert "risk_score" not in response.text


def test_hu01_cu01_missing_affiliate_404_body_has_only_detail_naming_the_affiliate():
    """HU-01 alternate flow: HTTP 404 and a body whose only key is `detail` with the id."""
    repository = _RecordingRiskRepository(score=None)
    _use(repository)

    response = TestClient(app).get("/api/v1/risk/999")

    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"detail"}
    assert isinstance(body["detail"], str)
    assert "999" in body["detail"]
    assert repository.lookup_calls == [999]


@pytest.mark.parametrize("identifier", ["abc", "1.5", "1e3"])
def test_hu01_cu01_non_integer_identifier_returns_422_without_reading_the_database(identifier):
    """HU-01 error flow: the identifier `abc` is not an integer -> HTTP 422, no score."""
    repository = _RecordingRiskRepository(score=_score(0.5))
    _use(repository)

    response = TestClient(app).get(f"/api/v1/risk/{identifier}")

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert "risk_score" not in response.text
    assert repository.lookup_calls == []


def test_hu01_cu01_repository_failure_returns_500_and_no_score():
    """HU-01 error flow: if the repository fails the API answers HTTP 500 without a score."""
    _use(_FailingRiskRepository())

    response = TestClient(app, raise_server_exceptions=False).get("/api/v1/risk/1")

    assert response.status_code == 500
    assert "risk_score" not in response.text


def test_hu02_cu02_empty_list_with_default_parameters_returns_200_and_total_zero():
    """HU-02 alternate flow: no stored scores -> HTTP 200, empty items, total 0, defaults 50/0."""
    repository = _RecordingRiskRepository(items=[])
    _use(repository)

    response = TestClient(app).get("/api/v1/risk")

    assert response.status_code == 200
    assert response.json() == {"items": [], "limit": 50, "offset": 0, "total": 0}
    assert repository.list_calls == [{"limit": 50, "offset": 0, "order": "desc"}]


@pytest.mark.parametrize("limit", [1, 100])
def test_hu02_cu02_limit_at_closed_boundaries_is_accepted_and_forwarded(limit):
    """HU-02 happy path / RF-03: limit belongs to [1, 100], both ends included."""
    repository = _RecordingRiskRepository(items=[_score(0.82)])
    _use(repository)

    response = TestClient(app).get(f"/api/v1/risk?limit={limit}")

    assert response.status_code == 200
    assert response.json()["limit"] == limit
    assert repository.list_calls == [{"limit": limit, "offset": 0, "order": "desc"}]


@pytest.mark.parametrize("offset", [0, 10_000])
def test_hu02_cu02_offset_is_accepted_and_forwarded_including_beyond_the_data(offset):
    """HU-02 / RF-03: offset >= 0; an offset past the last row is a valid empty page."""
    repository = _RecordingRiskRepository(items=[])
    _use(repository)

    response = TestClient(app).get(f"/api/v1/risk?offset={offset}")

    assert response.status_code == 200
    assert response.json()["offset"] == offset
    assert response.json()["items"] == []
    assert repository.list_calls[0]["offset"] == offset


@pytest.mark.parametrize("order", ["asc", "desc"])
def test_hu02_cu02_each_allowed_order_value_is_forwarded_to_the_repository(order):
    """HU-02 / RF-03: order belongs to {asc, desc}; the value reaches the repository intact."""
    repository = _RecordingRiskRepository(items=[_score(0.5)])
    _use(repository)

    response = TestClient(app).get(f"/api/v1/risk?order={order}")

    assert response.status_code == 200
    assert repository.list_calls == [{"limit": 50, "offset": 0, "order": order}]


@pytest.mark.parametrize(
    "query",
    ["limit=abc", "limit=1.5", "limit=-5", "offset=abc", "offset=1.5", "order=ASC", "order="],
)
def test_hu02_cu02_other_invalid_parameters_return_422(query):
    """HU-02 error flow (extension): non-numeric, decimal, negative and case-variant values."""
    repository = _RecordingRiskRepository(items=[_score(0.5)])
    _use(repository)

    response = TestClient(app).get(f"/api/v1/risk?{query}")

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "order=invalid"])
def test_hu02_cu02_invalid_parameters_are_rejected_before_reading_the_database(query):
    """HU-02 error flow regression: validation happens before any repository access."""
    repository = _RecordingRiskRepository(items=[_score(0.5)])
    _use(repository)

    response = TestClient(app).get(f"/api/v1/risk?{query}")

    assert response.status_code == 422
    assert repository.list_calls == []


def test_hu02_cu02_repository_failure_returns_500_and_no_items():
    """HU-02 error flow: a failing repository never produces a partial list."""
    _use(_FailingRiskRepository())

    response = TestClient(app, raise_server_exceptions=False).get("/api/v1/risk")

    assert response.status_code == 500
    assert "items" not in response.text
