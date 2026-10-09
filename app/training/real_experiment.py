import hashlib
import json
import os
import platform
import statistics
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.tree import DecisionTreeClassifier

from app.core.constants import RANDOM_SEED
from app.training.evaluation import EvaluationMetrics, evaluate_predictions
from app.training.feature_vector import FEATURE_COLUMNS
from app.training.model_comparison import MODEL_NAMES, ModelComparisonResult, ModelComparisonRunner
from app.training.synthetic_experiment import SyntheticDataset, TemporalSplit, temporal_split_60_20_20

IDENTIFIER_COLUMN = "affiliate_id"
DATE_COLUMN = "fecha_corte"
LABEL_COLUMN = "desercion"
REQUIRED_COLUMNS = (*FEATURE_COLUMNS, IDENTIFIER_COLUMN, DATE_COLUMN, LABEL_COLUMN)
RULE_THRESHOLD_DAYS = 180
BENCHMARK_REPETITIONS = 5
BENCHMARK_WARMUP = 1
SINGLE_ROW_SAMPLE = 200
RESULT_PREFIX = "comparacion_real_"
DAYS_FEATURE_INDEX = FEATURE_COLUMNS.index("dias_desde_ultimo_pago")


class RealExperimentError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedTrainingData:
    frame: pd.DataFrame
    input_rows: int
    excluded_rows: int
    sha256: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_training_csv(path: str | Path) -> LoadedTrainingData:
    source = Path(path)
    if not source.is_file():
        raise RealExperimentError(f"input file not found: {source}")
    try:
        frame = pd.read_csv(source, dtype={IDENTIFIER_COLUMN: str})
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise RealExperimentError(f"input file could not be parsed: {source} ({error})") from error
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise RealExperimentError(f"input file is missing required columns: {', '.join(missing)}")
    try:
        frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="raise")
    except (ValueError, TypeError) as error:
        raise RealExperimentError(f"column {DATE_COLUMN} contains invalid dates") from error
    if frame[DATE_COLUMN].isna().any():
        raise RealExperimentError(f"column {DATE_COLUMN} contains missing dates")
    if frame[LABEL_COLUMN].isna().any():
        raise RealExperimentError(f"column {LABEL_COLUMN} contains missing values")
    try:
        frame[LABEL_COLUMN] = frame[LABEL_COLUMN].astype(int)
    except (ValueError, TypeError) as error:
        raise RealExperimentError(f"column {LABEL_COLUMN} must be boolean or 0/1") from error
    if not frame[LABEL_COLUMN].isin([0, 1]).all():
        raise RealExperimentError(f"column {LABEL_COLUMN} must be boolean or 0/1")
    input_rows = len(frame)
    kept = frame[~(frame["antiguedad_dias"] < 0)].reset_index(drop=True)
    return LoadedTrainingData(
        frame=kept,
        input_rows=input_rows,
        excluded_rows=input_rows - len(kept),
        sha256=file_sha256(source),
    )


def to_dataset(frame: pd.DataFrame) -> SyntheticDataset:
    try:
        features = frame[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    except (ValueError, TypeError) as error:
        raise RealExperimentError("feature columns must be numeric") from error
    return SyntheticDataset(
        features=features,
        labels=frame[LABEL_COLUMN].to_numpy(dtype=np.int8),
        subject_ids=frame[IDENTIFIER_COLUMN].to_numpy(dtype=str),
        reference_dates=frame[DATE_COLUMN].to_numpy().astype("datetime64[D]"),
        feature_columns=tuple(FEATURE_COLUMNS),
        source="real",
    )


def split_dataset(dataset: SyntheticDataset) -> TemporalSplit:
    try:
        split = temporal_split_60_20_20(dataset)
    except ValueError as error:
        raise RealExperimentError(f"cannot build chronological partitions: {error}") from error
    for name in ("train", "validation", "test"):
        part = getattr(split, name)
        positives = int(np.sum(part.labels == 1))
        negatives = int(np.sum(part.labels == 0))
        if len(part.labels) == 0:
            raise RealExperimentError(f"partition '{name}' is empty")
        if positives == 0 or negatives == 0:
            raise RealExperimentError(
                f"partition '{name}' must contain both classes (positives={positives}, negatives={negatives})"
            )
    return split


def summarize_partition(part: SyntheticDataset) -> dict[str, Any]:
    rows = int(len(part.labels))
    positives = int(np.sum(part.labels == 1))
    return {
        "rows": rows,
        "positives": positives,
        "positive_rate": positives / rows,
        "unique_dates": int(len(np.unique(part.reference_dates))),
        "date_start": str(part.reference_dates.min()),
        "date_end": str(part.reference_dates.max()),
    }


def metrics_to_dict(metrics: EvaluationMetrics) -> dict[str, Any]:
    return {
        "average_precision": metrics.average_precision,
        "roc_auc": metrics.roc_auc,
        "recall": metrics.recall,
        "precision": metrics.precision,
        "f1": metrics.f1,
        "confusion_matrix": [[int(value) for value in row] for row in metrics.confusion_matrix],
        "threshold": metrics.threshold,
        "primary_metric": metrics.primary_metric,
        "primary_value": metrics.primary_value,
        "contingency_metric": metrics.contingency_metric,
        "contingency_value": metrics.contingency_value,
    }


def select_best_index(values: Sequence[float]) -> int:
    best_index = 0
    for index, value in enumerate(values):
        if value > values[best_index]:
            best_index = index
    return best_index


def count_leaves(model: Any) -> int:
    if isinstance(model, DecisionTreeClassifier):
        return int(model.tree_.n_leaves)
    if isinstance(model, RandomForestClassifier):
        return int(sum(estimator.tree_.n_leaves for estimator in model.estimators_))
    if isinstance(model, xgb.XGBClassifier):
        trees = model.get_booster().trees_to_dataframe()
        return int((trees["Feature"] == "Leaf").sum())
    raise RealExperimentError(f"unsupported model type for leaf counting: {type(model).__name__}")


def compute_baselines(days_since_last_payment: Sequence[float], labels: Sequence[int]) -> dict[str, Any]:
    scores = np.asarray(days_since_last_payment, dtype=float)
    y_true = np.asarray(labels, dtype=np.int8)
    missing = int(np.isnan(scores).sum())
    if missing:
        scores = np.where(np.isnan(scores), np.nanmin(scores) - 1.0, scores)
    predicted = (scores > RULE_THRESHOLD_DAYS).astype(np.int8)
    return {
        "prevalence": {"average_precision": float(np.mean(y_true))},
        f"rule_dias_desde_ultimo_pago_gt_{RULE_THRESHOLD_DAYS}": {
            "precision": float(precision_score(y_true, predicted, zero_division=0)),
            "recall": float(recall_score(y_true, predicted, zero_division=0)),
            "f1": float(f1_score(y_true, predicted, zero_division=0)),
        },
        "single_feature_dias_desde_ultimo_pago": {
            "average_precision": float(average_precision_score(y_true, scores)),
            "roc_auc": float(roc_auc_score(y_true, scores)),
            "missing_scores_filled": missing,
        },
    }


def benchmark_inference(
    model: Any,
    x_test: np.ndarray,
    repetitions: int = BENCHMARK_REPETITIONS,
    warmup: int = BENCHMARK_WARMUP,
    single_row_sample: int = SINGLE_ROW_SAMPLE,
) -> dict[str, Any]:
    n_jobs_set = "n_jobs" in model.get_params()
    if n_jobs_set:
        model.set_params(n_jobs=1)
    for _ in range(warmup):
        model.predict_proba(x_test)
    totals = []
    for _ in range(repetitions):
        started = time.perf_counter()
        model.predict_proba(x_test)
        totals.append((time.perf_counter() - started) * 1000.0)
    n_rows = int(x_test.shape[0])
    median_total_ms = statistics.median(totals)
    sample = min(single_row_sample, n_rows)
    latencies = []
    for index in range(sample):
        started = time.perf_counter()
        model.predict_proba(x_test[index : index + 1])
        latencies.append((time.perf_counter() - started) * 1000.0)
    return {
        "repetitions": repetitions,
        "warmup": warmup,
        "n_jobs": 1,
        "n_jobs_set": n_jobs_set,
        "n_test_rows": n_rows,
        "median_total_ms": median_total_ms,
        "ms_per_1000_rows": median_total_ms / n_rows * 1000.0,
        "single_row_latency_ms": statistics.median(latencies),
        "single_row_sample": sample,
    }


def select_configurations(
    comparisons: Sequence[ModelComparisonResult],
    validation_labels: np.ndarray,
) -> dict[str, dict[str, Any]]:
    selection: dict[str, dict[str, Any]] = {}
    for model_name in MODEL_NAMES:
        entries = [item for item in comparisons if item.model_name == model_name]
        metrics = [evaluate_predictions(validation_labels, item.probabilities) for item in entries]
        index = select_best_index([item.primary_value for item in metrics])
        selection[model_name] = {
            "entries": entries,
            "metrics": metrics,
            "selected_index": index,
        }
    return selection


def environment_metadata(run_id: str, loaded: LoadedTrainingData) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": RANDOM_SEED,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "versions": {
            "xgboost": xgb.__version__,
            "scikit-learn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "input_sha256": loaded.sha256,
    }


def run_real_experiment(csv_path: str | Path) -> dict[str, Any]:
    loaded = load_training_csv(csv_path)
    dataset = to_dataset(loaded.frame)
    split = split_dataset(dataset)
    run_id = str(uuid.uuid4())

    comparisons = ModelComparisonRunner(random_state=RANDOM_SEED).run_configurations(
        split.train.features,
        split.train.labels,
        x_test=split.validation.features,
    )
    selection = select_configurations(comparisons, split.validation.labels)
    primary_metric = next(iter(selection.values()))["metrics"][0].primary_metric

    validation_selection: dict[str, Any] = {}
    selected: dict[str, Any] = {}
    timing: dict[str, Any] = {}
    interpretability: dict[str, Any] = {}
    for model_name in MODEL_NAMES:
        entries = selection[model_name]["entries"]
        metrics = selection[model_name]["metrics"]
        index = selection[model_name]["selected_index"]
        validation_selection[model_name] = {
            "selected_index": index,
            "candidates": [
                {
                    "configuration_name": entry.configuration_name,
                    "hyperparameters": dict(entry.configuration),
                    "primary_value": metric.primary_value,
                }
                for entry, metric in zip(entries, metrics)
            ],
        }
        chosen = entries[index]
        validation_metrics = metrics[index]
        test_metrics = evaluate_predictions(
            split.test.labels,
            chosen.model.predict_proba(split.test.features)[:, 1],
            threshold=validation_metrics.threshold,
        )
        selected[model_name] = {
            "configuration_name": chosen.configuration_name,
            "hyperparameters": dict(chosen.configuration),
            "validation": metrics_to_dict(validation_metrics),
            "test": metrics_to_dict(test_metrics),
        }
        timing[model_name] = benchmark_inference(chosen.model, split.test.features)
        interpretability[model_name] = {"total_leaves": count_leaves(chosen.model)}

    metadata = environment_metadata(run_id, loaded)
    metadata["selected_hyperparameters"] = {
        name: {"configuration_name": item["configuration_name"], "hyperparameters": item["hyperparameters"]}
        for name, item in selected.items()
    }
    return {
        "metadata": metadata,
        "data": {
            "input_rows": loaded.input_rows,
            "excluded_negative_antiguedad": loaded.excluded_rows,
            "used_rows": len(loaded.frame),
            "feature_columns": list(FEATURE_COLUMNS),
            "dataset_columns": [column for column in loaded.frame.columns if column != IDENTIFIER_COLUMN],
            "identifier_column_omitted": True,
        },
        "partitions": {
            "train": summarize_partition(split.train),
            "validation": summarize_partition(split.validation),
            "test": summarize_partition(split.test),
        },
        "primary_metric": primary_metric,
        "validation_selection": validation_selection,
        "selected": selected,
        "baselines": compute_baselines(split.test.features[:, DAYS_FEATURE_INDEX], split.test.labels),
        "timing": timing,
        "interpretability": interpretability,
    }


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_markdown(result: dict[str, Any]) -> str:
    metadata = result["metadata"]
    data = result["data"]
    sections = [
        f"# Model comparison on real data ({metadata['run_id']})",
        f"- Timestamp (UTC): {metadata['timestamp_utc']}\n"
        f"- Seed: {metadata['seed']}\n"
        f"- Input SHA-256: {metadata['input_sha256']}\n"
        f"- Input rows: {data['input_rows']}, excluded (antiguedad_dias < 0): "
        f"{data['excluded_negative_antiguedad']}, used: {data['used_rows']}\n"
        f"- Primary metric: {result['primary_metric']}",
        "## Partitions",
        markdown_table(
            ["partition", "rows", "positives", "positive_rate", "unique_dates", "date_start", "date_end"],
            [
                [
                    name,
                    item["rows"],
                    item["positives"],
                    f"{item['positive_rate']:.4f}",
                    item["unique_dates"],
                    item["date_start"],
                    item["date_end"],
                ]
                for name, item in result["partitions"].items()
            ],
        ),
        "## Validation selection",
        markdown_table(
            ["model", "configuration", "validation primary_value", "selected", "hyperparameters"],
            [
                [
                    model_name,
                    candidate["configuration_name"],
                    f"{candidate['primary_value']:.4f}",
                    "yes" if position == item["selected_index"] else "",
                    json.dumps(candidate["hyperparameters"]),
                ]
                for model_name, item in result["validation_selection"].items()
                for position, candidate in enumerate(item["candidates"])
            ],
        ),
        "## Test metrics",
        markdown_table(
            ["model", "configuration", "average_precision", "roc_auc", "recall", "precision", "f1", "threshold", "confusion_matrix"],
            [
                [
                    model_name,
                    item["configuration_name"],
                    f"{item['test']['average_precision']:.4f}",
                    f"{item['test']['roc_auc']:.4f}",
                    f"{item['test']['recall']:.4f}",
                    f"{item['test']['precision']:.4f}",
                    f"{item['test']['f1']:.4f}",
                    f"{item['test']['threshold']:.4f}",
                    json.dumps(item["test"]["confusion_matrix"]),
                ]
                for model_name, item in result["selected"].items()
            ],
        ),
        markdown_table(
            ["model", "validation average_precision", "validation roc_auc", "validation recall", "validation precision", "validation f1"],
            [
                [
                    model_name,
                    f"{item['validation']['average_precision']:.4f}",
                    f"{item['validation']['roc_auc']:.4f}",
                    f"{item['validation']['recall']:.4f}",
                    f"{item['validation']['precision']:.4f}",
                    f"{item['validation']['f1']:.4f}",
                ]
                for model_name, item in result["selected"].items()
            ],
        ),
        "## Baselines (test partition)",
        markdown_table(
            ["baseline", "metrics"],
            [[name, json.dumps(values)] for name, values in result["baselines"].items()],
        ),
        "## Inference timing",
        markdown_table(
            ["model", "ms_per_1000_rows", "median_total_ms", "single_row_latency_ms", "repetitions", "warmup", "n_jobs"],
            [
                [
                    model_name,
                    f"{item['ms_per_1000_rows']:.3f}",
                    f"{item['median_total_ms']:.3f}",
                    f"{item['single_row_latency_ms']:.4f}",
                    item["repetitions"],
                    item["warmup"],
                    item["n_jobs"],
                ]
                for model_name, item in result["timing"].items()
            ],
        ),
        "## Leaves",
        markdown_table(
            ["model", "total_leaves"],
            [[model_name, item["total_leaves"]] for model_name, item in result["interpretability"].items()],
        ),
    ]
    return "\n\n".join(sections) + "\n"


def write_results(result: dict[str, Any], output_dir: str | Path) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{RESULT_PREFIX}{result['metadata']['run_id'][:8]}"
    json_path = directory / f"{stem}.json"
    markdown_path = directory / f"{stem}.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    return json_path, markdown_path
