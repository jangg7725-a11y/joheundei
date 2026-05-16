# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date

from saju import analysis as an
from saju import ilwoon as il


def test_ilwoon_anchor_day_1900_jiaxu() -> None:
    p = il.daily_pillar_for_date(1900, 1, 1)
    assert p["간지"] == "甲戌"


def test_ilwoon_week_has_seven_days(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    w = il.ilwoon_week_pack(dm, pillars, reference_date=date(2026, 5, 14))
    assert len(w["일자별"]) == 7


def test_ilwoon_month_grid_and_special_lists(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    m = il.ilwoon_month_pack(dm, pillars, 2026, 5)
    assert len(m["달력"]) >= 4
    assert "특별길일" in m and "특별흉일" in m
    assert "천을귀인일" in m["특별길일"]
    assert any(cell.get("패딩") is False for row in m["달력"] for cell in row)


def test_ilwoon_snapshot(raw_saju) -> None:
    snap = il.ilwoon_snapshot_pack(raw_saju["day_master"], raw_saju["pillars"], reference_date=date(2026, 1, 15))
    assert "오늘" in snap and snap["오늘"]["간지"]
    t = snap["오늘"]
    assert "오늘_일진_상세" in t and t["오늘_일진_상세"]["오늘의_십신"]
    assert len(t.get("시간대별_운세") or []) == 12
    assert "오늘_추천행동" in t and t["오늘_추천행동"]["행운_방향"]
    w0 = snap["이번주"]["일자별"][0]
    assert w0["미리보기"]["이모지등급"] in ("💚", "🔴", "⚪")
    cell = next(c for row in snap["이번달"]["달력"] for c in row if not c.get("패딩"))
    assert "달력_표시" in cell


def test_wolwoon_period_sinsal_matches_month_flags() -> None:
    """월운 신살은 월운표 중첩플래그(공망·동시충·복음)와 맞아야 한다."""
    r = an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
    )
    wol = r["월운표"]
    for m in wol.get("월별") or []:
        flags = m.get("중첩플래그") or {}
        pack = m.get("월운_신살") or {}
        names = {row.get("신살") for row in pack.get("발동_목록") or []}
        if flags.get("공망달"):
            assert any("공망" in str(n) for n in names), f"slot {m.get('절월번호')} 공망"
        if flags.get("세운월운_동시충"):
            assert "세운·월운 동시충" in names, f"slot {m.get('절월번호')} dual chong"
        if flags.get("세운월운_복음"):
            assert "세운월운 복음" in names, f"slot {m.get('절월번호')} fuyin"
        chong_n = len((m.get("원국_충파해합형") or {}).get("충") or [])
        if chong_n and not names:
            assert False, f"slot {m.get('절월번호')} has chong but no sinsal"


def test_ilwoon_period_sinsal_matches_special_bad() -> None:
    """일운 신살은 ilwoon 일진 분석(백호 충·일지충·공망)과 동일 규칙으로 발동해야 한다."""
    r = an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
    )
    day_row = il.analyze_ilwoon_day(r["day_master"], r["pillars"], 2026, 5, 16)
    bad = day_row.get("특별흉") or {}
    pack = r["sinsal"].get("일운_신살") or {}
    names = {row.get("신살") for row in pack.get("발동_목록") or []}
    if bad.get("백호살"):
        assert "백호살" in names
    if bad.get("일지충"):
        assert "일지충" in names
    if bad.get("공망"):
        assert any("공망" in str(n) for n in names)


def test_ilwoon_month_cells_have_calendar_markers(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    m = il.ilwoon_month_pack(dm, pillars, 2026, 5)
    assert "달력_표시" in m["일별전체"][0]
