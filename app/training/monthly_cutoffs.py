from datetime import date


def generar_fechas_de_corte_mensuales(fecha_inicio: date, fecha_fin: date) -> list[date]:
    fechas = []
    actual = date(fecha_inicio.year, fecha_inicio.month, 1)
    while actual <= fecha_fin:
        fechas.append(actual)
        actual = _primer_dia_del_siguiente_mes(actual)
    return fechas


def _primer_dia_del_siguiente_mes(fecha: date) -> date:
    if fecha.month == 12:
        return date(fecha.year + 1, 1, 1)
    return date(fecha.year, fecha.month + 1, 1)
