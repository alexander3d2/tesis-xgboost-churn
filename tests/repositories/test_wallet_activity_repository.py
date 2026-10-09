from datetime import date, datetime
from unittest.mock import MagicMock

from app.repositories.wallet_activity_repository import WalletActivityRepository


def _mock_connection(row: tuple | None):
    cursor = MagicMock()
    cursor.fetchone.return_value = row

    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection


def test_get_last_transaction_date_returns_date_when_found():
    connection = _mock_connection((datetime(2026, 8, 15, 10, 0),))
    repository = WalletActivityRepository(connection)

    result = repository.get_last_transaction_date(1, date(2026, 9, 1))

    assert result == date(2026, 8, 15)


def test_get_last_transaction_date_returns_none_when_no_transactions():
    connection = _mock_connection((None,))
    repository = WalletActivityRepository(connection)

    result = repository.get_last_transaction_date(1, date(2026, 9, 1))

    assert result is None
