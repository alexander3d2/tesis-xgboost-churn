from dataclasses import dataclass
from datetime import date

import numpy as np

from app.training.feature_vector import FEATURE_COLUMNS
from app.training.evaluation import EvaluationMetrics, evaluate_predictions
from app.training.model_comparison import ModelComparisonResult, ModelComparisonRunner


@dataclass(frozen=True)
class SyntheticDataset:
    features: np.ndarray
    labels: np.ndarray
    subject_ids: np.ndarray
    reference_dates: np.ndarray
    feature_columns: tuple[str, ...]
    source: str = "synthetic"


@dataclass(frozen=True)
class TemporalSplit:
    train: SyntheticDataset
    validation: SyntheticDataset
    test: SyntheticDataset
    cutoff: np.datetime64
    validation_cutoff: np.datetime64


@dataclass(frozen=True)
class SyntheticEvaluationRecord:
    model_name: str
    configuration_name: str
    validation: EvaluationMetrics
    test: EvaluationMetrics


@dataclass(frozen=True)
class SyntheticExperimentResult:
    dataset: SyntheticDataset
    split: TemporalSplit
    comparisons: tuple[ModelComparisonResult, ...]
    evaluations: tuple[SyntheticEvaluationRecord, ...]


def generate_synthetic_dataset(
    seed: int,
    n_samples: int = 60,
) -> SyntheticDataset:
    if n_samples < 2:
        raise ValueError("n_samples must be at least 2")

    rng = np.random.default_rng(seed)
    features = np.column_stack(
        (
            rng.integers(0, 181, size=n_samples),
            rng.integers(1, 31, size=n_samples),
            rng.uniform(0.0, 1000.0, size=n_samples),
            rng.integers(0, 3651, size=n_samples),
            rng.integers(0, 181, size=n_samples),
            rng.integers(0, 51, size=n_samples),
            rng.integers(0, 51, size=n_samples),
            rng.integers(0, 101, size=n_samples),
        )
    ).astype(float)
    labels = np.zeros(n_samples, dtype=np.int8)
    positive_count = max(1, n_samples // 4)
    labels[:positive_count] = 1
    labels = rng.permutation(labels)
    subject_ids = np.array(
        [f"SYN-{index:06d}" for index in range(n_samples)],
        dtype="U10",
    )
    start_date = np.datetime64(date(2025, 1, 1), "D")
    reference_dates = start_date + np.arange(n_samples).astype("timedelta64[D]")
    return SyntheticDataset(
        features=features,
        labels=labels,
        subject_ids=subject_ids,
        reference_dates=reference_dates,
        feature_columns=tuple(FEATURE_COLUMNS),
    )


def temporal_split(
    dataset: SyntheticDataset,
    cutoff: np.datetime64 | str,
    validation_cutoff: np.datetime64 | str | None = None,
) -> TemporalSplit:
    normalized_cutoff = np.datetime64(cutoff, "D")
    normalized_validation_cutoff = (
        np.datetime64(validation_cutoff, "D")
        if validation_cutoff is not None
        else normalized_cutoff
    )
    train_mask = dataset.reference_dates < normalized_cutoff
    validation_mask = (
        (dataset.reference_dates >= normalized_cutoff)
        & (dataset.reference_dates < normalized_validation_cutoff)
    )
    test_mask = dataset.reference_dates >= normalized_validation_cutoff
    if not train_mask.any() or not test_mask.any() or (
        validation_cutoff is not None and not validation_mask.any()
    ):
        raise ValueError("temporal cutoff must produce non-empty train and test partitions")

    def select(mask: np.ndarray) -> SyntheticDataset:
        return SyntheticDataset(
            features=dataset.features[mask],
            labels=dataset.labels[mask],
            subject_ids=dataset.subject_ids[mask],
            reference_dates=dataset.reference_dates[mask],
            feature_columns=dataset.feature_columns,
            source=dataset.source,
        )

    return TemporalSplit(
        train=select(train_mask),
        validation=select(validation_mask) if validation_cutoff is not None else select(test_mask),
        test=select(test_mask),
        cutoff=normalized_cutoff,
        validation_cutoff=normalized_validation_cutoff,
    )


def temporal_split_60_20_20(dataset: SyntheticDataset) -> TemporalSplit:
    dates = np.unique(dataset.reference_dates)
    train_count = int(len(dates) * 0.60)
    validation_count = int(len(dates) * 0.20)
    if train_count < 1 or validation_count < 1 or len(dates) - train_count - validation_count < 1:
        raise ValueError("60/20/20 temporal partition would contain an empty partition")
    return temporal_split(
        dataset,
        cutoff=dates[train_count],
        validation_cutoff=dates[train_count + validation_count],
    )


def run_synthetic_experiment(
    seed: int,
    n_samples: int = 60,
) -> SyntheticExperimentResult:
    dataset = generate_synthetic_dataset(seed=seed, n_samples=n_samples)
    split = temporal_split_60_20_20(dataset)
    comparisons = ModelComparisonRunner(random_state=seed).run_configurations(
        split.train.features,
        split.train.labels,
        x_test=split.validation.features,
    )
    evaluations = tuple(
        SyntheticEvaluationRecord(
            model_name=item.model_name,
            configuration_name=item.configuration_name,
            validation=evaluate_predictions(split.validation.labels, item.probabilities),
            test=evaluate_predictions(
                split.test.labels,
                item.model.predict_proba(split.test.features)[:, 1],
                threshold=evaluate_predictions(split.validation.labels, item.probabilities).threshold,
            ),
        )
        for item in comparisons
    )
    return SyntheticExperimentResult(
        dataset=dataset,
        split=split,
        comparisons=comparisons,
        evaluations=evaluations,
    )
