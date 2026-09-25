from datetime import datetime


class RiskScoreRepository:
    """Acceso de solo lectura a la tabla de resultados del modelo (score_riesgo).

    Aísla el SQL del resto de la aplicación: ni el controller ni el núcleo
    del modelo escriben queries directamente (regla de la Semana 4: separar
    el núcleo científico de la infraestructura).
    """

    def __init__(self, connection) -> None:
        self._connection = connection

    def get_latest_score(self, affiliate_id: int) -> dict | None:
        """Devuelve el score de riesgo más reciente de un afiliado, o None si no existe."""
        row = self._fetch_latest_score_row(affiliate_id)
        if row is None:
            return None
        return self._row_to_dict(row)

    def _fetch_latest_score_row(self, affiliate_id: int) -> tuple | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT affiliate_id, risk_score, risk_level, model_version, scored_at
                FROM score_riesgo
                WHERE affiliate_id = %s
                ORDER BY scored_at DESC
                LIMIT 1
                """,
                (affiliate_id,),
            )
            return cursor.fetchone()

    @staticmethod
    def _row_to_dict(row: tuple) -> dict:
        affiliate_id, risk_score, risk_level, model_version, scored_at = row
        return {
            "affiliate_id": affiliate_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "model_version": model_version,
            "scored_at": scored_at.isoformat() if isinstance(scored_at, datetime) else scored_at,
        }
