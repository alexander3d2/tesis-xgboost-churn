from dataclasses import dataclass
from datetime import date, timedelta

from app.core.churn_label import is_user_churned
from app.core.features import AffiliateFeatures, build_features
from app.core.horizon import HORIZONTE_PREDICCION_DIAS
from app.training.ports import AffiliateDataPort, SubscriptionExpirationPort


@dataclass(frozen=True)
class TrainingExampleFeatures:
    affiliate: AffiliateFeatures


class TrainingExampleBuilder:
    def __init__(
        self,
        affiliate_data_repository: AffiliateDataPort,
        subscription_expiration_repository: SubscriptionExpirationPort,
    ) -> None:
        self._affiliate_data_repository = affiliate_data_repository
        self._subscription_expiration_repository = subscription_expiration_repository

    def build_features(self, affiliate_id: int | str, reference_date: date) -> TrainingExampleFeatures:
        return TrainingExampleFeatures(
            affiliate=self._build_affiliate_features(affiliate_id, reference_date),
        )

    def build_label(self, affiliate_id: int | str, reference_date: date) -> bool:
        horizon_date = reference_date + timedelta(days=HORIZONTE_PREDICCION_DIAS)
        dias_por_suscripcion = self._subscription_expiration_repository.get_days_since_expiration_by_subscription(
            affiliate_id, horizon_date
        )
        return is_user_churned(dias_por_suscripcion)

    def _build_affiliate_features(self, affiliate_id: int | str, reference_date: date) -> AffiliateFeatures:
        raw_data = self._affiliate_data_repository.get_raw_data(affiliate_id, reference_date)
        return build_features(raw_data)
