import pandas as pd

from app.training.csv_referral_repository import CsvReferralRepository


def _affiliate() -> pd.DataFrame:
    return pd.DataFrame({"idsponsor": [1, 1, 1], "idson": [10, 11, 12]})


def _usercustomer() -> pd.DataFrame:
    return pd.DataFrame({"iduser": [10, 11, 12], "idstate": [1, 1, 0]})


def test_count_direct_referrals_by_status_splits_active_and_inactive():
    repository = CsvReferralRepository(_affiliate(), _usercustomer())

    result = repository.count_direct_referrals_by_status(1)

    assert result.activos == 2
    assert result.inactivos == 1


def test_count_direct_referrals_by_status_returns_zero_without_referrals():
    repository = CsvReferralRepository(_affiliate(), _usercustomer())

    result = repository.count_direct_referrals_by_status(999)

    assert result.activos == 0
    assert result.inactivos == 0
