# End-to-end evidence over the isolated Compose stack

The E2E test checks the real path `PostgreSQL record -> API container -> HTTP response`
with the synthetic 3-row fixture. It uses no mocks and no data from the source database.
The API is read-only (CU-01 consult one score, CU-02 list scores), so the test also checks
that the table is unchanged after the calls.

## Run it

```powershell
$env:SMOKE_COMPOSE_PROJECT = "tesis_xgboost_churn_e2e"        # isolated project name
$env:SMOKE_DB_PASSWORD = [guid]::NewGuid().ToString("N")      # random local value, never committed
docker compose -f docker-compose.smoke.yml up -d --build
docker compose -f docker-compose.smoke.yml exec -T api alembic upgrade head
docker compose -f docker-compose.smoke.yml exec -T api python scripts/smoke_test.py --check-config --seed

$env:E2E_API_URL = "http://127.0.0.1:18080"                   # API published on localhost only
.venv\Scripts\python.exe -m pytest tests/e2e -v

docker compose -f docker-compose.smoke.yml down -v            # stop and remove stack and volume
```

- Without `E2E_API_URL` (or `SMOKE_API_URL`) the E2E tests are skipped.
- PostgreSQL has no published port. The test reads it with
  `docker compose exec -T db psql` against `churn_results_smoke` only.
- The API port is bound to `127.0.0.1:18080`.

## What each test proves

| Test | Criterion |
|---|---|
| `test_database_is_the_isolated_synthetic_fixture` | Isolated database and 3-row fixture |
| `test_cu01_http_payload_equals_latest_database_record` (x2) | CU-01 / HU-01 / RF-01 happy path: payload keys, types and values equal the latest DB record |
| `test_cu01_missing_affiliate_returns_404_with_detail` | HU-01 alternate flow |
| `test_cu01_non_integer_identifier_returns_422` | HU-01 error flow |
| `test_cu02_default_list_*`, `*_order_*`, `*_limit_and_offset_*` | CU-02 / HU-02 / RF-03: total, limit, offset, order |
| `test_cu02_invalid_query_parameters_return_422` (x5) | HU-02 error flow |
| `test_api_calls_do_not_write_to_the_database` | Read-only API: count and row identity unchanged |

Offline alternate/error/regression tests live in `tests/api/test_risk_acceptance.py`; each test
name and docstring cites the HU-01/HU-02 acceptance criterion it verifies.

## Not covered

Authentication, SHAP, score insertion (RF-02) and recalculation (RF-04) are not implemented and
therefore not tested. The suite does not use the source database or any real extract.
