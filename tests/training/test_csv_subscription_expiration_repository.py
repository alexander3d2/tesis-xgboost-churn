from datetime import date

import pandas as pd

from app.training.csv_subscription_expiration_repository import CsvSubscriptionExpirationRepository


def _suscripciones() -> pd.DataFrame:
    return pd.DataFrame({"idsuscription": [1, 2], "iduser": [10, 10]})


def _payments() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "idsuscription": [1, 1, 2],
            "paydate": pd.to_datetime(["2026-06-01", None, "0001-01-01"], errors="coerce"),
            "nextexpirationdate": pd.to_datetime(["2026-06-01", "2026-07-01", "2026-06-01"]),
            "positiononschedule": [1, 2, 1],
        }
    )


def test_get_days_since_expiration_returns_one_value_per_subscription():
    repository = CsvSubscriptionExpirationRepository(_payments(), _suscripciones())

    result = repository.get_days_since_expiration_by_subscription(10, date(2026, 9, 1))

    assert result == [62, 92]


def test_get_days_since_expiration_works_with_string_ids():
    suscripciones = pd.DataFrame({"idsuscription": ["S1", "S2"], "iduser": ["U1A2B3C4D5E6F", "U1A2B3C4D5E6F"]})
    payments = _payments().assign(idsuscription=["S1", "S1", "S2"])
    repository = CsvSubscriptionExpirationRepository(payments, suscripciones)

    result = repository.get_days_since_expiration_by_subscription("U1A2B3C4D5E6F", date(2026, 9, 1))

    assert result == [62, 92]


def test_get_days_since_expiration_string_ids_keep_leading_zeros_distinct():
    suscripciones = pd.DataFrame({"idsuscription": ["001", "1"], "iduser": ["001", "1"]})
    payments = pd.DataFrame(
        {
            "idsuscription": ["001", "1"],
            "paydate": pd.to_datetime([None, None]),
            "nextexpirationdate": pd.to_datetime(["2026-08-01", "2026-07-01"]),
            "positiononschedule": [1, 1],
        }
    )
    repository = CsvSubscriptionExpirationRepository(payments, suscripciones)

    assert repository.get_days_since_expiration_by_subscription("001", date(2026, 9, 1)) == [31]
    assert repository.get_days_since_expiration_by_subscription("1", date(2026, 9, 1)) == [62]


def test_get_days_since_expiration_returns_empty_list_without_subscriptions():
    repository = CsvSubscriptionExpirationRepository(_payments(), _suscripciones())

    result = repository.get_days_since_expiration_by_subscription(999, date(2026, 9, 1))

    assert result == []
