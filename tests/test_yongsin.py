# -*- coding: utf-8 -*-
"""STEP 7: 용신."""

from __future__ import annotations

from saju import ohaeng as oh
from saju import sewoon as sw
from saju import yongsin as ys


def test_step7_yongsin(sample_pillars, day_master: str, sample_birth) -> None:
    counts = oh.count_elements(sample_pillars, include_hidden=True)
    nearby = sw.sewoon_range(2026, before=2, after=2)
    rep = ys.suggest_useful_gods(
        counts,
        day_master,
        sample_pillars["month"]["zhi"],
        pillars=sample_pillars,
        sewoon_nearby=nearby,
        sewoon_center_year=2026,
    )
    assert rep["용신_오행"] in ("목", "화", "토", "금", "수")
    assert rep["일간_강약"] in ("신강", "신약", "중화")
    assert "출력_문장" in rep
    detail = rep.get("강약_상세") or {}
    assert detail.get("판단_요약")
    assert detail.get("현상_특징")
    sew = rep.get("세운_강약_해설") or []
    assert len(sew) == 5
    assert any(r.get("기준년") for r in sew)
    assert all(r.get("상세") for r in sew)
