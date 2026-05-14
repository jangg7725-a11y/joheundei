# -*- coding: utf-8 -*-
"""STEP 5: 충·파·해·형·합."""

from __future__ import annotations

from saju import chung_pa_hae as cph


def test_step5_native_chong(sample_pillars) -> None:
    rows = cph.analyze_native_chong(sample_pillars)
    assert isinstance(rows, list)
    for r in rows:
        assert set(r.keys()) >= {"관계", "글자", "위치", "강도", "해석"}


def test_step5_relations_full(sample_pillars) -> None:
    full = cph.analyze_relations_full(sample_pillars)
    assert "원국_충" in full
    assert "관계_상세_전체" in full
    assert isinstance(full["관계_상세_전체"], list)
