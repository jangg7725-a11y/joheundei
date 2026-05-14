# -*- coding: utf-8 -*-

from __future__ import annotations

from saju import wolwoon as ww


def test_wolwoon_month_pillar_2026_slot1_is_gengyin() -> None:
    m = ww.month_pillar_for_slot(2026, 1)
    assert m["월주간지"] == "庚寅"
    assert m["월지"] == "寅"


def test_wolwoon_year_pack_twelve_months(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    pack = ww.wolwoon_year_pack(dm, pillars, 2026)
    assert len(pack["월별"]) == 12
    assert "출력_표텍스트" in pack
    assert "┌" in pack["출력_표텍스트"]
    assert "특별주의" in pack
    assert "연간_월운_요약" in pack
    flow = pack["연간_월운_요약"]
    assert len(flow["최고의달_TOP3"]) == 3
    assert len(flow["최악의달_TOP3"]) == 3
    assert "세운연간_참고" in pack
    m0 = pack["월별"][0]
    assert m0["길흉등급_5단계"] in ("대길", "길", "평", "흉", "대흉")
    assert 1 <= int(m0["길흉점수"]) <= 5
    assert "월별_핵심스토리" in m0 and m0["월별_핵심스토리"]
    assert "월별_행동지침" in m0
    assert "건강_월별" in m0
    assert "재물_타이밍" in m0
    assert "세운_월운_중첩" in m0


def test_slot_period_requires_supported_year() -> None:
    try:
        ww.slot_period_label(1899, 1)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "범위" in str(e)
