import xgboost as xgb

from app.core.constants import XGBOOST_PARAMS


def train(x_train, y_train) -> xgb.XGBClassifier:
    model = xgb.XGBClassifier(**XGBOOST_PARAMS)
    model.fit(x_train, y_train)
    return model


def predict_proba(model: xgb.XGBClassifier, x) -> float:
    return float(model.predict_proba(x)[:, 1][0])
