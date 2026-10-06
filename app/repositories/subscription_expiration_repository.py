from datetime import date, datetime

from app.repositories.sentinel_dates import FECHA_MINIMA_VALIDA


class SubscriptionExpirationRepository:
    def __init__(self, connection) -> None:
        self._connection = connection

    def get_days_since_expiration_by_subscription(
        self, affiliate_id: int, reference_date: date
    ) -> list[int | None]:
        subscription_ids = self._fetch_subscription_ids(affiliate_id)
        return [
            self._days_since_expiration(subscription_id, reference_date)
            for subscription_id in subscription_ids
        ]

    def _fetch_subscription_ids(self, affiliate_id: int) -> list[int]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT idsuscription FROM bo_membership.suscription WHERE iduser = %s",
                (affiliate_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def _days_since_expiration(self, subscription_id: int, reference_date: date) -> int | None:
        row = self._fetch_next_unpaid_expiration_row(subscription_id, reference_date)
        return self._row_to_days(row, reference_date)

    def _fetch_next_unpaid_expiration_row(self, subscription_id: int, reference_date: date) -> tuple | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT nextexpirationdate
                FROM bo_membership.payment
                WHERE idsuscription = %s AND (paydate IS NULL OR paydate <= %s OR paydate > %s)
                ORDER BY positiononschedule
                LIMIT 1
                """,
                (subscription_id, FECHA_MINIMA_VALIDA, reference_date),
            )
            return cursor.fetchone()

    @staticmethod
    def _row_to_days(row: tuple | None, reference_date: date) -> int | None:
        if row is None or row[0] is None:
            return None
        next_expiration = row[0]
        next_expiration_date = next_expiration.date() if isinstance(next_expiration, datetime) else next_expiration
        return (reference_date - next_expiration_date).days
