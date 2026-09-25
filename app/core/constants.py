"""Hiperparámetros y umbrales del modelo XGBoost.

Valores propuestos como punto de partida (Cap. III de la tesis); se
ajustarán durante el entrenamiento y la validación con datos reales, no
son resultados finales.
"""

RANDOM_SEED = 42  # reproducibilidad, exigida por la Semana 5 de Seminario II

XGBOOST_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "random_state": RANDOM_SEED,
}

RISK_LEVEL_THRESHOLDS = {
    "alto": 0.7,
    "medio": 0.4,
}
