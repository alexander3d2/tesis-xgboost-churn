"""Helpers for the end-to-end test over the isolated Docker Compose smoke stack.

The database is read through `docker compose exec db psql`, so PostgreSQL never
needs a published port. The HTTP side uses the API port that the stack publishes
on 127.0.0.1 only.
"""

import json
import os
import subprocess
from pathlib import Path

import httpx

API_URL = (os.getenv("E2E_API_URL") or os.getenv("SMOKE_API_URL") or "").rstrip("/")

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = "docker-compose.smoke.yml"

EXPECTED_DATABASE = "churn_results_smoke"
DB_USER = "smoke_user"

ITEM_FIELDS = ("affiliate_id", "risk_score", "risk_level", "model_version", "scored_at")

# Latest record per affiliate in the synthetic fixture seeded by scripts/smoke_test.py --seed.
EXPECTED_LATEST = {
    910001: {
        "affiliate_id": 910001,
        "risk_score": 0.91,
        "risk_level": "Alto",
        "model_version": "smoke-v1",
        "scored_at": "2026-01-02T00:00:00",
    },
    910002: {
        "affiliate_id": 910002,
        "risk_score": 0.18,
        "risk_level": "Bajo",
        "model_version": "smoke-v1",
        "scored_at": "2026-01-03T00:00:00",
    },
}


def expected_item(record: dict) -> dict:
    """Shape of one API item derived from a database record."""
    return {field: record[field] for field in ITEM_FIELDS}


def psql_command(sql: str) -> list[str]:
    """Build the command that runs read-only SQL inside the isolated db container."""
    return [
        "docker", "compose", "-f", COMPOSE_FILE,
        "exec", "-T", "db",
        "psql", "-X", "-A", "-t",
        "-U", DB_USER, "-d", EXPECTED_DATABASE,
        "-v", "ON_ERROR_STOP=1",
        "-c", sql,
    ]


class ResultsDb:
    """Direct read access to the isolated results database (never through the API)."""

    def _query(self, sql: str):
        completed = subprocess.run(
            psql_command(sql),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=True,
        )
        return json.loads(completed.stdout.strip())

    def current_database(self) -> str:
        return self._query("SELECT to_json(current_database())")

    def count(self) -> int:
        return self._query("SELECT to_json(count(*)) FROM score_riesgo")

    def latest_by_affiliate(self) -> dict[int, dict]:
        rows = self._query(
            """
            SELECT COALESCE(json_agg(t), '[]'::json) FROM (
                SELECT DISTINCT ON (affiliate_id)
                    affiliate_id, risk_score, risk_level, model_version, scored_at
                FROM score_riesgo
                ORDER BY affiliate_id, scored_at DESC
            ) t
            """
        )
        return {row["affiliate_id"]: row for row in rows}

    def snapshot(self) -> list[dict]:
        """Whole table content plus physical row identity (ctid, xmin) to detect any write."""
        return self._query(
            """
            SELECT COALESCE(json_agg(t ORDER BY t.id), '[]'::json) FROM (
                SELECT ctid::text AS ctid, xmin::text AS xmin, * FROM score_riesgo
            ) t
            """
        )


class ApiClient(httpx.Client):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url=base_url, timeout=10)
