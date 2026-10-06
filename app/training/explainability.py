from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class ExplainabilityUnavailable:
    available: bool = False
    reason: str = "SHAP is not installed"


@dataclass(frozen=True)
class ExplainabilityAvailable:
    available: bool
    values: Any
    feature_names: tuple[str, ...] | None


def explain_model(
    model: Any,
    features: Any,
    feature_names: Sequence[str] | None = None,
) -> ExplainabilityAvailable | ExplainabilityUnavailable:
    try:
        import shap
    except ImportError:
        return ExplainabilityUnavailable()
    try:
        values = shap.TreeExplainer(model)(features).values
    except Exception as exc:
        return ExplainabilityUnavailable(reason=f"SHAP unavailable for this model: {exc}")
    return ExplainabilityAvailable(
        available=True,
        values=values,
        feature_names=tuple(feature_names) if feature_names is not None else None,
    )
