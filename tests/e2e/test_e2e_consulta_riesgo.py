"""End-to-end test: PostgreSQL record -> HTTP response over the isolated Compose stack.

Covers CU-01 (consult one score, HU-01/RF-01) and CU-02 (list scores,
HU-02/RF-03) against the real API container and the isolated PostgreSQL
container with the synthetic 3-row fixture. No mocks and no dependency
overrides: every assertion crosses the real HTTP and database boundaries.

Run only when the stack is up (see docs/evidencias_e2e/README.md):

    E2E_API_URL=http://127.0.0.1:18080 pytest tests/e2e -q
"""

import pytest

from tests.e2e.helpers import (
    API_URL,
    EXPECTED_DATABASE,
    EXPECTED_LATEST,
    ITEM_FIELDS,
    ApiClient,
    ResultsDb,
    expected_item,
)

pytestmark = pytest.mark.skipif(
    not API_URL,
    reason="set E2E_API_URL (or SMOKE_API_URL) only when the isolated Docker smoke stack is running",
)

MISSING_AFFILIATE_ID = 919999


@pytest.fixture(scope="module")
def api():
    with ApiClient(API_URL) as client:
        yield client


@pytest.fixture(scope="module")
def db():
    return ResultsDb()


@pytest.fixture(scope="module", autouse=True)
def _database_unchanged_after_module(db):
    before = db.snapshot()
    yield
    assert db.snapshot() == before, "the API must be read-only: table content changed during the module"


def test_database_is_the_isolated_synthetic_fixture(db):
    assert db.current_database() == EXPECTED_DATABASE
    assert db.count() == 3
    assert db.latest_by_affiliate() == EXPECTED_LATEST


def test_health_endpoint_reports_ok(api):
    response = api.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("affiliate_id", sorted(EXPECTED_LATEST))
def test_cu01_http_payload_equals_latest_database_record(api, db, affiliate_id):
    record = db.latest_by_affiliate()[affiliate_id]

    response = api.get(f"/api/v1/risk/{affiliate_id}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == set(ITEM_FIELDS)
    assert isinstance(payload["affiliate_id"], int)
    assert isinstance(payload["risk_score"], float)
    assert 0 <= payload["risk_score"] <= 1
    assert payload == expected_item(record)


def test_cu01_returns_most_recent_record_not_the_first_inserted(api):
    payload = api.get("/api/v1/risk/910001").json()

    assert payload["risk_score"] == 0.91
    assert payload["risk_level"] == "Alto"
    assert payload["scored_at"] == "2026-01-02T00:00:00"


def test_cu01_missing_affiliate_returns_404_with_detail(api, db):
    assert MISSING_AFFILIATE_ID not in db.latest_by_affiliate()

    response = api.get(f"/api/v1/risk/{MISSING_AFFILIATE_ID}")

    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"detail"}
    assert str(MISSING_AFFILIATE_ID) in body["detail"]


def test_cu01_non_integer_identifier_returns_422(api):
    response = api.get("/api/v1/risk/abc")

    assert response.status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "order=invalid", "limit=abc"])
def test_cu02_invalid_query_parameters_return_422(api, query):
    response = api.get(f"/api/v1/risk?{query}")

    assert response.status_code == 422


def test_cu02_default_list_is_paginated_and_matches_database(api, db):
    latest = db.latest_by_affiliate()

    response = api.get("/api/v1/risk")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "limit", "offset", "total"}
    assert (body["limit"], body["offset"], body["total"]) == (50, 0, len(latest))
    expected = sorted(latest.values(), key=lambda row: row["risk_score"], reverse=True)
    assert body["items"] == [expected_item(row) for row in expected]


@pytest.mark.parametrize(
    ("order", "reverse"),
    [("desc", True), ("asc", False)],
)
def test_cu02_order_follows_risk_score(api, db, order, reverse):
    latest = db.latest_by_affiliate()

    body = api.get(f"/api/v1/risk?order={order}").json()

    scores = [item["risk_score"] for item in body["items"]]
    assert scores == sorted((row["risk_score"] for row in latest.values()), reverse=reverse)


def test_cu02_limit_and_offset_slice_the_ordered_list(api, db):
    latest = db.latest_by_affiliate()
    ordered = sorted(latest.values(), key=lambda row: row["risk_score"], reverse=True)

    first = api.get("/api/v1/risk?limit=1&offset=0&order=desc").json()
    second = api.get("/api/v1/risk?limit=1&offset=1&order=desc").json()

    assert (first["limit"], first["offset"], first["total"]) == (1, 0, len(latest))
    assert (second["limit"], second["offset"], second["total"]) == (1, 1, len(latest))
    assert first["items"] == [expected_item(ordered[0])]
    assert second["items"] == [expected_item(ordered[1])]


def test_cu02_offset_beyond_total_returns_200_with_empty_items(api):
    response = api.get("/api/v1/risk?limit=10&offset=50")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert (body["limit"], body["offset"]) == (10, 50)


def test_api_calls_do_not_write_to_the_database(api, db):
    count_before = db.count()
    snapshot_before = db.snapshot()

    for path in (
        "/health",
        "/api/v1/risk/910001",
        f"/api/v1/risk/{MISSING_AFFILIATE_ID}",
        "/api/v1/risk",
        "/api/v1/risk?limit=0",
    ):
        api.get(path)

    assert db.count() == count_before == 3
    assert db.snapshot() == snapshot_before
