from datetime import date
from unittest.mock import MagicMock

import pytest

from app.exceptions import AffiliateNotFoundError
from app.repositories.affiliate_data_repository import AffiliateDataRepository


def _mock_connection(payments: list[tuple], created_at_row: tuple | None):
    """Simula una conexión psycopg: cada `with connection.cursor()` sucesivo
    devuelve un cursor distinto, en el mismo orden en que el repositorio los
    abre (primero pagos, luego fecha de creación de cuenta)."""
    payments_cursor = MagicMock()
    payments_cursor.fetchall.return_value = payments

    created_cursor = MagicMock()
    created_cursor.fetchone.return_value = created_at_row

    connection = MagicMock()
    connection.cursor.return_value.__enter__.side_effect = [payments_cursor, created_cursor]
    return connection


def test_get_raw_data_builds_affiliate_raw_data_from_query_results():
    connection = _mock_connection(
        payments=[(date(2026, 6, 1), 100.0), (date(2026, 7, 1), 120.0)],
        created_at_row=(date(2025, 1, 1),),
    )
    repository = AffiliateDataRepository(connection)

    raw_data = repository.get_raw_data(affiliate_id=1, reference_date=date(2026, 9, 1))

    assert raw_data.payment_dates == [date(2026, 6, 1), date(2026, 7, 1)]
    assert raw_data.payment_amounts == [100.0, 120.0]
    assert raw_data.account_created_at == date(2025, 1, 1)
    assert raw_data.reference_date == date(2026, 9, 1)


def test_get_raw_data_raises_when_affiliate_not_found():
    connection = _mock_connection(payments=[], created_at_row=None)
    repository = AffiliateDataRepository(connection)

    with pytest.raises(AffiliateNotFoundError):
        repository.get_raw_data(affiliate_id=999, reference_date=date(2026, 9, 1))
