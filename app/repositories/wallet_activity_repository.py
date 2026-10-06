from datetime import date, datetime


class WalletActivityRepository:
    def __init__(self, connection) -> None:
        self._connection = connection

    def get_last_transaction_date(self, affiliate_id: int, reference_date: date) -> date | None:
        row = self._fetch_last_transaction_row(affiliate_id, reference_date)
        return self._row_to_date(row)

    def _fetch_last_transaction_row(self, affiliate_id: int, reference_date: date) -> tuple | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT MAX(wt.initialdate)
                FROM bo_wallet.wallettransaction wt
                JOIN bo_wallet.wallet w ON w.idwallet = wt.idwallet
                WHERE w.iduser = %s AND wt.initialdate <= %s
                """,
                (affiliate_id, reference_date),
            )
            return cursor.fetchone()

    @staticmethod
    def _row_to_date(row: tuple | None) -> date | None:
        if row is None or row[0] is None:
            return None
        last_transaction = row[0]
        return last_transaction.date() if isinstance(last_transaction, datetime) else last_transaction
