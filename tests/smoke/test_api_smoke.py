"""Optional black-box checks against an already-started local smoke API."""

import os
from urllib.request import urlopen

import pytest


BASE_URL = os.getenv("SMOKE_API_URL")


pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="set SMOKE_API_URL only when the isolated Docker smoke stack is running",
)


def _status(path: str) -> int:
    with urlopen(f"{BASE_URL.rstrip('/')}{path}", timeout=10) as response:
        return response.status


def test_health_is_available():
    assert _status("/health") == 200


def test_existing_score_is_available():
    assert _status("/api/v1/risk/910001") == 200


def test_missing_score_is_not_found():
    from urllib.error import HTTPError

    with pytest.raises(HTTPError) as error:
        _status("/api/v1/risk/919999")
    assert error.value.code == 404


def test_list_is_paginated():
    import json

    with urlopen(f"{BASE_URL.rstrip('/')}/api/v1/risk?limit=1&offset=0&order=desc", timeout=10) as response:
        payload = json.load(response)
    assert response.status == 200
    assert len(payload["items"]) == 1
    assert payload["total"] == 2
