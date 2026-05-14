# -*- coding: utf-8 -*-
"""STEP 8: 신살."""

from __future__ import annotations

from saju import sinsal as sn


def test_step8_sinsal(day_master: str, sample_pillars, sample_birth) -> None:
    gender = sample_birth.gender if sample_birth.gender else "male"
    out = sn.analyze_sinsal(day_master, sample_pillars, gender=gender)
    assert "신살_목록" in out
    assert isinstance(out["신살_목록"], list)
    if out["신살_목록"]:
        row = out["신살_목록"][0]
        assert row["신살"]
        assert row["길흉"] in ("길", "흉")
