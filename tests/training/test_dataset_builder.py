from datetime import date, timedelta
from unittest.mock import MagicMock

from app.core.features import AffiliateRawData
from app.core.horizon import HORIZONTE_PREDICCION_DIAS
from app.repositories.referral_repository import ReferralCounts
from app.training.csv_adapters import (
    CsvAffiliateDataRepository,
    CsvReferralRepository,
    CsvSubscriptionExpirationRepository,
    CsvWalletActivityRepository,
)
from app.training.csv_affiliate_data_repository import CsvAffiliateDataRepository as DirectCsvAffiliateDataRepository
from app.training.csv_referral_repository import CsvReferralRepository as DirectCsvReferralRepository
from app.training.csv_subscription_expiration_repository import (
    CsvSubscriptionExpirationRepository as DirectCsvSubscriptionExpirationRepository,
)
from app.training.csv_wallet_activity_repository import CsvWalletActivityRepository as DirectCsvWalletActivityRepository
from app.training.dataset_builder import TrainingExampleBuilder


def _builder(
    affiliate_raw_data: AffiliateRawData,
    last_transaction_date: date | None,
    referral_counts: ReferralCounts,
    days_since_expiration_by_subscription: list[int | None],
) -> TrainingExampleBuilder:
    affiliate_data_repository = MagicMock()
    affiliate_data_repository.get_raw_data.return_value = affiliate_raw_data

    wallet_activity_repository = MagicMock()
    wallet_activity_repository.get_last_transaction_date.return_value = last_transaction_date

    referral_repository = MagicMock()
    referral_repository.count_direct_referrals_by_status.return_value = referral_counts

    subscription_expiration_repository = MagicMock()
    subscription_expiration_repository.get_days_since_expiration_by_subscription.return_value = (
        days_since_expiration_by_subscription
    )

    return TrainingExampleBuilder(
        affiliate_data_repository=affiliate_data_repository,
        wallet_activity_repository=wallet_activity_repository,
        referral_repository=referral_repository,
        subscription_expiration_repository=subscription_expiration_repository,
    )


def test_build_features_combines_all_feature_sources():
    affiliate_raw_data = AffiliateRawData(
        payment_dates=[date(2026, 7, 1), date(2026, 8, 1)],
        payment_amounts=[100.0, 100.0],
        account_created_at=date(2025, 1, 1),
        reference_date=date(2026, 9, 1),
    )
    builder = _builder(
        affiliate_raw_data=affiliate_raw_data,
        last_transaction_date=date(2026, 8, 20),
        referral_counts=ReferralCounts(activos=2, inactivos=1),
        days_since_expiration_by_subscription=[],
    )

    features = builder.build_features(affiliate_id=1, reference_date=date(2026, 9, 1))

    assert features.affiliate.dias_desde_ultimo_pago == 31
    assert features.wallet_activity.dias_desde_ultima_transaccion_billetera == 12
    assert features.referral.referidos_directos_activos == 2
    assert features.referral.referidos_directos_inactivos == 1
    assert features.referral.referidos_directos_totales == 3


def test_csv_adapters_facade_reexports_existing_classes():
    assert CsvAffiliateDataRepository is DirectCsvAffiliateDataRepository
    assert CsvReferralRepository is DirectCsvReferralRepository
    assert CsvSubscriptionExpirationRepository is DirectCsvSubscriptionExpirationRepository
    assert CsvWalletActivityRepository is DirectCsvWalletActivityRepository


def test_build_label_true_when_a_subscription_is_churned_at_horizon():
    builder = _builder(
        affiliate_raw_data=AffiliateRawData(
            payment_dates=[date(2026, 7, 1)],
            payment_amounts=[100.0],
            account_created_at=date(2025, 1, 1),
            reference_date=date(2026, 9, 1),
        ),
        last_transaction_date=None,
        referral_counts=ReferralCounts(activos=0, inactivos=0),
        days_since_expiration_by_subscription=[200],
    )

    label = builder.build_label(affiliate_id=1, reference_date=date(2026, 9, 1))

    assert label is True


def test_build_label_false_when_no_subscription_is_churned_at_horizon():
    builder = _builder(
        affiliate_raw_data=AffiliateRawData(
            payment_dates=[date(2026, 7, 1)],
            payment_amounts=[100.0],
            account_created_at=date(2025, 1, 1),
            reference_date=date(2026, 9, 1),
        ),
        last_transaction_date=None,
        referral_counts=ReferralCounts(activos=0, inactivos=0),
        days_since_expiration_by_subscription=[30],
    )

    label = builder.build_label(affiliate_id=1, reference_date=date(2026, 9, 1))

    assert label is False


def test_build_label_uses_the_configured_30_day_horizon():
    affiliate_data_repository = MagicMock()
    wallet_activity_repository = MagicMock()
    referral_repository = MagicMock()
    subscription_expiration_repository = MagicMock()
    subscription_expiration_repository.get_days_since_expiration_by_subscription.return_value = [0]
    builder = TrainingExampleBuilder(
        affiliate_data_repository=affiliate_data_repository,
        wallet_activity_repository=wallet_activity_repository,
        referral_repository=referral_repository,
        subscription_expiration_repository=subscription_expiration_repository,
    )

    reference_date = date(2026, 9, 1)
    builder.build_label(affiliate_id=7, reference_date=reference_date)

    subscription_expiration_repository.get_days_since_expiration_by_subscription.assert_called_once_with(
        7, reference_date + timedelta(days=HORIZONTE_PREDICCION_DIAS)
    )
