from dataclasses import dataclass
from datetime import date

from app.exceptions import PagosInsuficientesError, SinPagosRegistradosError


@dataclass(frozen=True)
class AffiliateRawData:
    payment_dates: list[date]
    payment_amounts: list[float]
    account_created_at: date
    reference_date: date


@dataclass(frozen=True)
class AffiliateFeatures:
    dias_desde_ultimo_pago: int
    frecuencia_pago_dias: float
    monto_pago_promedio: float
    antiguedad_dias: int


def build_features(raw_data: AffiliateRawData) -> AffiliateFeatures:
    return AffiliateFeatures(
        dias_desde_ultimo_pago=_dias_desde_ultimo_pago(raw_data),
        frecuencia_pago_dias=_frecuencia_pago_dias(raw_data),
        monto_pago_promedio=_monto_pago_promedio(raw_data),
        antiguedad_dias=_antiguedad_dias(raw_data),
    )


def _dias_desde_ultimo_pago(raw_data: AffiliateRawData) -> int:
    if not raw_data.payment_dates:
        raise SinPagosRegistradosError
    ultimo_pago = max(raw_data.payment_dates)
    return (raw_data.reference_date - ultimo_pago).days


def _frecuencia_pago_dias(raw_data: AffiliateRawData) -> float:
    fechas_ordenadas = sorted(raw_data.payment_dates)
    if len(fechas_ordenadas) < 2:
        raise PagosInsuficientesError(len(fechas_ordenadas))

    intervalos_dias = [
        (fechas_ordenadas[i] - fechas_ordenadas[i - 1]).days for i in range(1, len(fechas_ordenadas))
    ]
    return sum(intervalos_dias) / len(intervalos_dias)


def _monto_pago_promedio(raw_data: AffiliateRawData) -> float:
    if not raw_data.payment_amounts:
        raise SinPagosRegistradosError
    return sum(raw_data.payment_amounts) / len(raw_data.payment_amounts)


def _antiguedad_dias(raw_data: AffiliateRawData) -> int:
    return (raw_data.reference_date - raw_data.account_created_at).days
