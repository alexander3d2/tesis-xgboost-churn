import hashlib
import hmac
import re
import secrets
import shutil
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PAYMENTS_FILE = "payments.csv"
SUSCRIPCIONES_FILE = "suscripciones.csv"
USUARIOS_FILE = "usuarios.csv"
EXTRACT_FILES = (PAYMENTS_FILE, SUSCRIPCIONES_FILE, USUARIOS_FILE)
CODE_PATTERN = re.compile(r"^U[0-9A-F]{12}$")
CODE_HEX_LENGTH = 12


class AnonymizationError(Exception):
    pass


@dataclass(frozen=True)
class AnonymizationReport:
    users: int
    suscripciones_rows: int
    usuarios_rows: int
    payments_rows: int


def build_user_code(key: bytes, iduser: str) -> str:
    digest = hmac.new(key, str(iduser).encode(), hashlib.sha256).hexdigest()
    return "U" + digest[:CODE_HEX_LENGTH].upper()


def anonymize_extracts(input_dir: Path, output_dir: Path) -> AnonymizationReport:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    _validate_directories(input_dir, output_dir)

    suscripciones = _read_two_column_extract(input_dir / SUSCRIPCIONES_FILE, ["idsuscription", "iduser"])
    usuarios = _read_two_column_extract(input_dir / USUARIOS_FILE, ["iduser", "createdate"])

    original_ids = pd.unique(pd.concat([suscripciones["iduser"], usuarios["iduser"]]))
    codes_by_id = _build_codes(original_ids)

    suscripciones["iduser"] = suscripciones["iduser"].map(codes_by_id)
    usuarios["iduser"] = usuarios["iduser"].map(codes_by_id)
    _verify_postconditions(original_ids, suscripciones["iduser"], usuarios["iduser"])

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(input_dir / PAYMENTS_FILE, output_dir / PAYMENTS_FILE)
    _write_extract(suscripciones, output_dir / SUSCRIPCIONES_FILE)
    _write_extract(usuarios, output_dir / USUARIOS_FILE)

    return AnonymizationReport(
        users=len(original_ids),
        suscripciones_rows=len(suscripciones),
        usuarios_rows=len(usuarios),
        payments_rows=_count_rows(input_dir / PAYMENTS_FILE),
    )


def _validate_directories(input_dir: Path, output_dir: Path) -> None:
    if input_dir.resolve() == output_dir.resolve():
        raise AnonymizationError("output directory must differ from input directory")
    for name in EXTRACT_FILES:
        if not (input_dir / name).is_file():
            raise AnonymizationError(f"missing input file: {name}")


def _read_two_column_extract(path: Path, names: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    if frame.shape[1] != len(names):
        raise AnonymizationError(f"{path.name} must have exactly {len(names)} columns")
    frame.columns = names
    return frame


def _build_codes(original_ids) -> dict[str, str]:
    key = secrets.token_bytes(32)
    codes_by_id = {}
    originals_by_code = {}
    for iduser in original_ids:
        code = build_user_code(key, iduser)
        if code in originals_by_code:
            raise AnonymizationError("code collision between distinct users")
        originals_by_code[code] = iduser
        codes_by_id[iduser] = code
    return codes_by_id


def _verify_postconditions(original_ids, suscripciones_codes: pd.Series, usuarios_codes: pd.Series) -> None:
    output_codes = set(suscripciones_codes) | set(usuarios_codes)
    if not all(CODE_PATTERN.match(code) for code in output_codes):
        raise AnonymizationError("output iduser does not match the expected code format")
    if len(output_codes) != len(original_ids):
        raise AnonymizationError("unique output codes differ from unique original ids")
    if output_codes & set(original_ids):
        raise AnonymizationError("an output iduser equals an original iduser")


def _write_extract(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, header=False, index=False, encoding="utf-8", lineterminator="\n")


def _count_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())
