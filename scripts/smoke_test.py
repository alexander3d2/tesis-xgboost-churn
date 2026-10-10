"""Controlled smoke test for the local results-db Compose environment."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg


EXPECTED_DB_NAME = "churn_results_smoke"
EXPECTED_DB_HOSTS = {"db"}
FIXTURE = (
    (910001, 0.41, "Medio", "smoke-v1", datetime(2026, 1, 1, tzinfo=timezone.utc)),
    (910001, 0.91, "Alto", "smoke-v1", datetime(2026, 1, 2, tzinfo=timezone.utc)),
    (910002, 0.18, "Bajo", "smoke-v1", datetime(2026, 1, 3, tzinfo=timezone.utc)),
)


def _fail_closed() -> None:
    if os.getenv("SMOKE_TEST") != "1":
        raise RuntimeError("SMOKE_TEST=1 is required")
    host = os.getenv("RESULTS_DB_HOST", "")
    name = os.getenv("RESULTS_DB_NAME", "")
    if host not in EXPECTED_DB_HOSTS or name != EXPECTED_DB_NAME:
        raise RuntimeError(
            "refusing non-isolated results database configuration; "
            "RESULTS_DB_HOST must be db and RESULTS_DB_NAME must be churn_results_smoke"
        )


def _connection() -> psycopg.Connection:
    _fail_closed()
    return psycopg.connect(
        host=os.environ["RESULTS_DB_HOST"],
        port=os.environ["RESULTS_DB_PORT"],
        dbname=os.environ["RESULTS_DB_NAME"],
        user=os.environ["RESULTS_DB_USER"],
        password=os.environ["RESULTS_DB_PASSWORD"],
        sslmode=os.getenv("RESULTS_DB_SSLMODE", "disable"),
    )


def seed_fixture() -> int:
    with _connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE score_riesgo RESTART IDENTITY")
            cursor.executemany(
                """
                INSERT INTO score_riesgo
                    (affiliate_id, risk_score, risk_level, model_version, scored_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                FIXTURE,
            )
        connection.commit()
    return len(FIXTURE)


def _request(base_url: str, path: str, expected_status: int) -> tuple[int, dict, float]:
    started = time.perf_counter()
    try:
        with urlopen(Request(f"{base_url}{path}", method="GET"), timeout=10) as response:
            status = response.status
            payload = json.load(response)
    except HTTPError as error:
        status = error.code
        payload = json.loads(error.read().decode("utf-8"))
    elapsed_ms = (time.perf_counter() - started) * 1000
    if status != expected_status:
        raise AssertionError(f"expected HTTP {expected_status}, got {status}")
    return status, payload, elapsed_ms


def run_smoke() -> int:
    _fail_closed()
    base_url = os.getenv("SMOKE_API_URL", "http://api:8000").rstrip("/")
    checks = (
        ("health", "/health", 200),
        ("existing_score", "/api/v1/risk/910001", 200),
        ("missing_score", "/api/v1/risk/919999", 404),
        ("paginated_list", "/api/v1/risk?limit=1&offset=0&order=desc", 200),
    )
    failures = 0
    for name, path, expected_status in checks:
        try:
            status, payload, elapsed_ms = _request(base_url, path, expected_status)
            count = len(payload.get("items", [])) if name == "paginated_list" else 0
            if name == "paginated_list" and (count != 1 or payload.get("total") != 2):
                raise AssertionError("unexpected pagination counts")
            print(f"{name} status={status} count={count} timing_ms={elapsed_ms:.1f} result=PASS")
        except (AssertionError, URLError, TimeoutError, ValueError) as error:
            failures += 1
            print(f"{name} status=ERROR count=0 timing_ms=0.0 result=FAIL ({type(error).__name__})")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--seed", action="store_true")
    args = parser.parse_args()
    try:
        _fail_closed()
        if args.check_config:
            print("config status=SAFE count=0 timing_ms=0.0 result=PASS")
        if args.seed:
            print(f"seed status=READY count={seed_fixture()} timing_ms=0.0 result=PASS")
        if not args.check_config and not args.seed:
            return run_smoke()
        return 0
    except (RuntimeError, KeyError, psycopg.Error) as error:
        print(f"safety_check status=ERROR count=0 timing_ms=0.0 result=BLOCKED ({type(error).__name__})")
        return 2


if __name__ == "__main__":
    sys.exit(main())
