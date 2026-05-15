# -*- coding: utf-8 -*-
"""AI 해설 일일 생성 횟수 제한."""

from __future__ import annotations

import json
import os
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, Tuple

USAGE_DIR = Path(__file__).resolve().parent.parent / "data" / "ai_usage"
# 한 차트 전체(탭 6개) 1회 분석 ≈ 6회 생성. 엄격 모드: SAJU_AI_FREE_DAILY=1
FREE_DAILY_LIMIT = int(os.getenv("SAJU_AI_FREE_DAILY", "6"))


def _usage_path(cache_key: str) -> Path:
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    return USAGE_DIR / f"{cache_key}.json"


def _today() -> str:
    return date.today().isoformat()


def check_and_consume(cache_key: str, *, tier: str = "free", bypass_cache: bool = False) -> Tuple[bool, str]:
    """
  Returns (allowed, message).
  bypass_cache=True → 새 API 호출(재생성) 시도.
  premium / paid → 무제한.
    """
    tier_l = (tier or "free").strip().lower()
    if tier_l in ("premium", "paid", "pro", "unlimited"):
        return True, ""
    if os.getenv("SAJU_AI_PREMIUM", "").strip().lower() in ("1", "true", "yes"):
        return True, ""

    if not bypass_cache:
        return True, ""

    path = _usage_path(cache_key)
    today = _today()
    count = 0
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("date") == today:
                count = int(data.get("count") or 0)
        except (json.JSONDecodeError, OSError, TypeError):
            count = 0

    if count >= FREE_DAILY_LIMIT:
        return (
            False,
            f"무료 이용은 하루 {FREE_DAILY_LIMIT}회까지 새 해설 생성이 가능합니다. "
            "캐시된 해설은 7일간 다시 볼 수 있습니다.",
        )

    path.write_text(
        json.dumps({"date": today, "count": count + 1, "updated_at": time.time()}, ensure_ascii=False),
        encoding="utf-8",
    )
    return True, ""


def usage_status(cache_key: str, *, tier: str = "free") -> Dict[str, Any]:
    tier_l = (tier or "free").strip().lower()
    unlimited = tier_l in ("premium", "paid", "pro", "unlimited") or os.getenv(
        "SAJU_AI_PREMIUM", ""
    ).strip().lower() in ("1", "true", "yes")
    if unlimited:
        return {"tier": tier_l, "unlimited": True, "remaining_today": -1}

    path = _usage_path(cache_key)
    today = _today()
    count = 0
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("date") == today:
                count = int(data.get("count") or 0)
        except (json.JSONDecodeError, OSError, TypeError):
            count = 0
    remaining = max(0, FREE_DAILY_LIMIT - count)
    return {
        "tier": "free",
        "unlimited": False,
        "daily_limit": FREE_DAILY_LIMIT,
        "used_today": count,
        "remaining_today": remaining,
    }
