# -*- coding: utf-8 -*-
"""10간 대표 사주 — build_report 전수 검증."""

from __future__ import annotations

from saju import analysis as an

TEST_CASES = [
    ("solar", 1990, 3, 20, 14, 0, "male"),
    ("solar", 1985, 6, 15, 8, 0, "female"),
    ("solar", 1988, 8, 10, 12, 0, "male"),
    ("solar", 1992, 11, 5, 18, 0, "female"),
    ("lunar", 1966, 11, 4, 2, 5, "female"),
    ("solar", 1975, 9, 9, 6, 0, "male"),
    ("solar", 1980, 12, 1, 22, 0, "female"),
    ("solar", 1983, 4, 20, 4, 0, "male"),
    ("solar", 1972, 7, 7, 10, 0, "female"),
    ("solar", 1969, 2, 14, 16, 0, "male"),
]

CAT_KEYS = [
    "1_연애_궁합",
    "2_직업_사회운",
    "3_재물운",
    "4_건강",
    "5_사고_관재",
    "6_횡재운",
    "7_손재운",
    "8_상복_우환",
    "9_이별_별리",
    "10_전체_운세_흐름",
]


def _build(cal, y, m, d, h, mi, gender):
    return an.build_report(
        calendar=cal,
        year=y,
        month=m,
        day=d,
        hour=h,
        minute=mi,
        gender=gender,
        lunar_leap=False,
    )


def test_all_daymasters_report_structure() -> None:
    for case in TEST_CASES:
        cal, y, m, d, h, mi, gender = case
        r = _build(cal, y, m, d, h, mi, gender)
        story = r["원국_스토리텔링"]
        assert story["사주_한줄_핵심"].strip()
        per = story["성격_분석"]
        assert len(per["장점_5"]) == 5
        assert len(set(per["장점_5"])) == 5
        assert len(per["단점_5"]) == 5
        assert len(set(per["단점_5"])) == 5
        career = story["직업_적성"]
        assert len(career["최적_직군_TOP5"]) >= 5
        assert story["재물_패턴"]["버는_방식"].strip()
        vuln = story["건강_평생"]["선천_취약_축"]
        if isinstance(vuln, list):
            assert vuln and str(vuln[0]).strip()
        else:
            assert str(vuln).strip()
        unt = story["unteim_서사"]
        assert unt.get("일간_심리", "").strip() or unt.get("일간_심리_카드")
        assert unt.get("힐링_메시지", "").strip() or unt.get("힐링_메시지")
        cats = r["분석_카테고리"]
        for key in CAT_KEYS:
            assert key in cats, f"missing category {key} for {case}"
