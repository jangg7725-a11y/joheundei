# -*- coding: utf-8 -*-
"""운테임 narrative/data JSON 로더 — 좋은데이 saju 패키지 내 정적 DB."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA_ROOT = Path(__file__).resolve().parent / "data"
_NARRATIVE_DIR = _DATA_ROOT / "unteim_narrative"
_UNTEIM_DATA_DIR = _DATA_ROOT / "unteim_data"


def narrative_dir() -> Path:
    return _NARRATIVE_DIR


def unteim_data_dir() -> Path:
    return _UNTEIM_DATA_DIR


def _resolve_path(file_name: str, *, subdir: str = "narrative") -> Path:
    name = file_name.strip()
    if not name.endswith(".json"):
        name = f"{name}.json"
    base = _NARRATIVE_DIR if subdir == "narrative" else _UNTEIM_DATA_DIR
    return base / name


@lru_cache(maxsize=64)
def load_narrative_db(file_name: str) -> Dict[str, Any]:
    """narrative/*.json 전체 dict 로드 (확장자 생략 가능)."""
    path = _resolve_path(file_name, subdir="narrative")
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=32)
def load_unteim_data(file_name: str) -> Any:
    """data/unteim_data/*.json 로드."""
    path = _resolve_path(file_name, subdir="data")
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def clear_narrative_cache() -> None:
    load_narrative_db.cache_clear()
    load_unteim_data.cache_clear()


def get_by_path(data: Any, path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def get_value(file_name: str, key: str, default: Any = None) -> Any:
    data = load_narrative_db(file_name)
    v = get_by_path(data, key, None)
    return default if v is None else v


def pick_from_pool(pool: Any, rng) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        choice = rng.choice(pool)
        return str(choice).strip() if choice is not None else ""
    return ""


def list_narrative_files() -> List[str]:
    if not _NARRATIVE_DIR.is_dir():
        return []
    return sorted(p.name for p in _NARRATIVE_DIR.glob("*.json"))


def list_unteim_data_files() -> List[str]:
    if not _UNTEIM_DATA_DIR.is_dir():
        return []
    return sorted(p.name for p in _UNTEIM_DATA_DIR.glob("*.json"))
