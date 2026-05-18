# -*- coding: utf-8 -*-
"""삼재 들·눌·날 판정."""

from __future__ import annotations

from saju import samjae as sj


def test_myo_birth_samjae_phases_haemomi() -> None:
    """해묘미(亥卯未) → 삼재 사오미(巳午未)."""
    assert sj.phase_for_target_zhi("卯", "巳") == "deul"
    assert sj.phase_for_target_zhi("卯", "午") == "nul"
    assert sj.phase_for_target_zhi("卯", "未") == "nal"
    assert sj.phase_for_target_zhi("卯", "申") == "none"
    assert sj.phase_for_target_zhi("亥", "午") == "nul"
    assert sj.phase_for_target_zhi("未", "午") == "nul"


def test_analyze_samjae_2026_nul_for_myo() -> None:
    r = sj.analyze_samjae("卯", target_year=2026)
    assert r["올해_삼재_코드"] == "nul"
    assert r["올해_삼재"] == "눌삼재"
    assert r["삼재_여부"] is True


def test_analyze_samjae_2025_deul_for_myo() -> None:
    r = sj.analyze_samjae("卯", target_year=2025)
    assert r["올해_삼재_코드"] == "deul"


def test_ino_sul_group_uses_sin_yu_sul() -> None:
    assert sj.phase_for_target_zhi("寅", "申") == "deul"
    assert sj.phase_for_target_zhi("午", "酉") == "nul"
