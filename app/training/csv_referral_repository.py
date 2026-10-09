import pandas as pd

from app.repositories.referral_repository import ReferralCounts


class CsvReferralRepository:
    def __init__(self, affiliate: pd.DataFrame, usercustomer: pd.DataFrame) -> None:
        self._referidos_por_sponsor = self._index_referidos_por_sponsor(affiliate, usercustomer)

    def count_direct_referrals_by_status(self, affiliate_id: int) -> ReferralCounts:
        grupo = self._referidos_por_sponsor.get(affiliate_id)
        if grupo is None:
            return ReferralCounts(activos=0, inactivos=0)
        activos = int((grupo["idstate"] == 1).sum())
        inactivos = int((grupo["idstate"] != 1).sum())
        return ReferralCounts(activos=activos, inactivos=inactivos)

    @staticmethod
    def _index_referidos_por_sponsor(affiliate: pd.DataFrame, usercustomer: pd.DataFrame) -> dict:
        referidos = affiliate.merge(
            usercustomer, left_on="idson", right_on="iduser", how="inner"
        )
        return {idsponsor: grupo for idsponsor, grupo in referidos.groupby("idsponsor")}
