import numpy as np

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


def test_evaluation_contains_required_metrics_and_confusion_matrix():
    result = evaluate_predictions(
        np.array([0, 1, 0, 1]), np.array([0.1, 0.8, 0.4, 0.7]), threshold=0.7
    )
    assert result.average_precision > 0
    assert result.roc_auc > 0
    assert result.confusion_matrix == ((2, 0), (0, 2))
