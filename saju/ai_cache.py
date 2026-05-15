# -*- coding: utf-8 -*-
"""AI 해설 파일 캐시 (7일 TTL)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "ai_cache"
TTL_SECONDS = 7 * 24 * 3600


def chart_cache_key(saju_data: Dict[str, Any]) -> str:
    """년·월·일·시주 + 성별 기준 키."""
    pillars = saju_data.get("pillars") or {}
    parts = []
    for k in ("year", "month", "day", "hour"):
        p = pillars.get(k) or {}
        parts.append(str(p.get("pillar") or f"{p.get('gan','')}{p.get('zhi','')}"))
    gender = (saju_data.get("meta") or {}).get("gender_for_daewoon") or ""
    if not gender:
        gender = str(saju_data.get("gender") or "")
    raw = "|".join(parts) + "|" + gender
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _path(cache_key: str, tab: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_tab = "".join(c if c.isalnum() or c in "-_" else "_" for c in tab)
    return CACHE_DIR / f"{cache_key}_{safe_tab}.json"


def get_cached(cache_key: str, tab: str) -> Optional[Dict[str, Any]]:
    path = _path(cache_key, tab)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    saved = float(payload.get("saved_at") or 0)
    if time.time() - saved > TTL_SECONDS:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    return payload


def set_cached(cache_key: str, tab: str, body: Dict[str, Any]) -> None:
    path = _path(cache_key, tab)
    payload = {**body, "saved_at": time.time(), "cache_key": cache_key, "tab": tab}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")


def delete_cached(cache_key: str, tab: str) -> None:
    path = _path(cache_key, tab)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
