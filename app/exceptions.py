class AffiliateScoreNotFoundError(Exception):
    def __init__(self, affiliate_id: int):
        self.affiliate_id = affiliate_id
        super().__init__(f"No existe un score de riesgo calculado para el afiliado {affiliate_id}.")


class AffiliateNotFoundError(Exception):
    def __init__(self, affiliate_id: int):
        self.affiliate_id = affiliate_id
        super().__init__(f"No existe ningún afiliado registrado con id {affiliate_id}.")


class SinPagosRegistradosError(Exception):
    def __init__(self, affiliate_id: int | None = None):
        self.affiliate_id = affiliate_id
        detalle = f" (afiliado {affiliate_id})" if affiliate_id is not None else ""
        super().__init__(f"No hay pagos registrados para calcular las variables de pago{detalle}.")


class PagosInsuficientesError(Exception):
    def __init__(self, cantidad_pagos: int):
        self.cantidad_pagos = cantidad_pagos
        super().__init__(
            f"Se necesitan al menos 2 pagos para calcular la frecuencia de pago; se encontraron {cantidad_pagos}."
        )
