from dataclasses import dataclass


@dataclass(frozen=True)
class ReferralCounts:
    activos: int
    inactivos: int


class ReferralRepository:
    def __init__(self, connection) -> None:
        self._connection = connection

    def count_direct_referrals_by_status(self, affiliate_id: int) -> ReferralCounts:
        row = self._fetch_counts(affiliate_id)
        return ReferralCounts(activos=row[0], inactivos=row[1])

    def _fetch_counts(self, affiliate_id: int) -> tuple[int, int]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE u.idstate = 1),
                    COUNT(*) FILTER (WHERE u.idstate != 1)
                FROM affiliate a
                JOIN usercustomer u ON u.iduser = a.idson
                WHERE a.idsponsor = %s
                """,
                (affiliate_id,),
            )
            return cursor.fetchone()
