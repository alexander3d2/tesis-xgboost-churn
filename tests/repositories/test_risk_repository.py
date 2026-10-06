from datetime import date, datetime
from unittest.mock import MagicMock

from app.repositories.risk_repository import RiskScoreRepository


def _mock_connection(row: tuple | None):
    cursor = MagicMock()
    cursor.fetchone.return_value = row

    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection


def test_get_latest_score_returns_mapped_dict_when_found():
    scored_at = datetime(2026, 9, 1, 10, 30)
    connection = _mock_connection((1, 0.82, "Alto", "v1", scored_at))
    repository = RiskScoreRepository(connection)

    result = repository.get_latest_score(1)

    assert result == {
        "affiliate_id": 1,
        "risk_score": 0.82,
        "risk_level": "Alto",
        "model_version": "v1",
        "scored_at": scored_at.isoformat(),
    }


def test_get_latest_score_serializes_plain_date_without_time():
    scored_at = date(2026, 9, 1)
    connection = _mock_connection((1, 0.82, "Alto", "v1", scored_at))
    repository = RiskScoreRepository(connection)

    result = repository.get_latest_score(1)

    assert result["scored_at"] == scored_at.isoformat()


def test_get_latest_score_returns_none_when_not_found():
    connection = _mock_connection(None)
    repository = RiskScoreRepository(connection)

    result = repository.get_latest_score(999)

    assert result is None


def test_get_latest_scores_maps_rows_and_uses_parameterized_pagination():
    scored_at = datetime(2026, 9, 1, 10, 30)
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, 0.82, "Alto", "v1", scored_at, 1)]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    repository = RiskScoreRepository(connection)

    items, total = repository.get_latest_scores(limit=10, offset=2, order="asc")

    assert items[0]["affiliate_id"] == 1
    assert total == 1
    query, params = cursor.execute.call_args.args
    assert "ORDER BY risk_score ASC, scored_at DESC" in query
    assert "%s" in query
    assert params == (10, 2)


def test_get_latest_scores_returns_empty_page_with_zero_total():
    connection = _mock_connection(None)
    connection.cursor.return_value.__enter__.return_value.fetchall.return_value = []
    repository = RiskScoreRepository(connection)

    assert repository.get_latest_scores(limit=50, offset=0, order="desc") == ([], 0)
