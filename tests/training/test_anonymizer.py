import dataclasses
import importlib.util
import re
from pathlib import Path

import pandas as pd
import pytest

from app.training import anonymizer
from app.training.anonymizer import (
    AnonymizationError,
    AnonymizationReport,
    anonymize_extracts,
)

CODE_PATTERN = re.compile(r"^U[0-9A-F]{12}$")
EXPECTED_FILES = {"payments.csv", "suscripciones.csv", "usuarios.csv"}
PAYMENTS_BYTES = (
    b"1,2026-07-01,100.0,2026-08-01,1\r\n"
    b"1,2026-08-01,100.0,2026-09-01,2\r\n"
    b"3,2026-07-15,50.5,2026-08-15,1\r\n"
)
ORIGINAL_USER_IDS = ["00123", "456", "789"]


def _write_extracts(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "payments.csv").write_bytes(PAYMENTS_BYTES)
    (input_dir / "suscripciones.csv").write_text("1,00123\n2,00123\n3,456\n", encoding="utf-8")
    (input_dir / "usuarios.csv").write_text(
        "00123,2025-01-01\n456,2025-02-01\n789,2025-03-01\n", encoding="utf-8"
    )


def _read(path: Path, names: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, header=None, names=names, dtype=str, keep_default_na=False)


@pytest.fixture
def extracts(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _write_extracts(input_dir)
    return input_dir, output_dir


def test_same_original_id_maps_to_same_code_in_both_files(extracts):
    input_dir, output_dir = extracts

    anonymize_extracts(input_dir, output_dir)

    suscripciones = _read(output_dir / "suscripciones.csv", ["idsuscription", "iduser"])
    usuarios = _read(output_dir / "usuarios.csv", ["iduser", "createdate"])
    assert suscripciones["iduser"].iloc[0] == suscripciones["iduser"].iloc[1]
    assert suscripciones["iduser"].iloc[0] == usuarios["iduser"].iloc[0]
    assert suscripciones["iduser"].iloc[2] == usuarios["iduser"].iloc[1]
    assert set(suscripciones["iduser"]) <= set(usuarios["iduser"])


def test_codes_match_expected_format(extracts):
    input_dir, output_dir = extracts

    anonymize_extracts(input_dir, output_dir)

    usuarios = _read(output_dir / "usuarios.csv", ["iduser", "createdate"])
    suscripciones = _read(output_dir / "suscripciones.csv", ["idsuscription", "iduser"])
    for code in list(usuarios["iduser"]) + list(suscripciones["iduser"]):
        assert CODE_PATTERN.match(code)


def test_distinct_original_ids_get_distinct_codes_and_none_leak(extracts):
    input_dir, output_dir = extracts

    anonymize_extracts(input_dir, output_dir)

    usuarios = _read(output_dir / "usuarios.csv", ["iduser", "createdate"])
    assert usuarios["iduser"].nunique() == len(ORIGINAL_USER_IDS)
    assert not set(usuarios["iduser"]) & set(ORIGINAL_USER_IDS)


def test_other_columns_and_row_order_are_preserved(extracts):
    input_dir, output_dir = extracts

    anonymize_extracts(input_dir, output_dir)

    suscripciones = _read(output_dir / "suscripciones.csv", ["idsuscription", "iduser"])
    usuarios = _read(output_dir / "usuarios.csv", ["iduser", "createdate"])
    assert list(suscripciones["idsuscription"]) == ["1", "2", "3"]
    assert list(usuarios["createdate"]) == ["2025-01-01", "2025-02-01", "2025-03-01"]


def test_payments_file_is_copied_byte_for_byte(extracts):
    input_dir, output_dir = extracts

    anonymize_extracts(input_dir, output_dir)

    assert (output_dir / "payments.csv").read_bytes() == PAYMENTS_BYTES


def test_only_the_three_expected_files_are_written_and_no_mapping_exists(extracts, tmp_path):
    input_dir, output_dir = extracts
    for extra in ("wallets.csv", "affiliate.csv", "usercustomer.csv", "wallet_transacciones.csv"):
        (input_dir / extra).write_text("1,2\n", encoding="utf-8")

    anonymize_extracts(input_dir, output_dir)

    assert {path.name for path in output_dir.iterdir()} == EXPECTED_FILES
    all_files = {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()}
    assert all_files == {
        f"in/{name}" for name in EXPECTED_FILES | {"wallets.csv", "affiliate.csv", "usercustomer.csv", "wallet_transacciones.csv"}
    } | {f"out/{name}" for name in EXPECTED_FILES}


def test_different_runs_produce_different_codes(tmp_path):
    input_dir = tmp_path / "in"
    _write_extracts(input_dir)

    anonymize_extracts(input_dir, tmp_path / "out1")
    anonymize_extracts(input_dir, tmp_path / "out2")

    first = _read(tmp_path / "out1" / "usuarios.csv", ["iduser", "createdate"])
    second = _read(tmp_path / "out2" / "usuarios.csv", ["iduser", "createdate"])
    assert not set(first["iduser"]) & set(second["iduser"])


def test_report_contains_only_counts(extracts):
    input_dir, output_dir = extracts

    report = anonymize_extracts(input_dir, output_dir)

    assert isinstance(report, AnonymizationReport)
    assert dataclasses.asdict(report) == {
        "users": 3,
        "suscripciones_rows": 3,
        "usuarios_rows": 3,
        "payments_rows": 3,
    }


def test_code_collision_raises_explicit_error_and_writes_nothing(extracts, monkeypatch):
    input_dir, output_dir = extracts
    monkeypatch.setattr(anonymizer, "build_user_code", lambda key, iduser: "U000000000000")

    with pytest.raises(AnonymizationError, match="collision"):
        anonymize_extracts(input_dir, output_dir)

    assert not output_dir.exists() or not any(output_dir.iterdir())


def test_invalid_code_format_fails_postcondition(extracts, monkeypatch):
    input_dir, output_dir = extracts
    counter = iter(range(100))
    monkeypatch.setattr(anonymizer, "build_user_code", lambda key, iduser: f"X{next(counter)}")

    with pytest.raises(AnonymizationError, match="format"):
        anonymize_extracts(input_dir, output_dir)


def test_missing_input_file_raises(extracts):
    input_dir, output_dir = extracts
    (input_dir / "usuarios.csv").unlink()

    with pytest.raises(AnonymizationError, match="usuarios.csv"):
        anonymize_extracts(input_dir, output_dir)

    assert not output_dir.exists()


def test_refuses_when_output_dir_equals_input_dir(extracts):
    input_dir, _ = extracts

    with pytest.raises(AnonymizationError, match="output"):
        anonymize_extracts(input_dir, input_dir)

    assert (input_dir / "usuarios.csv").read_text(encoding="utf-8").startswith("00123,")


def test_rejects_extract_with_unexpected_column_count(extracts):
    input_dir, output_dir = extracts
    (input_dir / "usuarios.csv").write_text("00123,2025-01-01,extra\n", encoding="utf-8")

    with pytest.raises(AnonymizationError, match="columns"):
        anonymize_extracts(input_dir, output_dir)


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "notebooks" / "04_anonimizar_extractos.py"
    spec = importlib.util.spec_from_file_location("anonimizar_extractos_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_prints_only_counts_and_succeeds(extracts, capsys):
    input_dir, output_dir = extracts

    exit_code = _load_cli().main([str(input_dir), str(output_dir)])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "3" in captured
    usuarios = _read(output_dir / "usuarios.csv", ["iduser", "createdate"])
    for code in usuarios["iduser"]:
        assert code not in captured
    for original in ORIGINAL_USER_IDS:
        assert original not in captured.split()


def test_cli_refuses_same_directory_with_nonzero_exit(extracts, capsys):
    input_dir, _ = extracts

    exit_code = _load_cli().main([str(input_dir), str(input_dir)])

    assert exit_code != 0


def test_anonymized_extracts_feed_the_dataset_notebook_with_string_ids(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    (input_dir / "payments.csv").write_text(
        "".join(
            f"00123,2025-0{month}-01,100.0,2025-0{month + 1}-01,{month}\n" for month in range(1, 6)
        ),
        encoding="utf-8",
    )
    (input_dir / "suscripciones.csv").write_text("00123,0042\n", encoding="utf-8")
    (input_dir / "usuarios.csv").write_text("0042,2025-01-01\n", encoding="utf-8")
    anonymize_extracts(input_dir, output_dir)
    path = Path(__file__).resolve().parents[2] / "notebooks" / "03_construir_dataset_desde_csv.py"
    spec = importlib.util.spec_from_file_location("construir_dataset_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.DEFAULT_DATASHEET_DIR == "Datasheet_anonimizado"

    builder, usuarios = module.construir_builder(str(output_dir))
    dataset = module.construir_dataset(builder, usuarios)

    assert len(dataset) > 0
    assert dataset["affiliate_id"].nunique() == 1
    assert CODE_PATTERN.match(dataset["affiliate_id"].iloc[0])
    assert list(dataset.columns[:4]) == [
        "dias_desde_ultimo_pago",
        "frecuencia_pago_dias",
        "monto_pago_promedio",
        "antiguedad_dias",
    ]


def test_cli_defaults_to_datasheet_directories():
    cli = _load_cli()

    assert cli.DEFAULT_INPUT_DIR == "Datasheet"
    assert cli.DEFAULT_OUTPUT_DIR == "Datasheet_anonimizado"
