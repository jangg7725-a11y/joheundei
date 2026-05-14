# -*- coding: utf-8 -*-
"""STEP 9: 십이운성."""

from __future__ import annotations

from saju import sibiunsung as sb


def test_step9_sibiunsung_classic() -> None:
    assert sb.stage_for("甲", "亥") == "장생"
    assert sb.stage_for("乙", "午") == "장생"


def test_step9_pillar_twelve(day_master: str, sample_pillars) -> None:
    out = sb.pillar_twelve_stages(day_master, sample_pillars)
    for k in ("year", "month", "day", "hour"):
        assert out[k]["stage"]
        assert out[k]["meaning"]
