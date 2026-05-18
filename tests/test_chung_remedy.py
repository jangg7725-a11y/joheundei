# -*- coding: utf-8 -*-
"""합충파해 보완법 — 음력 1966-11-04 02:05 여성 검증."""

from __future__ import annotations

from datetime import datetime

from saju import analysis
from saju import chung_pa_hae as cph
from saju import sewoon as sw


def _verification_report():
    center = datetime.now().year
    sew = sw.yearly_pillar_for_solar_year(center)
    return analysis.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
        sewoon_center_year=center,
    ), sew["pillar"], center


def test_native_chung_hai_remedy(verification_pillars) -> None:
    rel = cph.analyze_relations_full(verification_pillars)
    chung = next((r for r in rel["원국_충"] if "子" in r["글자"] and "午" in r["글자"]), None)
    assert chung and chung.get("보완법"), "子午충 보완법 없음"
    assert "水(子)" in chung["보완법"] or "북쪽" in chung["보완법"]

    hai = next((r for r in rel["원국_해"] if "丑" in r["글자"] and "午" in r["글자"]), None)
    assert hai and hai.get("보완법"), "丑午해 보완법 없음"


def test_samhap_partial_remedy(verification_pillars) -> None:
    rel = cph.analyze_relations_full(verification_pillars)
    partial = next((r for r in rel["원국_합"] if r["관계"] == "삼합(두지)"), None)
    assert partial, "삼합(두지) 없음"
    assert partial.get("부족한_글자") == "辰"
    assert "辰" in partial.get("해석", "")
    assert partial.get("보완법")


def test_sewoon_fuyin_chung_hai_remedy(verification_pillars) -> None:
    center = datetime.now().year
    sew = sw.yearly_pillar_for_solar_year(center)
    rel = cph.analyze_relations_full(
        verification_pillars,
        sewoon_pillar=sew["pillar"],
        sewoon_year=center,
    )
    cp = cph.analyze_branch_relations(
        verification_pillars,
        sewoon_pillar=sew["pillar"],
        sewoon_year=center,
    )
    assert cp.get("세운_복음충")

    fuyin = [r for r in rel["복음"] if "복음" in str(r.get("관계", ""))]
    if fuyin:
        assert fuyin[0].get("보완법"), "복음 보완법 없음"
        assert "복음" in fuyin[0]["보완법"] or "실수" in fuyin[0]["보완법"]

    sew_chung = [r for r in rel["세운_대입"] if r.get("관계") == "세운충"]
    if sew_chung:
        assert sew_chung[0].get("보완법")

    sew_hai = [r for r in rel["세운_대입"] if r.get("관계") == "세운해"]
    if sew_hai:
        assert sew_hai[0].get("보완법")


def test_build_report_chung_pa_hae_has_remedy_fields() -> None:
    report, _, _ = _verification_report()
    cp = report["chung_pa_hae"]
    detail = cp.get("관계_상세_전체") or []
    assert detail
    chung_row = next(
        (r for r in detail if r.get("관계") == "충" and "子" in str(r.get("글자"))),
        None,
    )
    assert chung_row and chung_row.get("보완법")
    assert "세운_복음충" in cp
