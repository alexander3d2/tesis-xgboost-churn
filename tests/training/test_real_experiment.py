import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from app.core.constants import RANDOM_SEED
from app.training import real_experiment
from app.training.feature_vector import FEATURE_COLUMNS
from app.training.model_comparison import CONFIGURATION_CANDIDATES, MODEL_NAMES
from app.training.real_experiment import (
    RealExperimentError,
    benchmark_inference,
    compute_baselines,
    count_leaves,
    load_training_csv,
    render_markdown,
    run_real_experiment,
    select_best_index,
    write_results,
)

ID_PREFIX = "AFF-SECRET-"


def make_frame(n_dates: int = 20, rows_per_date: int = 30, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-31", periods=n_dates, freq="ME")
    records = []
    counter = 0
    for fecha in dates:
        for _ in range(rows_per_date):
            dias = int(rng.integers(0, 361))
            noise = rng.random() < 0.1
            label = (dias > 150) != noise
            records.append(
                {
                    "dias_desde_ultimo_pago": dias,
                    "frecuencia_pago_dias": float(rng.integers(1, 91)),
                    "monto_pago_promedio": float(rng.uniform(10, 200)),
                    "antiguedad_dias": int(rng.integers(10, 2000)),
                    "affiliate_id": f"{ID_PREFIX}{counter:06d}",
                    "fecha_corte": fecha.date(),
                    "desercion": bool(label),
                }
            )
            counter += 1
    return pd.DataFrame(records)


def write_csv(frame: pd.DataFrame, path: Path) -> Path:
    frame.to_csv(path, index=False)
    return path


@pytest.fixture(scope="module")
def csv_path(tmp_path_factory) -> Path:
    frame = make_frame()
    frame.loc[[0, 1, 2], "antiguedad_dias"] = -5
    return write_csv(frame, tmp_path_factory.mktemp("real") / "synthetic_train.csv")


@pytest.fixture(scope="module")
def result(csv_path) -> dict:
    return run_real_experiment(csv_path)


def test_loader_excludes_negative_antiguedad_and_reports_counts(csv_path):
    loaded = load_training_csv(csv_path)

    assert loaded.input_rows == 600
    assert loaded.excluded_rows == 3
    assert len(loaded.frame) == 597
    assert (loaded.frame["antiguedad_dias"] >= 0).all()
    assert len(loaded.sha256) == 64


def test_loader_keeps_affiliate_id_as_string_with_leading_zeros(tmp_path):
    frame = make_frame(n_dates=5, rows_per_date=2)
    frame["affiliate_id"] = [f"{index:08d}" for index in range(len(frame))]
    loaded = load_training_csv(write_csv(frame, tmp_path / "ids.csv"))

    assert loaded.frame["affiliate_id"].iloc[0] == "00000000"


def test_loader_rejects_missing_file(tmp_path):
    with pytest.raises(RealExperimentError, match="not found"):
        load_training_csv(tmp_path / "absent.csv")


def test_loader_rejects_missing_columns(tmp_path):
    frame = make_frame(n_dates=5, rows_per_date=2).drop(columns=["monto_pago_promedio", "desercion"])

    with pytest.raises(RealExperimentError, match="monto_pago_promedio") as error:
        load_training_csv(write_csv(frame, tmp_path / "bad.csv"))

    assert "desercion" in str(error.value)


def test_partitions_follow_unique_date_split_and_are_chronological(result):
    partitions = result["partitions"]

    assert partitions["train"]["unique_dates"] == 12
    assert partitions["validation"]["unique_dates"] == 4
    assert partitions["test"]["unique_dates"] == 4
    assert sum(item["rows"] for item in partitions.values()) == result["data"]["used_rows"]
    assert partitions["train"]["date_end"] < partitions["validation"]["date_start"]
    assert partitions["validation"]["date_end"] < partitions["test"]["date_start"]
    for item in partitions.values():
        assert 0 < item["positive_rate"] < 1
        assert item["positives"] > 0


def test_data_section_reports_exclusions_and_columns_without_identifier(result):
    data = result["data"]

    assert data["input_rows"] == 600
    assert data["excluded_negative_antiguedad"] == 3
    assert data["used_rows"] == 597
    assert data["feature_columns"] == FEATURE_COLUMNS
    assert "affiliate_id" not in json.dumps(result)


def test_select_best_index_prefers_highest_and_breaks_ties_by_lowest_index():
    assert select_best_index([0.5, 0.7, 0.6]) == 1
    assert select_best_index([0.5, 0.7, 0.7]) == 1
    assert select_best_index([0.9, 0.9, 0.9]) == 0


def test_all_nine_configurations_are_audited_and_selection_is_argmax(result):
    selection = result["validation_selection"]

    assert set(selection) == set(MODEL_NAMES)
    for model_name in MODEL_NAMES:
        candidates = selection[model_name]["candidates"]
        assert len(candidates) == len(CONFIGURATION_CANDIDATES[model_name]) == 3
        values = [item["primary_value"] for item in candidates]
        expected = values.index(max(values))
        assert selection[model_name]["selected_index"] == expected
        assert result["selected"][model_name]["configuration_name"] == candidates[expected]["configuration_name"]
        assert result["selected"][model_name]["hyperparameters"] == candidates[expected]["hyperparameters"]
        assert result["selected"][model_name]["validation"]["primary_value"] == values[expected]


def test_primary_metric_follows_validation_class_balance(result):
    positive_rate = result["partitions"]["validation"]["positive_rate"]
    expected = "average_precision" if positive_rate < 0.5 else "roc_auc"
    assert result["primary_metric"] == expected
    for model_name in MODEL_NAMES:
        assert result["selected"][model_name]["validation"]["primary_metric"] == expected


def test_test_partition_is_evaluated_only_for_three_selected_models_with_validation_threshold(
    csv_path, monkeypatch
):
    calls = []
    original = real_experiment.evaluate_predictions

    def spy(y_true, probabilities, threshold=None):
        calls.append(threshold)
        return original(y_true, probabilities, threshold=threshold)

    monkeypatch.setattr(real_experiment, "evaluate_predictions", spy)
    outcome = run_real_experiment(csv_path)

    assert sum(1 for threshold in calls if threshold is None) == 9
    assert sum(1 for threshold in calls if threshold is not None) == 3
    assert set(outcome["selected"]) == set(MODEL_NAMES)
    for model_name in MODEL_NAMES:
        selected = outcome["selected"][model_name]
        assert selected["test"]["threshold"] == selected["validation"]["threshold"]
        assert selected["test"]["threshold"] in [call for call in calls if call is not None]


def test_selected_models_report_all_required_test_metrics(result):
    for model_name in MODEL_NAMES:
        test = result["selected"][model_name]["test"]
        for key in ("average_precision", "roc_auc", "recall", "precision", "f1", "threshold"):
            assert isinstance(test[key], float)
        matrix = test["confusion_matrix"]
        assert sum(sum(row) for row in matrix) == result["partitions"]["test"]["rows"]
        assert all(isinstance(value, int) for row in matrix for value in row)


def test_baselines_on_hand_computable_case():
    dias = np.array([200.0, 10.0, 190.0, 100.0])
    labels = np.array([1, 0, 0, 1])

    baselines = compute_baselines(dias, labels)

    assert baselines["prevalence"]["average_precision"] == pytest.approx(0.5)
    assert baselines["rule_dias_desde_ultimo_pago_gt_180"]["precision"] == pytest.approx(0.5)
    assert baselines["rule_dias_desde_ultimo_pago_gt_180"]["recall"] == pytest.approx(0.5)
    assert baselines["rule_dias_desde_ultimo_pago_gt_180"]["f1"] == pytest.approx(0.5)
    assert baselines["single_feature_dias_desde_ultimo_pago"]["average_precision"] == pytest.approx(
        (1.0 + 2.0 / 3.0) / 2.0
    )
    assert baselines["single_feature_dias_desde_ultimo_pago"]["roc_auc"] == pytest.approx(0.75)


def test_rule_baseline_uses_strict_greater_than_180():
    dias = np.array([180.0, 181.0, 5.0, 6.0])
    labels = np.array([1, 1, 0, 0])

    rule = compute_baselines(dias, labels)["rule_dias_desde_ultimo_pago_gt_180"]

    assert rule["precision"] == pytest.approx(1.0)
    assert rule["recall"] == pytest.approx(0.5)


def test_baselines_in_result_come_from_test_partition(result):
    baselines = result["baselines"]
    assert baselines["prevalence"]["average_precision"] == pytest.approx(
        result["partitions"]["test"]["positive_rate"]
    )
    assert baselines["single_feature_dias_desde_ultimo_pago"]["roc_auc"] > 0.5


def separable_data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    signal = np.concatenate([np.linspace(0, 1, 20), np.linspace(2, 3, 20)])
    noise = rng.normal(size=(40, 3))
    return np.column_stack((signal, noise)), np.array([0] * 20 + [1] * 20)


def test_count_leaves_decision_tree():
    x, y = separable_data()
    model = DecisionTreeClassifier(max_depth=1, random_state=RANDOM_SEED).fit(x, y)

    assert count_leaves(model) == 2


def test_count_leaves_random_forest_sums_over_trees():
    x, y = separable_data()
    model = RandomForestClassifier(
        n_estimators=3, max_depth=1, bootstrap=False, random_state=RANDOM_SEED
    ).fit(x, y)

    assert count_leaves(model) == 6
    assert count_leaves(model) == sum(est.tree_.n_leaves for est in model.estimators_)


def test_count_leaves_xgboost_counts_leaf_rows():
    x, y = separable_data()
    one_tree = xgb.XGBClassifier(n_estimators=1, max_depth=1, random_state=RANDOM_SEED).fit(x, y)
    three_trees = xgb.XGBClassifier(n_estimators=3, max_depth=1, random_state=RANDOM_SEED).fit(x, y)

    assert count_leaves(one_tree) == 2
    assert count_leaves(three_trees) == 6


def test_count_leaves_rejects_unknown_model():
    with pytest.raises(RealExperimentError):
        count_leaves(object())


def test_benchmark_inference_fields_and_n_jobs_for_random_forest():
    x, y = separable_data()
    model = RandomForestClassifier(n_estimators=5, max_depth=2, n_jobs=2, random_state=0).fit(x, y)

    timing = benchmark_inference(model, x)

    assert model.n_jobs == 1
    assert timing["repetitions"] == 5
    assert timing["warmup"] == 1
    assert timing["n_jobs"] == 1
    assert timing["n_jobs_set"] is True
    assert timing["n_test_rows"] == 40
    assert timing["median_total_ms"] > 0
    assert timing["ms_per_1000_rows"] == pytest.approx(timing["median_total_ms"] / 40 * 1000)
    assert timing["single_row_latency_ms"] > 0
    assert timing["single_row_sample"] == 40


def test_benchmark_inference_skips_n_jobs_for_decision_tree():
    x, y = separable_data()
    model = DecisionTreeClassifier(max_depth=2, random_state=0).fit(x, y)

    timing = benchmark_inference(model, x)

    assert timing["n_jobs_set"] is False
    assert timing["median_total_ms"] > 0


def test_benchmark_inference_caps_single_row_sample_at_200():
    x = np.tile(separable_data()[0], (6, 1))
    y = np.tile(separable_data()[1], 6)
    model = DecisionTreeClassifier(max_depth=2, random_state=0).fit(x, y)

    assert benchmark_inference(model, x)["single_row_sample"] == 200


def test_result_contains_timing_and_leaves_for_each_selected_model(result):
    for model_name in MODEL_NAMES:
        timing = result["timing"][model_name]
        assert timing["median_total_ms"] > 0
        assert timing["ms_per_1000_rows"] > 0
        assert timing["single_row_latency_ms"] > 0
        assert timing["repetitions"] == 5
        assert timing["warmup"] == 1
        assert timing["n_jobs"] == 1
        assert result["interpretability"][model_name]["total_leaves"] >= 2
    assert result["timing"]["decision_tree"]["n_jobs_set"] is False
    assert result["timing"]["xgboost"]["n_jobs_set"] is True


def test_metadata_is_complete(result, csv_path):
    metadata = result["metadata"]

    assert len(metadata["run_id"]) == 36
    assert metadata["seed"] == RANDOM_SEED
    assert metadata["timestamp_utc"].endswith("+00:00")
    assert metadata["cpu_count"] >= 1
    assert set(metadata["versions"]) == {"xgboost", "scikit-learn", "numpy", "pandas"}
    assert metadata["python_version"]
    assert metadata["platform"]
    assert len(metadata["input_sha256"]) == 64
    assert metadata["input_sha256"] == load_training_csv(csv_path).sha256


def test_outputs_are_written_and_contain_no_identifiers(result, tmp_path):
    json_path, md_path = write_results(result, tmp_path / "resultados")

    prefix = result["metadata"]["run_id"][:8]
    assert json_path.name == f"comparacion_real_{prefix}.json"
    assert md_path.name == f"comparacion_real_{prefix}.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["run_id"] == result["metadata"]["run_id"]
    markdown = md_path.read_text(encoding="utf-8")
    for text in (json_path.read_text(encoding="utf-8"), markdown):
        assert ID_PREFIX not in text
        assert "affiliate_id" not in text
    for heading in ("Partitions", "Validation selection", "Test metrics", "Baselines", "Inference timing", "Leaves"):
        assert heading in markdown


def test_render_markdown_lists_every_model(result):
    markdown = render_markdown(result)

    for model_name in MODEL_NAMES:
        assert model_name in markdown


def test_experiment_rejects_single_class_partition(tmp_path):
    frame = make_frame()
    frame["desercion"] = False

    with pytest.raises(RealExperimentError, match="both classes"):
        run_real_experiment(write_csv(frame, tmp_path / "one_class.csv"))


def test_experiment_rejects_empty_partition(tmp_path):
    frame = make_frame(n_dates=2, rows_per_date=20)

    with pytest.raises(RealExperimentError, match="partition"):
        run_real_experiment(write_csv(frame, tmp_path / "two_dates.csv"))


def load_cli():
    path = Path(__file__).resolve().parents[2] / "notebooks" / "05_comparar_modelos.py"
    spec = importlib.util.spec_from_file_location("comparar_modelos_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_success_writes_outputs_and_prints_summary(csv_path, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    code = load_cli().main([str(csv_path)])

    output = capsys.readouterr().out
    assert code == 0
    json_files = list((tmp_path / "resultados").glob("comparacion_real_*.json"))
    md_files = list((tmp_path / "resultados").glob("comparacion_real_*.md"))
    assert len(json_files) == 1 and len(md_files) == 1
    assert json_files[0].name in output
    assert md_files[0].name in output
    for model_name in MODEL_NAMES:
        assert model_name in output
    assert ID_PREFIX not in output


def test_cli_fails_on_missing_file(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    code = load_cli().main([str(tmp_path / "absent.csv")])

    assert code != 0
    assert "not found" in capsys.readouterr().err


def test_cli_defaults_to_dataset_entrenamiento_in_cwd(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    code = load_cli().main([])

    assert code != 0
    assert "dataset_entrenamiento.csv" in capsys.readouterr().err


def test_cli_fails_on_missing_columns(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    frame = make_frame(n_dates=5, rows_per_date=2).drop(columns=["fecha_corte"])

    code = load_cli().main([str(write_csv(frame, tmp_path / "bad.csv"))])

    assert code != 0
    assert "fecha_corte" in capsys.readouterr().err
    assert not (tmp_path / "resultados").exists()


def test_cli_fails_on_single_class_partition(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    frame = make_frame()
    frame["desercion"] = True

    code = load_cli().main([str(write_csv(frame, tmp_path / "one_class.csv"))])

    assert code != 0
    assert "both classes" in capsys.readouterr().err


def test_cli_fails_on_empty_partition(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    frame = make_frame(n_dates=2, rows_per_date=20)

    code = load_cli().main([str(write_csv(frame, tmp_path / "two_dates.csv"))])

    assert code != 0
    assert "partition" in capsys.readouterr().err
