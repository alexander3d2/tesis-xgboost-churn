from datetime import date

from app.training.monthly_cutoffs import generar_fechas_de_corte_mensuales


def test_generar_fechas_de_corte_mensuales_incluye_primer_dia_de_cada_mes():
    fechas = generar_fechas_de_corte_mensuales(date(2026, 1, 15), date(2026, 4, 1))

    assert fechas == [
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
        date(2026, 4, 1),
    ]


def test_generar_fechas_de_corte_mensuales_cruza_el_fin_de_anio():
    fechas = generar_fechas_de_corte_mensuales(date(2025, 11, 10), date(2026, 2, 1))

    assert fechas == [
        date(2025, 11, 1),
        date(2025, 12, 1),
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]


def test_generar_fechas_de_corte_mensuales_vacio_cuando_inicio_es_posterior_a_fin():
    fechas = generar_fechas_de_corte_mensuales(date(2026, 5, 1), date(2026, 4, 1))

    assert fechas == []
