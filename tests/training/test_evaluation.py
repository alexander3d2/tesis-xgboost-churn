import time

import numpy as np
import pytest

from app.training.evaluation import (
    evaluate_predictions,
    select_primary_metric,
    select_threshold,
)


def test_primary_metric_uses_pr_auc_only_for_minority_positive_class():
    assert select_primary_metric([0, 0, 0, 1]) == "average_precision"
    assert select_primary_metric([0, 1, 0, 1]) == "roc_auc"


def test_threshold_uses_validation_f1_and_recall_tie_break():
    threshold = select_threshold([0, 1, 0, 1], [0.1, 0.8, 0.4, 0.7])
    assert threshold == 0.7


def _reference_threshold(y_true, probabilities):
    from sklearn.metrics import f1_score, recall_score

    labels = np.asarray(y_true, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=float)
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


@pytest.mark.parametrize("seed", range(25))
def test_threshold_matches_exhaustive_reference_with_ties(seed):
    rng = np.random.default_rng(seed)
    size = int(rng.integers(5, 60))
    labels = rng.integers(0, 2, size=size)
    scores = np.round(rng.uniform(0, 1, size=size), 1)
    assert select_threshold(labels, scores) == _reference_threshold(labels, scores)


def test_threshold_matches_reference_without_positives_and_with_one_class():
    assert select_threshold([0, 0, 0], [0.2, 0.5, 0.9]) == _reference_threshold(
        [0, 0, 0], [0.2, 0.5, 0.9]
    )
    assert select_threshold([1, 1, 1], [0.2, 0.5, 0.9]) == _reference_threshold(
        [1, 1, 1], [0.2, 0.5, 0.9]
    )


def test_threshold_selection_scales_to_many_distinct_scores():
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 2, size=3000)
    scores = rng.uniform(0, 1, size=3000)
    started = time.perf_counter()
    select_threshold(labels, scores)
    assert time.perf_counter() - started < 1.0


def test_evaluation_contains_required_metrics_and_confusion_matrix():
    result = evaluate_predictions(
        np.array([0, 1, 0, 1]), np.array([0.1, 0.8, 0.4, 0.7]), threshold=0.7
    )
    assert result.average_precision > 0
    assert result.roc_auc > 0
    assert result.confusion_matrix == ((2, 0), (0, 2))
