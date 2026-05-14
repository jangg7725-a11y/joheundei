# -*- coding: utf-8 -*-
"""STEP 6: 대운·세운."""

from __future__ import annotations

from saju import daewoon as dw
from saju import sewoon as sw


def test_step6_daewoon(raw_saju) -> None:
    block = dw.compute_daewoon(raw_saju["_eight_char"], gender_male=True)
    assert "cycles" in block
    assert len(block["cycles"]) >= 1


def test_step6_sewoon_year_pillar() -> None:
    y = sw.yearly_pillar_for_solar_year(2026)
    assert y["pillar"]
    assert len(y["pillar"]) == 2
    rng = sw.sewoon_range(2026, before=1, after=1)
    assert len(rng) == 3


def test_step6_sewoon_forecast_pack(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    pack = sw.sewoon_forecast_pack(dm, pillars, gender="male", center_year=2026, span=10)
    assert pack["범위"]["총년수"] == 21
    assert len(pack["연도별"]) == 21
    y2026 = next(y for y in pack["연도별"] if y["연도"] == 2026)
    assert y2026["간지"]
    assert "출력_트리텍스트" in y2026
    assert "세운_대입_원본" in y2026


def test_step6_analyze_sewoon_year_structure(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    row = sw.analyze_sewoon_year(dm, pillars, gender="female", solar_year=2020)
    assert row["운세등급"] in ("길운", "흉운", "보통")
    assert 1 <= row["별점"] <= 5
    assert isinstance(row["사건예측"], dict)
