from datetime import date

import pandas as pd

from app.training.csv_wallet_activity_repository import CsvWalletActivityRepository


def _wallets() -> pd.DataFrame:
    return pd.DataFrame({"idwallet": [1], "iduser": [10]})


def _transacciones() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "idwallet": [1, 1],
            "initialdate": pd.to_datetime(["2026-08-15", "2026-08-20"]),
        }
    )


def test_get_last_transaction_date_returns_most_recent_before_reference_date():
    repository = CsvWalletActivityRepository(_wallets(), _transacciones())

    result = repository.get_last_transaction_date(10, date(2026, 9, 1))

    assert result == date(2026, 8, 20)


def test_get_last_transaction_date_respects_reference_date_cutoff():
    repository = CsvWalletActivityRepository(_wallets(), _transacciones())

    result = repository.get_last_transaction_date(10, date(2026, 8, 16))

    assert result == date(2026, 8, 15)


def test_get_last_transaction_date_returns_none_when_no_wallet():
    repository = CsvWalletActivityRepository(_wallets(), _transacciones())

    result = repository.get_last_transaction_date(999, date(2026, 9, 1))

    assert result is None
