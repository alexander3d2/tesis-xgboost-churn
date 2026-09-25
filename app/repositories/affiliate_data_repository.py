from datetime import date

from app.core.features import AffiliateRawData
from app.exceptions import AffiliateNotFoundError


class AffiliateDataRepository:
    """Lee los datos crudos de un afiliado desde la BD de origen (dev_inclub).

    Solo lectura, y solo trae datos crudos: nunca calcula variables aquí.
    Eso lo hace app.core.features, manteniendo el núcleo científico aislado
    de la base de datos (regla de la Semana 4).
    """

    def __init__(self, connection) -> None:
        self._connection = connection

    def get_raw_data(self, affiliate_id: int, reference_date: date) -> AffiliateRawData:
        payments = self._fetch_payments(affiliate_id)
        return AffiliateRawData(
            payment_dates=[payment_date for payment_date, _ in payments],
            payment_amounts=[float(amount) for _, amount in payments],
            account_created_at=self._fetch_account_created_at(affiliate_id),
            reference_date=reference_date,
        )

    def _fetch_payments(self, affiliate_id: int) -> list[tuple[date, float]]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.paydate, p.quoteusd
                FROM bo_membership.payment p
                JOIN bo_membership.suscription s ON s.idsuscription = p.idsuscription
                WHERE s.iduser = %s
                ORDER BY p.paydate
                """,
                (affiliate_id,),
            )
            return cursor.fetchall()

    def _fetch_account_created_at(self, affiliate_id: int) -> date:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT createdate FROM bo_account.user WHERE id = %s", (affiliate_id,))
            row = cursor.fetchone()

        if row is None:
            raise AffiliateNotFoundError(affiliate_id)
        return row[0]
