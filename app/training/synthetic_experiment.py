"""Synthetic-only scaffolding for validating the experimental plumbing.

This module intentionally does not estimate scientific metrics or make model
selection decisions. Its values are fixtures for testing integration only.
"""

from dataclasses import dataclass
from datetime import date

import numpy as np

from app.training.feature_vector import FEATURE_COLUMNS
from app.training.model_comparison import ModelComparisonResult, compare_models


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
    test: SyntheticDataset
    cutoff: np.datetime64


@dataclass(frozen=True)
class SyntheticExperimentResult:
    dataset: SyntheticDataset
    split: TemporalSplit
    comparisons: tuple[ModelComparisonResult, ...]


def generate_synthetic_dataset(
    seed: int,
    n_samples: int = 60,
) -> SyntheticDataset:
    """Generate reproducible fixture rows using only the explicit seed."""
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
    labels = rng.permutation(np.arange(n_samples) % 2).astype(np.int8)
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
) -> TemporalSplit:
    """Split strictly before and on/after an explicit date cutoff."""
    normalized_cutoff = np.datetime64(cutoff, "D")
    train_mask = dataset.reference_dates < normalized_cutoff
    test_mask = dataset.reference_dates >= normalized_cutoff
    if not train_mask.any() or not test_mask.any():
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
        test=select(test_mask),
        cutoff=normalized_cutoff,
    )


def run_synthetic_experiment(
    seed: int,
    n_samples: int = 60,
) -> SyntheticExperimentResult:
    """Generate, split, and execute candidates without evaluating them."""
    dataset = generate_synthetic_dataset(seed=seed, n_samples=n_samples)
    cutoff = dataset.reference_dates[n_samples // 2]
    split = temporal_split(dataset, cutoff=cutoff)
    comparisons = compare_models(
        split.train.features,
        split.train.labels,
        random_state=seed,
        x_test=split.test.features,
    )
    return SyntheticExperimentResult(
        dataset=dataset,
        split=split,
        comparisons=comparisons,
    )
