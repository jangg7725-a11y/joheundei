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


_BANNED_OPENERS = (
    "명리적으로 말씀드리면,",
    "전통 명리를 바탕으로 보면,",
    "이 사주에서는 흔히,",
    "풀어서 말씀드리면,",
)


def _collect_strings(obj, out: list) -> None:
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_strings(v, out)


def _assert_no_banned_openers(texts: list[str], label: str) -> None:
    for txt in texts:
        if len(txt) < 8:
            continue
        for b in _BANNED_OPENERS:
            assert b not in txt, f"{label}: contains banned opener {b!r} in {txt[:60]!r}..."


def test_report_no_voice_openers_global() -> None:
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
    texts: list = []
    _collect_strings(r.get("원국_스토리텔링") or {}, texts)
    _collect_strings(r.get("월운표") or {}, texts)
    _collect_strings(r.get("unteim_세운월운") or {}, texts)
    _assert_no_banned_openers(texts, "1966-female")


def test_strip_voice_openers() -> None:
    raw = "전통 명리를 바탕으로 보면, 입춘을 지난 인월입니다."
    assert tn.strip_voice_openers(raw).startswith("입춘")
    mid = "에너지가 낮다. 풀어서 말씀드리면, 쉬는 시간이 필요합니다."
    assert "풀어서 말씀드리면" not in tn.strip_voice_openers(mid)
