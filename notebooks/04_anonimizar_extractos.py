import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.training.anonymizer import AnonymizationError, anonymize_extracts

DEFAULT_INPUT_DIR = "Datasheet"
DEFAULT_OUTPUT_DIR = "Datasheet_anonimizado"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replace iduser with per-run random codes in the payment extracts.")
    parser.add_argument("input_dir", nargs="?", default=DEFAULT_INPUT_DIR)
    parser.add_argument("output_dir", nargs="?", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = anonymize_extracts(Path(args.input_dir), Path(args.output_dir))
    except AnonymizationError as error:
        print(f"Anonymization aborted: {error}")
        return 1

    print(f"Users: {report.users}")
    print(f"Suscripciones rows: {report.suscripciones_rows}")
    print(f"Usuarios rows: {report.usuarios_rows}")
    print(f"Payments rows: {report.payments_rows}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
