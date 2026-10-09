from datetime import date

import pandas as pd

from app.core.features import AffiliateRawData
from app.exceptions import AffiliateNotFoundError
from app.repositories.sentinel_dates import FECHA_MINIMA_VALIDA


class CsvAffiliateDataRepository:
    def __init__(self, payments: pd.DataFrame, suscripciones: pd.DataFrame, usuarios: pd.DataFrame) -> None:
        self._payments_by_user = self._index_payments_by_user(payments, suscripciones)
        self._created_at_by_user = usuarios.set_index("iduser")["createdate"]

    def get_raw_data(self, affiliate_id: int | str, reference_date: date) -> AffiliateRawData:
        payments = self._fetch_payments(affiliate_id, reference_date)
        return AffiliateRawData(
            payment_dates=[payment_date.date() for payment_date in payments["paydate"]],
            payment_amounts=[float(amount) for amount in payments["quoteusd"]],
            account_created_at=self._fetch_account_created_at(affiliate_id),
            reference_date=reference_date,
        )

    @staticmethod
    def _index_payments_by_user(payments: pd.DataFrame, suscripciones: pd.DataFrame) -> dict:
        fecha_minima = pd.Timestamp(FECHA_MINIMA_VALIDA)
        pagos_validos = payments[payments["paydate"] > fecha_minima]
        pagos_con_usuario = pagos_validos.merge(suscripciones, on="idsuscription", how="inner")
        return {iduser: grupo for iduser, grupo in pagos_con_usuario.groupby("iduser")}

    def _fetch_payments(self, affiliate_id: int | str, reference_date: date) -> pd.DataFrame:
        grupo = self._payments_by_user.get(affiliate_id)
        if grupo is None:
            return pd.DataFrame(columns=["paydate", "quoteusd"])
        corte = pd.Timestamp(reference_date)
        return grupo[grupo["paydate"] <= corte]

    def _fetch_account_created_at(self, affiliate_id: int | str) -> date:
        if affiliate_id not in self._created_at_by_user.index:
            raise AffiliateNotFoundError(affiliate_id)
        return self._created_at_by_user.loc[affiliate_id].date()
