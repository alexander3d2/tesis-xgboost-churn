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


def test_runner_predicts_probabilities_for_separate_test_input():
    x_train, y_train = _synthetic_training_data()
    x_test = np.ones((7, x_train.shape[1]))

    results = ModelComparisonRunner(random_state=7).run(
        x_train,
        y_train,
        x_test=x_test,
    )

    for result in results:
        assert result.probabilities.shape == (len(x_test),)
