from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass(frozen=True)
class EvaluationMetrics:
    average_precision: float
    roc_auc: float
    recall: float
    precision: float
    f1: float
    confusion_matrix: tuple[tuple[int, int], tuple[int, int]]
    threshold: float
    primary_metric: str
    primary_value: float
    contingency_metric: str
    contingency_value: float


def select_primary_metric(y_true: Sequence[int]) -> str:
    labels = np.asarray(y_true)
    positives = int(np.sum(labels == 1))
    negatives = int(np.sum(labels == 0))
    if positives == 0 or negatives == 0:
        raise ValueError("both binary classes are required")
    return "average_precision" if positives < negatives else "roc_auc"


def select_threshold(y_true: Sequence[int], probabilities: Sequence[float]) -> float:
    labels = np.asarray(y_true, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=float)
    if labels.shape != scores.shape or labels.ndim != 1:
        raise ValueError("y_true and probabilities must be one-dimensional and aligned")
    candidates = np.unique(np.concatenate((np.array([0.0, 1.0]), scores)))
    ranked = []
    for threshold in candidates:
        predicted = (scores >= threshold).astype(np.int8)
        ranked.append(
            (
                f1_score(labels, predicted, zero_division=0),
                recall_score(labels, predicted, zero_division=0),
                float(threshold),
            )
        )
    return max(ranked, key=lambda item: (item[0], item[1], item[2]))[2]


def evaluate_predictions(
    y_true: Sequence[int],
    probabilities: Sequence[float],
    threshold: float | None = None,
) -> EvaluationMetrics:
    labels = np.asarray(y_true, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=float)
    if labels.shape != scores.shape or labels.ndim != 1:
        raise ValueError("y_true and probabilities must be one-dimensional and aligned")
    chosen_threshold = select_threshold(labels, scores) if threshold is None else float(threshold)
    predicted = (scores >= chosen_threshold).astype(np.int8)
    matrix = confusion_matrix(labels, predicted, labels=[0, 1])
    primary = select_primary_metric(labels)
    average_precision = float(average_precision_score(labels, scores))
    roc_auc = float(roc_auc_score(labels, scores))
    values = {"average_precision": average_precision, "roc_auc": roc_auc}
    contingency = "roc_auc" if primary == "average_precision" else "average_precision"
    return EvaluationMetrics(
        average_precision=average_precision,
        roc_auc=roc_auc,
        recall=float(recall_score(labels, predicted, zero_division=0)),
        precision=float(precision_score(labels, predicted, zero_division=0)),
        f1=float(f1_score(labels, predicted, zero_division=0)),
        confusion_matrix=(tuple(matrix[0]), tuple(matrix[1])),
        threshold=chosen_threshold,
        primary_metric=primary,
        primary_value=values[primary],
        contingency_metric=contingency,
        contingency_value=values[contingency],
    )
