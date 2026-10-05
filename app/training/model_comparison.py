from dataclasses import dataclass
from typing import Any

import numpy as np
import xgboost as xgb
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from app.core.constants import RANDOM_SEED, XGBOOST_PARAMS


MODEL_NAMES = ("xgboost", "random_forest", "decision_tree")


@dataclass(frozen=True)
class ModelComparisonResult:
    model_name: str
    model: ClassifierMixin
    probabilities: np.ndarray


class ModelComparisonRunner:
    def __init__(self, random_state: int = RANDOM_SEED) -> None:
        self.random_state = random_state

    def run(self, x: Any, y: Any) -> tuple[ModelComparisonResult, ...]:
        results = []
        for model_name, model in self._models():
            model.fit(x, y)
            probabilities = model.predict_proba(x)[:, 1]
            results.append(
                ModelComparisonResult(
                    model_name=model_name,
                    model=model,
                    probabilities=probabilities,
                )
            )
        return tuple(results)

    def _models(self) -> tuple[tuple[str, ClassifierMixin], ...]:
        xgboost_params = {**XGBOOST_PARAMS, "random_state": self.random_state}
        return (
            ("xgboost", xgb.XGBClassifier(**xgboost_params)),
            ("random_forest", RandomForestClassifier(random_state=self.random_state)),
            ("decision_tree", DecisionTreeClassifier(random_state=self.random_state)),
        )


def compare_models(
    x: Any,
    y: Any,
    random_state: int = RANDOM_SEED,
) -> tuple[ModelComparisonResult, ...]:
    return ModelComparisonRunner(random_state=random_state).run(x, y)
