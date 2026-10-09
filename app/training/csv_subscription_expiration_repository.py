from datetime import date

import pandas as pd

from app.repositories.sentinel_dates import FECHA_MINIMA_VALIDA


class CsvSubscriptionExpirationRepository:
    def __init__(self, payments: pd.DataFrame, suscripciones: pd.DataFrame) -> None:
        self._subscription_ids_by_user = self._index_subscription_ids_by_user(suscripciones)
        self._payments_by_subscription = self._index_payments_by_subscription(payments)

    def get_days_since_expiration_by_subscription(
        self, affiliate_id: int | str, reference_date: date
    ) -> list[int | None]:
        subscription_ids = self._subscription_ids_by_user.get(affiliate_id, [])
        return [
            self._days_since_expiration(subscription_id, reference_date)
            for subscription_id in subscription_ids
        ]

    @staticmethod
    def _index_subscription_ids_by_user(suscripciones: pd.DataFrame) -> dict:
        return suscripciones.groupby("iduser")["idsuscription"].apply(list).to_dict()

    @staticmethod
    def _index_payments_by_subscription(payments: pd.DataFrame) -> dict:
        ordenados = payments.sort_values("positiononschedule")
        return {idsuscription: grupo for idsuscription, grupo in ordenados.groupby("idsuscription")}

    def _days_since_expiration(self, subscription_id: int | str, reference_date: date) -> int | None:
        grupo = self._payments_by_subscription.get(subscription_id)
        if grupo is None:
            return None

        fecha_minima = pd.Timestamp(FECHA_MINIMA_VALIDA)
        corte = pd.Timestamp(reference_date)
        no_pagada = grupo["paydate"].isna() | (grupo["paydate"] <= fecha_minima) | (grupo["paydate"] > corte)
        primera_no_pagada = grupo[no_pagada].head(1)

        if primera_no_pagada.empty or pd.isna(primera_no_pagada["nextexpirationdate"].iloc[0]):
            return None

        vencimiento = primera_no_pagada["nextexpirationdate"].iloc[0].date()
        return (reference_date - vencimiento).days
