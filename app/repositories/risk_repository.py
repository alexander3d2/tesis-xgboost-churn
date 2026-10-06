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

    def get_latest_scores(self, limit: int, offset: int, order: str) -> tuple[list[dict], int]:
        directions = {"asc": "ASC", "desc": "DESC"}
        try:
            direction = directions[order]
        except KeyError as exc:
            raise ValueError("order must be 'asc' or 'desc'") from exc

        with self._connection.cursor() as cursor:
            cursor.execute(
                f"""
                WITH latest_scores AS (
                    SELECT DISTINCT ON (affiliate_id)
                        affiliate_id, risk_score, risk_level, model_version, scored_at
                    FROM score_riesgo
                    ORDER BY affiliate_id, scored_at DESC
                )
                SELECT affiliate_id, risk_score, risk_level, model_version, scored_at,
                       COUNT(*) OVER () AS total
                FROM latest_scores
                ORDER BY risk_score {direction}, scored_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()

        if not rows:
            return [], 0
        total = rows[0][5]
        return [self._row_to_dict(row[:5]) for row in rows], total

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
            # hasattr en vez de isinstance(datetime) a propósito: cubre tanto
            # datetime como date por si la columna real termina siendo solo
            # fecha, sin hora.
            "scored_at": scored_at.isoformat() if hasattr(scored_at, "isoformat") else scored_at,
        }
