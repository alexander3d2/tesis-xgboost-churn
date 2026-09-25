from datetime import date

import pytest

from app.core.features import AffiliateRawData, build_features
from app.exceptions import PagosInsuficientesError, SinPagosRegistradosError


def _raw_data(**overrides) -> AffiliateRawData:
    defaults = {
        "payment_dates": [date(2026, 6, 1), date(2026, 7, 1), date(2026, 8, 1)],
        "payment_amounts": [100.0, 100.0, 120.0],
        "account_created_at": date(2025, 1, 1),
        "reference_date": date(2026, 9, 1),
    }
    defaults.update(overrides)
    return AffiliateRawData(**defaults)


def test_build_features_with_valid_data():
    features = build_features(_raw_data())

    assert features.dias_desde_ultimo_pago == 31
    assert features.frecuencia_pago_dias == pytest.approx(30.5, rel=0.01)
    assert features.monto_pago_promedio == pytest.approx(106.67, rel=0.01)
    assert features.antiguedad_dias == 608


def test_build_features_raises_when_no_payments():
    with pytest.raises(SinPagosRegistradosError):
        build_features(_raw_data(payment_dates=[], payment_amounts=[]))


def test_build_features_raises_when_only_one_payment():
    with pytest.raises(PagosInsuficientesError):
        build_features(_raw_data(payment_dates=[date(2026, 8, 1)], payment_amounts=[100.0]))
