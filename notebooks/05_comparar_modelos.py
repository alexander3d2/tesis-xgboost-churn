import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.training.real_experiment import RealExperimentError, run_real_experiment, write_results

DEFAULT_DATASET_PATH = "dataset_entrenamiento.csv"
OUTPUT_DIR = "resultados"


def print_summary(result: dict, json_path: Path, markdown_path: Path) -> None:
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    data = result["data"]
    print(
        f"Rows: input={data['input_rows']} excluded={data['excluded_negative_antiguedad']} used={data['used_rows']}"
    )
    for name, item in result["partitions"].items():
        print(f"Partition {name}: rows={item['rows']} positive_rate={item['positive_rate']:.4f}")
    print(f"Primary metric (validation): {result['primary_metric']}")
    for model_name, item in result["selected"].items():
        test = item["test"]
        timing = result["timing"][model_name]
        print(
            f"{model_name} [{item['configuration_name']}]: "
            f"test AP={test['average_precision']:.4f} AUC={test['roc_auc']:.4f} "
            f"recall={test['recall']:.4f} precision={test['precision']:.4f} f1={test['f1']:.4f} "
            f"leaves={result['interpretability'][model_name]['total_leaves']} "
            f"ms/1000rows={timing['ms_per_1000_rows']:.2f}"
        )
    print(f"Prevalence AP (test): {result['baselines']['prevalence']['average_precision']:.4f}")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    dataset_path = args[0] if args else DEFAULT_DATASET_PATH
    try:
        result = run_real_experiment(dataset_path)
        json_path, markdown_path = write_results(result, OUTPUT_DIR)
    except RealExperimentError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"ERROR: unexpected failure: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print_summary(result, json_path, markdown_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
