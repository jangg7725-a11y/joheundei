# -*- coding: utf-8 -*-
"""STEP 7: 용신."""

from __future__ import annotations

from saju import ohaeng as oh
from saju import yongsin as ys


def test_step7_yongsin(sample_pillars, day_master: str, sample_birth) -> None:
    counts = oh.count_elements(sample_pillars, include_hidden=True)
    rep = ys.suggest_useful_gods(
        counts,
        day_master,
        sample_pillars["month"]["zhi"],
        pillars=sample_pillars,
    )
    assert rep["용신_오행"] in ("목", "화", "토", "금", "수")
    assert rep["일간_강약"] in ("신강", "신약", "중화")
    assert "출력_문장" in rep
