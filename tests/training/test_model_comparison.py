import numpy as np

from app.training.model_comparison import (
    MODEL_NAMES,
    ModelComparisonRunner,
    compare_models,
)


def _synthetic_training_data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed=42)
    x = rng.random((30, 3))
    y = np.array([0, 1] * 15)
    return x, y


def test_compare_models_uses_all_candidates_and_returns_probabilities():
    x, y = _synthetic_training_data()

    results = compare_models(x, y)

    assert tuple(result.model_name for result in results) == MODEL_NAMES
    for result in results:
        assert result.probabilities.shape == (len(x),)
        assert np.all((0.0 <= result.probabilities) & (result.probabilities <= 1.0))
        assert result.model.n_features_in_ == x.shape[1]


def test_runner_is_deterministic_with_the_same_seed_and_input():
    x, y = _synthetic_training_data()

    first = ModelComparisonRunner(random_state=7).run(x, y)
    second = ModelComparisonRunner(random_state=7).run(x, y)

    for first_result, second_result in zip(first, second):
        np.testing.assert_array_equal(
            first_result.probabilities,
            second_result.probabilities,
        )
