from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"
NOW = dt.datetime(2024, 3, 14, 15, 9, 26)


@pytest.fixture
def now() -> dt.datetime:
    return NOW


@pytest.fixture
def image_path() -> Path:
    return DATA / "author.bmp"


@pytest.fixture
def records() -> list[dict]:
    return [
        {"msg": "My first Cell", "id": 1, "when": NOW},
        {"msg": "My second Cell", "id": 2, "when": NOW},
    ]


@pytest.fixture
def chdir_tmp(tmp_path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path
