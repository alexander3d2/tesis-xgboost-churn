import dataclasses
import inspect
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.core.features import AffiliateRawData
from app.core.horizon import HORIZONTE_PREDICCION_DIAS
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
from app.training.dataset_builder import TrainingExampleBuilder, TrainingExampleFeatures


def _builder(
    affiliate_raw_data: AffiliateRawData,
    days_since_expiration_by_subscription: list[int | None],
) -> TrainingExampleBuilder:
    affiliate_data_repository = MagicMock()
    affiliate_data_repository.get_raw_data.return_value = affiliate_raw_data

    subscription_expiration_repository = MagicMock()
    subscription_expiration_repository.get_days_since_expiration_by_subscription.return_value = (
        days_since_expiration_by_subscription
    )

    return TrainingExampleBuilder(
        affiliate_data_repository=affiliate_data_repository,
        subscription_expiration_repository=subscription_expiration_repository,
    )


def test_build_features_returns_only_payment_based_affiliate_features():
    affiliate_raw_data = AffiliateRawData(
        payment_dates=[date(2026, 7, 1), date(2026, 8, 1)],
        payment_amounts=[100.0, 100.0],
        account_created_at=date(2025, 1, 1),
        reference_date=date(2026, 9, 1),
    )
    builder = _builder(affiliate_raw_data=affiliate_raw_data, days_since_expiration_by_subscription=[])

    features = builder.build_features(affiliate_id=1, reference_date=date(2026, 9, 1))

    assert features.affiliate.dias_desde_ultimo_pago == 31
    assert features.affiliate.frecuencia_pago_dias == 31
    assert features.affiliate.monto_pago_promedio == 100.0
    assert features.affiliate.antiguedad_dias == 608
    assert [field.name for field in dataclasses.fields(TrainingExampleFeatures)] == ["affiliate"]


def test_builder_constructor_does_not_require_wallet_or_referral_repositories():
    parameters = set(inspect.signature(TrainingExampleBuilder.__init__).parameters) - {"self"}

    assert parameters == {"affiliate_data_repository", "subscription_expiration_repository"}


def test_build_features_accepts_string_affiliate_id():
    affiliate_raw_data = AffiliateRawData(
        payment_dates=[date(2026, 7, 1), date(2026, 8, 1)],
        payment_amounts=[100.0, 100.0],
        account_created_at=date(2025, 1, 1),
        reference_date=date(2026, 9, 1),
    )
    builder = _builder(affiliate_raw_data=affiliate_raw_data, days_since_expiration_by_subscription=[])

    builder.build_features(affiliate_id="U1A2B3C4D5E6F", reference_date=date(2026, 9, 1))

    builder._affiliate_data_repository.get_raw_data.assert_called_once_with("U1A2B3C4D5E6F", date(2026, 9, 1))


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
        days_since_expiration_by_subscription=[30],
    )

    label = builder.build_label(affiliate_id=1, reference_date=date(2026, 9, 1))

    assert label is False


def test_build_label_uses_the_configured_30_day_horizon():
    affiliate_data_repository = MagicMock()
    subscription_expiration_repository = MagicMock()
    subscription_expiration_repository.get_days_since_expiration_by_subscription.return_value = [0]
    builder = TrainingExampleBuilder(
        affiliate_data_repository=affiliate_data_repository,
        subscription_expiration_repository=subscription_expiration_repository,
    )

    reference_date = date(2026, 9, 1)
    builder.build_label(affiliate_id=7, reference_date=reference_date)

    subscription_expiration_repository.get_days_since_expiration_by_subscription.assert_called_once_with(
        7, reference_date + timedelta(days=HORIZONTE_PREDICCION_DIAS)
    )
