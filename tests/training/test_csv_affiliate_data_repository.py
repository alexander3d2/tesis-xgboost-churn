from datetime import date

import pandas as pd
import pytest

from app.exceptions import AffiliateNotFoundError
from app.training.csv_affiliate_data_repository import CsvAffiliateDataRepository


def _payments() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "idsuscription": [1, 1, 2],
            "paydate": pd.to_datetime(["2026-07-01", "2026-08-01", "0001-01-01"], errors="coerce"),
            "quoteusd": [100.0, 100.0, 999.0],
            "nextexpirationdate": pd.to_datetime(["2026-07-01", "2026-08-01", "0001-01-01"], errors="coerce"),
            "positiononschedule": [1, 2, 1],
        }
    )


def _suscripciones() -> pd.DataFrame:
    return pd.DataFrame({"idsuscription": [1, 2], "iduser": [10, 10]})


def _usuarios() -> pd.DataFrame:
    return pd.DataFrame({"iduser": [10], "createdate": pd.to_datetime(["2025-01-01"])})


def test_get_raw_data_excludes_garbage_sentinel_dates():
    repository = CsvAffiliateDataRepository(_payments(), _suscripciones(), _usuarios())

    raw_data = repository.get_raw_data(affiliate_id=10, reference_date=date(2026, 9, 1))

    assert raw_data.payment_dates == [date(2026, 7, 1), date(2026, 8, 1)]
    assert raw_data.payment_amounts == [100.0, 100.0]
    assert raw_data.account_created_at == date(2025, 1, 1)


def test_get_raw_data_respects_reference_date_cutoff():
    repository = CsvAffiliateDataRepository(_payments(), _suscripciones(), _usuarios())

    raw_data = repository.get_raw_data(affiliate_id=10, reference_date=date(2026, 7, 15))

    assert raw_data.payment_dates == [date(2026, 7, 1)]


def test_get_raw_data_works_with_string_ids():
    payments = _payments().assign(idsuscription=["S1", "S1", "S2"])
    suscripciones = pd.DataFrame({"idsuscription": ["S1", "S2"], "iduser": ["U1A2B3C4D5E6F", "U1A2B3C4D5E6F"]})
    usuarios = pd.DataFrame({"iduser": ["U1A2B3C4D5E6F"], "createdate": pd.to_datetime(["2025-01-01"])})
    repository = CsvAffiliateDataRepository(payments, suscripciones, usuarios)

    raw_data = repository.get_raw_data(affiliate_id="U1A2B3C4D5E6F", reference_date=date(2026, 9, 1))

    assert raw_data.payment_dates == [date(2026, 7, 1), date(2026, 8, 1)]
    assert raw_data.payment_amounts == [100.0, 100.0]
    assert raw_data.account_created_at == date(2025, 1, 1)


def test_get_raw_data_with_string_ids_keeps_leading_zeros_distinct():
    payments = pd.DataFrame(
        {
            "idsuscription": ["001", "1"],
            "paydate": pd.to_datetime(["2026-07-01", "2026-08-01"]),
            "quoteusd": [10.0, 20.0],
            "nextexpirationdate": pd.to_datetime(["2026-08-01", "2026-09-01"]),
            "positiononschedule": [1, 1],
        }
    )
    suscripciones = pd.DataFrame({"idsuscription": ["001", "1"], "iduser": ["001", "1"]})
    usuarios = pd.DataFrame({"iduser": ["001", "1"], "createdate": pd.to_datetime(["2025-01-01", "2025-02-01"])})
    repository = CsvAffiliateDataRepository(payments, suscripciones, usuarios)

    raw_data = repository.get_raw_data(affiliate_id="001", reference_date=date(2026, 9, 1))

    assert raw_data.payment_amounts == [10.0]
    assert raw_data.account_created_at == date(2025, 1, 1)


def test_get_raw_data_raises_when_string_affiliate_not_found():
    payments = _payments().assign(idsuscription=["S1", "S1", "S2"])
    suscripciones = pd.DataFrame({"idsuscription": ["S1", "S2"], "iduser": ["UAAAAAAAAAAAA", "UAAAAAAAAAAAA"]})
    usuarios = pd.DataFrame({"iduser": ["UAAAAAAAAAAAA"], "createdate": pd.to_datetime(["2025-01-01"])})
    repository = CsvAffiliateDataRepository(payments, suscripciones, usuarios)

    with pytest.raises(AffiliateNotFoundError):
        repository.get_raw_data(affiliate_id="UBBBBBBBBBBBB", reference_date=date(2026, 9, 1))


def test_get_raw_data_raises_when_affiliate_not_found():
    repository = CsvAffiliateDataRepository(_payments(), _suscripciones(), _usuarios())

    with pytest.raises(AffiliateNotFoundError):
        repository.get_raw_data(affiliate_id=999, reference_date=date(2026, 9, 1))
