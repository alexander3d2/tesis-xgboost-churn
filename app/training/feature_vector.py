from app.training.dataset_builder import TrainingExampleFeatures

FEATURE_COLUMNS = [
    "dias_desde_ultimo_pago",
    "frecuencia_pago_dias",
    "monto_pago_promedio",
    "antiguedad_dias",
]


def to_feature_vector(features: TrainingExampleFeatures) -> list[float | None]:
    return [
        features.affiliate.dias_desde_ultimo_pago,
        features.affiliate.frecuencia_pago_dias,
        features.affiliate.monto_pago_promedio,
        features.affiliate.antiguedad_dias,
    ]
