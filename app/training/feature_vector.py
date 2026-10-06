from app.training.dataset_builder import TrainingExampleFeatures

FEATURE_COLUMNS = [
    "dias_desde_ultimo_pago",
    "frecuencia_pago_dias",
    "monto_pago_promedio",
    "antiguedad_dias",
    "dias_desde_ultima_transaccion_billetera",
    "referidos_directos_activos",
    "referidos_directos_inactivos",
    "referidos_directos_totales",
]


def to_feature_vector(features: TrainingExampleFeatures) -> list[float | None]:
    return [
        features.affiliate.dias_desde_ultimo_pago,
        features.affiliate.frecuencia_pago_dias,
        features.affiliate.monto_pago_promedio,
        features.affiliate.antiguedad_dias,
        features.wallet_activity.dias_desde_ultima_transaccion_billetera,
        features.referral.referidos_directos_activos,
        features.referral.referidos_directos_inactivos,
        features.referral.referidos_directos_totales,
    ]
