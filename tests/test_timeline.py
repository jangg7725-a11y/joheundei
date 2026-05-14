# -*- coding: utf-8 -*-

from __future__ import annotations

from saju import daewoon as dw
from saju import ohaeng as oh
from saju import timeline as tl
from saju import yongsin as ys


def test_timeline_visual_colors() -> None:
    rows = tl.timeline_visualization_years(1990, 2026, span_past=1, span_future=1)
    assert len(rows) == 3
    themes = {r["테마키"] for r in rows}
    assert "past_gray" in themes and "present_gold" in themes and "future_blue" in themes


def test_timeline_pack_light(raw_saju) -> None:
    dm = raw_saju["day_master"]
    pillars = raw_saju["pillars"]
    ec = raw_saju["_eight_char"]
    cycles = dw.compute_daewoon(ec, gender_male=True)["cycles"]
    counts = oh.count_elements(pillars, include_hidden=True)
    yong = ys.suggest_useful_gods(counts, dm, pillars["month"]["zhi"], pillars=pillars)

    pack = tl.build_timeline_pack(
        dm,
        pillars,
        gender="male",
        counts=counts,
        birth_year=1990,
        daewoon_cycles=cycles,
        yong_block=yong,
        current_year=2026,
        triple_scan_years=0,
        include_ilwoon_counts=False,
        age_events_until_year=2026,
    )

    assert pack["현재연도"] == 2026
    assert len(pack["향후5년"]["연도별"]) == 5
    assert pack["향후5년"]["연도별"][0]["위험도바_ASCII"]
    assert isinstance(pack["삼중분석"]["극위험_삼중충"], list)
