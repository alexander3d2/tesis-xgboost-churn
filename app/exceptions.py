class AffiliateScoreNotFoundError(Exception):
    """No existe un score de riesgo calculado para el afiliado solicitado."""

    def __init__(self, affiliate_id: int):
        self.affiliate_id = affiliate_id
        super().__init__(f"No existe un score de riesgo calculado para el afiliado {affiliate_id}.")
