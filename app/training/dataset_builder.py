from dataclasses import dataclass
from datetime import date, timedelta

from app.core.churn_label import is_user_churned
from app.core.features import AffiliateFeatures, build_features
from app.core.horizon import HORIZONTE_PREDICCION_DIAS
from app.core.referral_features import ReferralFeatures, ReferralRawData, build_referral_features
from app.core.wallet_activity_features import (
    WalletActivityFeatures,
    WalletActivityRawData,
    build_wallet_activity_features,
)
from app.training.ports import (
    AffiliateDataPort,
    ReferralPort,
    SubscriptionExpirationPort,
    WalletActivityPort,
)


@dataclass(frozen=True)
class TrainingExampleFeatures:
    affiliate: AffiliateFeatures
    wallet_activity: WalletActivityFeatures
    referral: ReferralFeatures


class TrainingExampleBuilder:
    def __init__(
        self,
        affiliate_data_repository: AffiliateDataPort,
        wallet_activity_repository: WalletActivityPort,
        referral_repository: ReferralPort,
        subscription_expiration_repository: SubscriptionExpirationPort,
    ) -> None:
        self._affiliate_data_repository = affiliate_data_repository
        self._wallet_activity_repository = wallet_activity_repository
        self._referral_repository = referral_repository
        self._subscription_expiration_repository = subscription_expiration_repository

    def build_features(self, affiliate_id: int, reference_date: date) -> TrainingExampleFeatures:
        return TrainingExampleFeatures(
            affiliate=self._build_affiliate_features(affiliate_id, reference_date),
            wallet_activity=self._build_wallet_activity_features(affiliate_id, reference_date),
            referral=self._build_referral_features(affiliate_id),
        )

    def build_label(self, affiliate_id: int, reference_date: date) -> bool:
        horizon_date = reference_date + timedelta(days=HORIZONTE_PREDICCION_DIAS)
        dias_por_suscripcion = self._subscription_expiration_repository.get_days_since_expiration_by_subscription(
            affiliate_id, horizon_date
        )
        return is_user_churned(dias_por_suscripcion)

    def _build_affiliate_features(self, affiliate_id: int, reference_date: date) -> AffiliateFeatures:
        raw_data = self._affiliate_data_repository.get_raw_data(affiliate_id, reference_date)
        return build_features(raw_data)

    def _build_wallet_activity_features(self, affiliate_id: int, reference_date: date) -> WalletActivityFeatures:
        last_transaction_date = self._wallet_activity_repository.get_last_transaction_date(
            affiliate_id, reference_date
        )
        raw_data = WalletActivityRawData(
            last_transaction_date=last_transaction_date,
            reference_date=reference_date,
        )
        return build_wallet_activity_features(raw_data)

    def _build_referral_features(self, affiliate_id: int) -> ReferralFeatures:
        counts = self._referral_repository.count_direct_referrals_by_status(affiliate_id)
        raw_data = ReferralRawData(
            referidos_directos_activos=counts.activos,
            referidos_directos_inactivos=counts.inactivos,
        )
        return build_referral_features(raw_data)
