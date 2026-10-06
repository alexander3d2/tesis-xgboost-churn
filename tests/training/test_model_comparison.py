import numpy as np

from app.training.model_comparison import (
    CONFIGURATION_CANDIDATES,
    MODEL_NAMES,
    ModelComparisonRunner,
    compare_models,
)


def test_each_model_has_exactly_three_explicit_synthetic_scaffold_configs():
    assert tuple(len(CONFIGURATION_CANDIDATES[name]) for name in MODEL_NAMES) == (3, 3, 3)
    assert all(all(configuration for configuration in configs) for configs in CONFIGURATION_CANDIDATES.values())


def test_runner_can_execute_all_nine_scaffold_candidates():
    x, y = _synthetic_training_data()
    results = ModelComparisonRunner(random_state=7).run_configurations(x, y)
    assert len(results) == 9
    assert all(result.configuration_name in {"scaffold-1", "scaffold-2", "scaffold-3"} for result in results)


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
