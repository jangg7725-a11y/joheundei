# -*- coding: utf-8 -*-
"""manseryeok_fortune — 세운·월운 요약."""

import re

from saju import manseryeok_fortune as mf
from saju import manseryeok_profile as msp
from saju import tone as tn


def test_build_fortune_has_sewoon_and_twelve_months():
    p = msp.compute_manseryeok_profile(
        calendar="solar",
        year=1966,
        month=12,
        day=15,
        hour=2,
        minute=5,
        gender="female",
        user_name="테스트",
    )
    f = p.get("fortune") or {}
    assert f.get("center_year")
    se = f.get("sewoon") or {}
    assert se.get("pillar")
    assert se.get("grade") in ("길한 편", "보통", "조심")
    assert se.get("headline")
    assert len(se.get("story") or []) >= 2
    assert len(se.get("phases") or []) == 3
    assert (se.get("position") or {}).get("intro")
    months = (f.get("monthly") or {}).get("months") or []
    assert len(months) == 12
    assert (months[0].get("detail") or {}).get("story")


def test_plain_grade_mapping():
    assert mf._plain_grade("길운") == "길한 편"
    assert mf._plain_grade("흉운") == "조심"


def test_fortune_uses_unteim_and_differs_by_daymaster():
    p_a = msp.compute_manseryeok_profile(
        calendar="solar",
        year=1984,
        month=3,
        day=10,
        hour=9,
        minute=0,
        gender="male",
    )
    p_b = msp.compute_manseryeok_profile(
        calendar="solar",
        year=1978,
        month=11,
        day=22,
        hour=14,
        minute=30,
        gender="female",
    )
    fa = p_a.get("fortune") or {}
    fb = p_b.get("fortune") or {}
    assert fa.get("sewoon", {}).get("unteim_loaded") is True
    story_a = "\n".join(fa.get("sewoon", {}).get("story") or [])
    story_b = "\n".join(fb.get("sewoon", {}).get("story") or [])
    assert story_a and story_b
    assert story_a != story_b
    assert fa.get("monthly", {}).get("first_half") != fb.get("monthly", {}).get("first_half") or (
        fa.get("sewoon", {}).get("headline") != fb.get("sewoon", {}).get("headline")
    )


_PLAIN_ENDING_MARKERS = (
    "미친다",
    "단계다",
    "작동한다",
    "움직인다",
    "나온다",
    "연결된다",
    "올라온다",
    "상태다",
)


def test_manseryeok_voice_plain_to_honorific() -> None:
    assert "미칠 수 있습니다" in tn.manseryeok_voice("건강에 영향을 미친다.")
    assert "단계입니다" in tn.manseryeok_voice("에너지가 연결되는 단계.")
    assert "작동합니다" in tn.manseryeok_voice("기반이 작동한다.")


def test_fortune_story_avoids_plain_endings() -> None:
    p = msp.compute_manseryeok_profile(
        calendar="solar",
        year=1984,
        month=3,
        day=10,
        hour=9,
        minute=0,
        gender="male",
    )
    texts: list[str] = []
    se = p.get("fortune", {}).get("sewoon") or {}
    texts.extend(se.get("story") or [])
    texts.append(se.get("headline") or "")
    texts.append(se.get("closing") or "")
    blob = "\n".join(t for t in texts if t)
    for marker in _PLAIN_ENDING_MARKERS:
        assert marker not in blob, f"plain ending {marker!r} in fortune text"
    assert not re.search(r"연결되는 단계\.", blob)
    assert re.search(r"(습니다|입니다|세요|하시면)", blob)
