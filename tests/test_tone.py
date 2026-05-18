# -*- coding: utf-8 -*-
"""명리 참고 해설 톤 레이어 (법적 안전 표현)."""

from __future__ import annotations

from saju import analysis as an
from saju import tone as tn
from saju import narrative_loader as nl


def test_no_risky_career_claims() -> None:
    raw = "제가 30년 넘게 사주를 보아온 상담 관점에서 정리했습니다. 30년차 명리박사입니다."
    out = tn.voice_text(raw)
    assert "30년" not in out
    assert "박사" not in out or "참고" in out


def test_voice_text_consultative() -> None:
    raw = "당신은 묵직하게 쌓아두다 터뜨리는 패턴입니다. 주의하세요."
    out = tn.voice_text(raw)
    assert "회원님" in out or "말씀" in out or "유의" in out
    assert "주의하세요" not in out


def test_apply_voice_to_report_story() -> None:
    r = an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
    )
    story = r["원국_스토리텔링"]
    core = story.get("사주_한줄_핵심") or ""
    assert core
    assert "당신은" not in core or "회원님" in core or "말씀" in core or "사주" in core


def test_pick_from_pool_uses_voice() -> None:
    import random

    rng = random.Random(42)
    out = nl.pick_from_pool("주의하세요. 검토하세요.", rng)
    assert "주의하세요" not in out
