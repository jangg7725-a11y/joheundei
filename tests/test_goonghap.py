# -*- coding: utf-8 -*-
"""궁합 모듈 스모크 테스트."""

from __future__ import annotations

from saju import goonghap as gh
from saju import ohaeng as oh
from saju import saju_calc as sc
from saju import yongsin as ys


def _raw_dm_counts(calendar: str, y: int, m: int, d: int, hour: int, gender: str):
    birth = sc.BirthInput(
        calendar=calendar,
        year=y,
        month=m,
        day=d,
        hour=hour,
        minute=0,
        lunar_leap=False,
        gender=gender,
    )
    raw = sc.compute_saju(birth)
    counts = oh.count_elements(raw["pillars"], include_hidden=True)
    return raw, counts


def test_ilji_yukhap_and_cheon_gan_hap():
    raw_a, ca = _raw_dm_counts("solar", 1990, 1, 15, 12, "male")
    raw_b, cb = _raw_dm_counts("solar", 1991, 6, 20, 12, "female")
    dm_a = raw_a["day_master"]
    dm_b = raw_b["day_master"]
    z_a = raw_a["pillars"]["day"]["zhi"]
    z_b = raw_b["pillars"]["day"]["zhi"]

    ilji = gh.analyze_ilji_relations(z_a, z_b)
    assert "관계_표기" in ilji
    assert "커플_유형" in ilji

    ilgan = gh.analyze_ilgan_relation(dm_a, dm_b)
    assert ilgan["유형"] in ("비화", "생(A→B)", "생(B→A)", "극(A→B)", "극(B→A)", "기타")

    cheon = gh.analyze_cheon_gan_hap(dm_a, dm_b)
    assert "성립" in cheon

    ya = ys.suggest_useful_gods(ca, dm_a, raw_a["pillars"]["month"]["zhi"], pillars=raw_a["pillars"])
    yb = ys.suggest_useful_gods(cb, dm_b, raw_b["pillars"]["month"]["zhi"], pillars=raw_b["pillars"])
    pack = gh.analyze_goonghap_pair(
        raw_a=raw_a,
        raw_b=raw_b,
        counts_a=ca,
        counts_b=cb,
        yong_a=ya,
        yong_b=yb,
        label_a="甲",
        label_b="乙",
    )
    assert "종합_점수" in pack
    assert "하트_게이지_퍼센트" in pack["종합_점수"]
    assert "원국_나란히" in pack
    assert pack["원국_나란히"]["A"]["표시_이름"] == "甲"
