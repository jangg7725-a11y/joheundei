# -*- coding: utf-8 -*-
"""60갑자 공망 순(旬) 검증."""

from __future__ import annotations

from saju import analysis as an
from saju import saju_calc as sc
from saju.sinsal import _xunkong_for_pillar


def test_kongmang_xunkong_table() -> None:
    """甲子순~甲寅순 공망 지지 쌍."""
    expected_cycles = [
        ("甲子", ("戌", "亥")),
        ("甲戌", ("申", "酉")),
        ("甲申", ("午", "未")),
        ("甲午", ("辰", "巳")),
        ("甲辰", ("寅", "卯")),
        ("甲寅", ("子", "丑")),
    ]
    for pillar, pair in expected_cycles:
        assert _xunkong_for_pillar(pillar) == pair


def test_kongmang_in_report_matches_day_pillar() -> None:
    """대표 생일 — report sinsal 공망 == 일주 순공."""
    cases = [
        ("solar", 1990, 3, 20, 14, 0, "male"),
        ("solar", 1985, 6, 15, 8, 0, "female"),
        ("lunar", 1966, 11, 4, 2, 5, "female"),
    ]
    for cal, y, m, d, h, mi, g in cases:
        r = an.build_report(
            calendar=cal,
            year=y,
            month=m,
            day=d,
            hour=h,
            minute=mi,
            gender=g,
            lunar_leap=False,
        )
        day_p = r["pillars"]["day"]["pillar"]
        exp = list(_xunkong_for_pillar(day_p))
        actual = r["sinsal"].get("공망") or []
        assert set(actual) == set(exp), f"{y}-{m}-{d}: {actual} != {exp}"
