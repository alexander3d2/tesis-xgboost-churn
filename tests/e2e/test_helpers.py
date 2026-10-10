"""Offline checks for the E2E helpers (no stack required)."""

from tests.e2e.helpers import (
    COMPOSE_FILE,
    DB_USER,
    EXPECTED_DATABASE,
    ITEM_FIELDS,
    expected_item,
    psql_command,
)


def test_psql_command_targets_only_the_isolated_db_service():
    command = psql_command("SELECT 1")

    assert command[:5] == ["docker", "compose", "-f", COMPOSE_FILE, "exec"]
    assert command[command.index("-d") + 1] == EXPECTED_DATABASE
    assert command[command.index("-U") + 1] == DB_USER
    assert "db" in command
    assert command[-2:] == ["-c", "SELECT 1"]


def test_expected_item_keeps_only_the_api_contract_fields():
    record = {field: field for field in ITEM_FIELDS} | {"id": 7, "ctid": "(0,1)"}

    assert list(expected_item(record)) == list(ITEM_FIELDS)
