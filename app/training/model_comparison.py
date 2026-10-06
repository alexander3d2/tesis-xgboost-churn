from dataclasses import dataclass
from typing import Any

import numpy as np
import xgboost as xgb
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from app.core.constants import RANDOM_SEED, XGBOOST_PARAMS


MODEL_NAMES = ("xgboost", "random_forest", "decision_tree")
CONFIGURATION_CANDIDATES = {
    "xgboost": (
        {"n_estimators": 50, "max_depth": 3, "learning_rate": 0.1},
        {"n_estimators": 100, "max_depth": 4, "learning_rate": 0.05},
        {"n_estimators": 150, "max_depth": 2, "learning_rate": 0.1},
    ),
    "random_forest": (
        {"n_estimators": 100, "max_depth": 4, "min_samples_leaf": 1},
        {"n_estimators": 150, "max_depth": 6, "min_samples_leaf": 2},
        {"n_estimators": 200, "max_depth": 8, "min_samples_leaf": 1},
    ),
    "decision_tree": (
        {"max_depth": 3, "min_samples_leaf": 1},
        {"max_depth": 5, "min_samples_leaf": 2},
        {"max_depth": 7, "min_samples_leaf": 3},
    ),
}


@dataclass(frozen=True)
class ModelComparisonResult:
    model_name: str
    model: ClassifierMixin
    probabilities: np.ndarray
    configuration_name: str = "scaffold-1"
    configuration: tuple[tuple[str, Any], ...] = ()


class ModelComparisonRunner:
    def __init__(self, random_state: int = RANDOM_SEED) -> None:
        self.random_state = random_state

    def run(
        self,
        x: Any,
        y: Any,
        x_test: Any | None = None,
    ) -> tuple[ModelComparisonResult, ...]:
        prediction_input = x if x_test is None else x_test
        results = []
        for model_name, model in self._models():
            model.fit(x, y)
            probabilities = model.predict_proba(prediction_input)[:, 1]
            results.append(
                ModelComparisonResult(
                    model_name=model_name,
                    model=model,
                    probabilities=probabilities,
                )
            )
        return tuple(results)

    def run_configurations(
        self, x: Any, y: Any, x_test: Any | None = None
    ) -> tuple[ModelComparisonResult, ...]:
        prediction_input = x if x_test is None else x_test
        results = []
        for model_name in MODEL_NAMES:
            for index, configuration in enumerate(CONFIGURATION_CANDIDATES[model_name], start=1):
                model = self._build_model(model_name, configuration)
                model.fit(x, y)
                results.append(ModelComparisonResult(
                    model_name=model_name,
                    model=model,
                    probabilities=model.predict_proba(prediction_input)[:, 1],
                    configuration_name=f"scaffold-{index}",
                    configuration=tuple(sorted(configuration.items())),
                ))
        return tuple(results)

    def _models(self) -> tuple[tuple[str, ClassifierMixin], ...]:
        return tuple((name, self._build_model(name, CONFIGURATION_CANDIDATES[name][0])) for name in MODEL_NAMES)

    def _build_model(self, model_name: str, configuration: dict[str, Any]) -> ClassifierMixin:
        if model_name == "xgboost":
            params = {**XGBOOST_PARAMS, **configuration, "random_state": self.random_state}
            return xgb.XGBClassifier(**params)
        if model_name == "random_forest":
            return RandomForestClassifier(**configuration, random_state=self.random_state)
        return DecisionTreeClassifier(**configuration, random_state=self.random_state)


def compare_models(
    x: Any,
    y: Any,
    random_state: int = RANDOM_SEED,
    x_test: Any | None = None,
) -> tuple[ModelComparisonResult, ...]:
    return ModelComparisonRunner(random_state=random_state).run(x, y, x_test=x_test)
