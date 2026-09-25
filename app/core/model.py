"""Núcleo del modelo predictivo (entrenamiento e inferencia).

Nunca importa FastAPI ni el driver de base de datos: solo trabaja con
arreglos/objetos de features ya construidos, para poder probarlo sin
levantar la API ni una conexión real (regla de la Semana 4).
"""

import xgboost as xgb

from app.core.constants import XGBOOST_PARAMS


def train(x_train, y_train) -> xgb.XGBClassifier:
    """Entrena un modelo XGBoost nuevo con los hiperparámetros de constants.py."""
    model = xgb.XGBClassifier(**XGBOOST_PARAMS)
    model.fit(x_train, y_train)
    return model


def predict_proba(model: xgb.XGBClassifier, x) -> float:
    """Devuelve la probabilidad de deserción (clase positiva) para un único registro."""
    return float(model.predict_proba(x)[:, 1][0])
