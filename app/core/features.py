"""Cálculo de variables (features) a partir de datos crudos del afiliado.

Aislado a propósito de la API y de la base de datos: recibe datos ya
consultados y devuelve variables listas para el modelo, sin saber de dónde
vinieron ni a dónde va el resultado (regla de la Semana 4: el núcleo
científico no se mezcla con la infraestructura).

Cada variable vive en su propia función privada para poder probarlas por
separado y no acumular lógica en un solo método.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AffiliateFeatures:
    dias_desde_ultimo_pago: int
    frecuencia_pago: float
    monto_pago_promedio: float
    antiguedad_dias: int
    frecuencia_acceso: float


def build_features(raw_data: dict) -> AffiliateFeatures:
    """Ensambla las variables individuales a partir de datos crudos ya consultados."""
    return AffiliateFeatures(
        dias_desde_ultimo_pago=_dias_desde_ultimo_pago(raw_data),
        frecuencia_pago=_frecuencia_pago(raw_data),
        monto_pago_promedio=_monto_pago_promedio(raw_data),
        antiguedad_dias=_antiguedad_dias(raw_data),
        frecuencia_acceso=_frecuencia_acceso(raw_data),
    )


def _dias_desde_ultimo_pago(raw_data: dict) -> int:
    raise NotImplementedError("Pendiente: definir con el mapeo real de columnas (ver notas en Obsidian).")


def _frecuencia_pago(raw_data: dict) -> float:
    raise NotImplementedError("Pendiente: definir con el mapeo real de columnas (ver notas en Obsidian).")


def _monto_pago_promedio(raw_data: dict) -> float:
    raise NotImplementedError("Pendiente: definir con el mapeo real de columnas (ver notas en Obsidian).")


def _antiguedad_dias(raw_data: dict) -> int:
    raise NotImplementedError("Pendiente: definir con el mapeo real de columnas (ver notas en Obsidian).")


def _frecuencia_acceso(raw_data: dict) -> float:
    raise NotImplementedError("Pendiente: definir con el mapeo real de columnas (ver notas en Obsidian).")
