from datetime import date

import pandas as pd


class CsvWalletActivityRepository:
    def __init__(self, wallets: pd.DataFrame, wallet_transacciones: pd.DataFrame) -> None:
        self._transacciones_by_user = self._index_transacciones_by_user(wallets, wallet_transacciones)

    def get_last_transaction_date(self, affiliate_id: int, reference_date: date) -> date | None:
        grupo = self._transacciones_by_user.get(affiliate_id)
        if grupo is None:
            return None
        corte = pd.Timestamp(reference_date)
        transacciones_validas = grupo[grupo["initialdate"] <= corte]
        if transacciones_validas.empty:
            return None
        return transacciones_validas["initialdate"].max().date()

    @staticmethod
    def _index_transacciones_by_user(wallets: pd.DataFrame, wallet_transacciones: pd.DataFrame) -> dict:
        transacciones_con_usuario = wallet_transacciones.merge(wallets, on="idwallet", how="inner")
        return {iduser: grupo for iduser, grupo in transacciones_con_usuario.groupby("iduser")}
