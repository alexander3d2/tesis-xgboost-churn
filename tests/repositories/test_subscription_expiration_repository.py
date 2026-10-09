from datetime import date, datetime
from unittest.mock import MagicMock

from app.repositories.subscription_expiration_repository import SubscriptionExpirationRepository


def _mock_connection(subscription_ids: list[tuple], expiration_rows: list[tuple | None]):
    subscription_ids_cursor = MagicMock()
    subscription_ids_cursor.fetchall.return_value = subscription_ids

    expiration_cursors = []
    for row in expiration_rows:
        cursor = MagicMock()
        cursor.fetchone.return_value = row
        expiration_cursors.append(cursor)

    connection = MagicMock()
    connection.cursor.return_value.__enter__.side_effect = [subscription_ids_cursor, *expiration_cursors]
    return connection


def test_get_days_since_expiration_by_subscription_computes_days_for_each_subscription():
    connection = _mock_connection(
        subscription_ids=[(10,), (20,)],
        expiration_rows=[(datetime(2026, 6, 1),), (datetime(2026, 8, 15),)],
    )
    repository = SubscriptionExpirationRepository(connection)

    result = repository.get_days_since_expiration_by_subscription(1, date(2026, 9, 1))

    assert result == [92, 17]


def test_get_days_since_expiration_by_subscription_returns_none_when_fully_paid():
    connection = _mock_connection(
        subscription_ids=[(10,)],
        expiration_rows=[None],
    )
    repository = SubscriptionExpirationRepository(connection)

    result = repository.get_days_since_expiration_by_subscription(1, date(2026, 9, 1))

    assert result == [None]


def test_get_days_since_expiration_by_subscription_returns_empty_list_without_subscriptions():
    connection = _mock_connection(subscription_ids=[], expiration_rows=[])
    repository = SubscriptionExpirationRepository(connection)

    result = repository.get_days_since_expiration_by_subscription(1, date(2026, 9, 1))

    assert result == []
