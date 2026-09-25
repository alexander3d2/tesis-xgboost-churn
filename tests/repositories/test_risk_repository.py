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
    """scored_at podría llegar como date (sin hora) y no solo datetime; no debe romperse."""
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
