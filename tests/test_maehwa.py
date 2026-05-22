# -*- coding: utf-8 -*-
from saju.maehwa import build_reading, calc_basic_suri, calc_year_suri, meta


def test_calc_basic_suri():
    assert calc_basic_suri(8, 15) == 6  # 8+15+1=24 -> 6


def test_build_reading_structure():
    r = build_reading("lunar", 1985, 8, 15, hour=14, minute=0)
    assert "gua_flow" in r
    assert r["gua_flow"]["ben"]["name"]
    assert r["gua_flow"]["dong"]["index"] in range(1, 7)
    assert r["gua_flow"]["zhi"]["name"]
    assert r["suri"]["basic_num"] in range(1, 10)
    assert len(r["suri"]["year_table"]) >= 5
    assert r["manseryeok"]["status"] == "coming_soon"


def test_solar_calendar_conversion():
    r = build_reading("solar", 1990, 5, 15, hour=10)
    assert r["datetime"]["solar"]["year"] == 1990
    assert r["datetime"]["lunar"]["month"] >= 1


def test_meta():
    m = meta()
    assert "suri" in m["features"]
