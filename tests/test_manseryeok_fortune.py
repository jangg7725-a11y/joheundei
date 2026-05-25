# -*- coding: utf-8 -*-
"""manseryeok_fortune — 세운·월운 요약."""

from saju import manseryeok_fortune as mf
from saju import manseryeok_profile as msp


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
