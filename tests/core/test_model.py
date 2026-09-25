import numpy as np

from app.core.model import predict_proba, train


def test_train_and_predict_returns_probability_between_0_and_1():
    rng = np.random.default_rng(seed=42)
    x_train = rng.random((20, 3))
    y_train = rng.integers(0, 2, size=20)

    model = train(x_train, y_train)
    probability = predict_proba(model, x_train[:1])

    assert 0.0 <= probability <= 1.0
