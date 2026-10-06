DIAS_MINIMOS_DESERCION = 180


def is_subscription_churned(dias_desde_vencimiento: int | None) -> bool:
    if dias_desde_vencimiento is None:
        return False
    return dias_desde_vencimiento > DIAS_MINIMOS_DESERCION


def is_user_churned(dias_desde_vencimiento_por_suscripcion: list[int | None]) -> bool:
    return any(is_subscription_churned(dias) for dias in dias_desde_vencimiento_por_suscripcion)
