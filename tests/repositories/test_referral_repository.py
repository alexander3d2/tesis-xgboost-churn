from unittest.mock import MagicMock

from app.repositories.referral_repository import ReferralRepository


def _mock_connection(row: tuple):
    cursor = MagicMock()
    cursor.fetchone.return_value = row

    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection


def test_count_direct_referrals_by_status_returns_active_and_inactive_counts():
    connection = _mock_connection((3, 2))
    repository = ReferralRepository(connection)

    result = repository.count_direct_referrals_by_status(1)

    assert result.activos == 3
    assert result.inactivos == 2


def test_count_direct_referrals_by_status_returns_zero_when_no_referrals():
    connection = _mock_connection((0, 0))
    repository = ReferralRepository(connection)

    result = repository.count_direct_referrals_by_status(1)

    assert result.activos == 0
    assert result.inactivos == 0
