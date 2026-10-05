import numpy as np

from app.training.feature_vector import FEATURE_COLUMNS
from app.training.synthetic_experiment import (
    generate_synthetic_dataset,
    run_synthetic_experiment,
    temporal_split,
)


def test_generation_is_reproducible_and_uses_current_feature_order():
    first = generate_synthetic_dataset(seed=11, n_samples=24)
    second = generate_synthetic_dataset(seed=11, n_samples=24)

    np.testing.assert_array_equal(first.features, second.features)
    np.testing.assert_array_equal(first.labels, second.labels)
    np.testing.assert_array_equal(first.subject_ids, second.subject_ids)
    np.testing.assert_array_equal(first.reference_dates, second.reference_dates)
    assert first.feature_columns == tuple(FEATURE_COLUMNS)
    assert first.source == "synthetic"


def test_temporal_split_isolates_dates_and_rejects_empty_partitions():
    dataset = generate_synthetic_dataset(seed=3, n_samples=20)
    cutoff = dataset.reference_dates[12]

    split = temporal_split(dataset, cutoff=cutoff)

    assert np.all(split.train.reference_dates < cutoff)
    assert np.all(split.test.reference_dates >= cutoff)
    assert len(split.train.reference_dates) > 0
    assert len(split.test.reference_dates) > 0

    with np.testing.assert_raises(ValueError):
        temporal_split(dataset, cutoff=dataset.reference_dates[0])


def test_synthetic_experiment_executes_all_candidates_on_test_shape():
    result = run_synthetic_experiment(seed=5, n_samples=30)

    assert tuple(item.model_name for item in result.comparisons) == (
        "xgboost",
        "random_forest",
        "decision_tree",
    )
    for item in result.comparisons:
        assert item.probabilities.shape == (len(result.split.test.labels),)
