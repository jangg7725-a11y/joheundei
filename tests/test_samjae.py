# -*- coding: utf-8 -*-
"""삼재 들·눌·날 판정."""

from __future__ import annotations

from saju import samjae as sj


def test_myo_birth_samjae_phases() -> None:
    # 묘(卯) 띠 → 삼재 申酉戌
    assert sj.phase_for_target_zhi("卯", "申") == "deul"
    assert sj.phase_for_target_zhi("卯", "酉") == "nul"
    assert sj.phase_for_target_zhi("卯", "戌") == "nal"
    assert sj.phase_for_target_zhi("卯", "午") == "none"


def test_analyze_samjae_2028_deul_for_myo() -> None:
    r = sj.analyze_samjae("卯", target_year=2028)
    assert r["올해_삼재_코드"] == "deul"
    assert r["올해_삼재"] == "들삼재"
    assert r["삼재_여부"] is True


def test_analyze_samjae_2026_none_for_myo() -> None:
    r = sj.analyze_samjae("卯", target_year=2026)
    assert r["올해_삼재_코드"] == "none"
    assert r["삼재_여부"] is False
