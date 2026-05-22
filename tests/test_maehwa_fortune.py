# -*- coding: utf-8 -*-
"""매화역수 일별·월별 운세."""

from __future__ import annotations

from datetime import date

from saju.maehwa import (
    _mod9,
    build_fortune_pack,
    build_reading,
    calc_day_suri,
    calc_month_suri,
)


def test_month_day_suri_layered():
    basic = 8
    birth_ly = 1966
    ms = calc_month_suri(basic, birth_ly, 2026, 5)
    ds = calc_day_suri(basic, birth_ly, 2026, 5, 19)
    assert 1 <= ms <= 9
    assert 1 <= ds <= 9
    assert ds == _mod9(ms + 19)


def test_build_reading_includes_fortune():
    r = build_reading("lunar", 1985, 8, 15, hour=14, user_name="테스트")
    assert "fortune" in r
    assert r["fortune"]["daily"]["day_suri"]["num"] in range(1, 10)
    assert r["fortune"]["monthly"]["month_suri"]["num"] in range(1, 10)
    assert len(r["fortune"]["monthly"]["calendar_days"]) >= 28


def test_daily_fortune_has_gua_and_narrative():
    pack = build_fortune_pack("lunar", 1985, 8, 15, 14, 0, "male", False, "홍길동")
    d = pack["daily"]
    assert d["gua_flow"]["ben"]["name"]
    assert d["narrative"]["body"]
    assert "홍길동" in d["narrative"]["body"]


def test_month_calendar_today_flag():
    t = date.today()
    pack = build_fortune_pack(
        "solar", 1990, 3, 20, 14, 0, "female", False, "",
        query_year=t.year,
        query_month=t.month,
    )
    today_cells = [c for c in pack["monthly"]["calendar_days"] if c["is_today"]]
    assert len(today_cells) == 1
    assert today_cells[0]["solar_day"] == t.day
