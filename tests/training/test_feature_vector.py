from app.core.features import AffiliateFeatures
from app.training.dataset_builder import TrainingExampleFeatures
from app.training.feature_vector import FEATURE_COLUMNS, to_feature_vector


def test_feature_columns_are_the_four_payment_based_variables_in_order():
    assert FEATURE_COLUMNS == [
        "dias_desde_ultimo_pago",
        "frecuencia_pago_dias",
        "monto_pago_promedio",
        "antiguedad_dias",
    ]


def test_to_feature_vector_matches_feature_columns_order_and_length():
    features = TrainingExampleFeatures(
        affiliate=AffiliateFeatures(
            dias_desde_ultimo_pago=31,
            frecuencia_pago_dias=30.5,
            monto_pago_promedio=106.67,
            antiguedad_dias=608,
        ),
    )

    vector = to_feature_vector(features)

    assert len(vector) == len(FEATURE_COLUMNS)
    assert vector == [31, 30.5, 106.67, 608]


def test_to_feature_vector_allows_none_for_missing_exploratory_values():
    features = TrainingExampleFeatures(
        affiliate=AffiliateFeatures(
            dias_desde_ultimo_pago=5,
            frecuencia_pago_dias=None,
            monto_pago_promedio=90.0,
            antiguedad_dias=200,
        ),
    )

    vector = to_feature_vector(features)

    assert vector[1] is None
