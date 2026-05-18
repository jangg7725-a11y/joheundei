# -*- coding: utf-8 -*-
"""생시 미상(모름) 입력."""

from __future__ import annotations

from saju import analysis as an


def test_hour_unknown_sets_meta_and_keeps_three_pillars_reliable() -> None:
    known = an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
        hour_unknown=False,
    )
    unknown = an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
        hour_unknown=True,
    )
    assert unknown["meta"].get("hour_unknown") is True
    assert unknown["meta"].get("birth_time_note")
    assert not known["meta"].get("hour_unknown")
    assert known["day_master"] == unknown["day_master"]
    assert known["pillars"]["year"]["pillar"] == unknown["pillars"]["year"]["pillar"]
    assert known["pillars"]["month"]["pillar"] == unknown["pillars"]["month"]["pillar"]
    assert known["pillars"]["day"]["pillar"] == unknown["pillars"]["day"]["pillar"]
