# -*- coding: utf-8 -*-
"""STEP 10: 종합 분석."""

from __future__ import annotations

from saju import analysis as an


def test_step10_build_report(sample_birth) -> None:
    report = an.build_report(
        calendar="solar",
        year=sample_birth.year,
        month=sample_birth.month,
        day=sample_birth.day,
        hour=sample_birth.hour,
        minute=sample_birth.minute,
        gender=sample_birth.gender if sample_birth.gender else "male",
        lunar_leap=False,
        sewoon_center_year=2026,
        partner_day_pillar=None,
    )
    assert report["pillars"]
    assert report["분석_카테고리"]
    assert "1_연애_궁합" in report["분석_카테고리"]
    assert report["chung_pa_hae"]["관계_상세_전체"]
    y0 = report["세운_심층"]["연도별"][0]
    assert "정밀분석" in y0
    assert "충_강도" in y0["정밀분석"]
    m0 = report["월운표"]["월별"][0]
    assert "정밀분석" in m0
    assert "절기_전후_불안정" in m0["정밀분석"]
    assert isinstance(report["sewoon"], list) and len(report["sewoon"]) >= 1
    assert isinstance(report["wolwoon"], list) and len(report["wolwoon"]) == 12
    assert report["ilwoon"] == report["일운"]
    assert report["timeline"] == report["통합_타임라인"]
    assert "sewoon" in report["jeongmil"] and "wolwoon" in report["jeongmil"]
    story = report["원국_스토리텔링"]
    assert story["사주_한줄_핵심"]
    assert len(story["성격_분석"]["장점_5"]) == 5
    assert len(story["직업_적성"]["최적_직군_TOP5"]) == 5
    assert "유년기_15미만" in story["인생_전체_흐름"]
