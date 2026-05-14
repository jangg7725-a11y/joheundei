# -*- coding: utf-8 -*-
"""STEP 2–4: ganji · 원국 · 십신 스모크 테스트."""

from __future__ import annotations

from saju import ganji as gj
from saju import saju_calc as sc
from saju import sipsin as sp


def test_step2_ganji_stems_branches() -> None:
    assert len(gj.STEMS) == 10
    assert len(gj.BRANCHES) == 12
    assert gj.JIA_ZI[0] == "甲子"
    assert gj.element_of_stem("甲") == "목"
    assert gj.element_of_branch("子") == "수"


def test_step3_compute_saju_structure(sample_birth: sc.BirthInput) -> None:
    raw = sc.compute_saju(sample_birth)
    assert raw["day_master"]
    assert raw["eight_char_string"]
    for k in ("year", "month", "day", "hour"):
        p = raw["pillars"][k]
        assert p["gan"] and p["zhi"]
        assert p["pillar"] == p["gan"] + p["zhi"]
    assert raw["_eight_char"] is not None


def test_step4_sipsin_classify(sample_pillars, day_master: str) -> None:
    target_gan = None
    for key in ("month", "year", "hour"):
        g = sample_pillars[key]["gan"]
        if g != day_master:
            target_gan = g
            break
    assert target_gan is not None
    name = sp.classify_sipsin(day_master, target_gan)
    assert name in (
        "비견",
        "겁재",
        "식신",
        "상관",
        "편재",
        "정재",
        "편관",
        "정관",
        "편인",
        "정인",
        "미상",
    )
