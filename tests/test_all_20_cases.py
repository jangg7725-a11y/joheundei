# -*- coding: utf-8 -*-
"""10간 × 남녀 20사주 전수 검증."""

from __future__ import annotations

import json
from typing import Any, List

from saju import analysis as an


def _yongsin_user_blob(yong: dict) -> str:
    keys = (
        "신강약_스토리",
        "용신_의미",
        "용신_작용",
        "용신_생활",
        "희신_스토리",
        "기신_스토리",
        "피할것",
        "요약_한줄",
        "근거_스토리",
        "lifestyle",
        "직업추천",
        "강약_상세",
        "notes",
        "세운_힌트",
        "출력_문장",
    )
    return json.dumps({k: yong.get(k) for k in keys if k in yong}, ensure_ascii=False)


def scan_nulls(obj: Any, path: str = "") -> List[str]:
    issues: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            issues += scan_nulls(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            issues += scan_nulls(v, f"{path}[{i}]")
    elif obj is None:
        issues.append(f"None: {path}")
    return issues

# 일간 검증: saju_calc 기준 대표 양력·음력 생일 (scripts/find_dm_fast.py)
ALL_CASES = [
    ("solar", 1990, 3, 20, 14, 0, "male", "甲"),
    ("solar", 1990, 3, 20, 14, 0, "female", "甲"),
    ("solar", 1985, 6, 15, 8, 0, "male", "乙"),
    ("solar", 1985, 6, 15, 8, 0, "female", "乙"),
    ("solar", 1970, 1, 6, 10, 0, "male", "丙"),
    ("solar", 1970, 1, 6, 10, 0, "female", "丙"),
    ("solar", 1970, 1, 7, 10, 0, "male", "丁"),
    ("solar", 1970, 1, 7, 10, 0, "female", "丁"),
    ("lunar", 1966, 11, 4, 2, 5, "male", "戊"),
    ("lunar", 1966, 11, 4, 2, 5, "female", "戊"),
    ("solar", 1970, 1, 9, 10, 0, "male", "己"),
    ("solar", 1970, 1, 9, 10, 0, "female", "己"),
    ("solar", 1970, 1, 10, 10, 0, "male", "庚"),
    ("solar", 1970, 1, 10, 10, 0, "female", "庚"),
    ("solar", 1970, 1, 1, 10, 0, "male", "辛"),
    ("solar", 1970, 1, 1, 10, 0, "female", "辛"),
    ("solar", 1970, 1, 2, 10, 0, "male", "壬"),
    ("solar", 1970, 1, 2, 10, 0, "female", "壬"),
    ("solar", 1970, 1, 3, 10, 0, "male", "癸"),
    ("solar", 1970, 1, 3, 10, 0, "female", "癸"),
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


def test_all_20_cases() -> None:
    for cal, y, m, d, h, mi, gender, exp_dm in ALL_CASES:
        report = _build(cal, y, m, d, h, mi, gender)
        assert report["day_master"] == exp_dm, f"{exp_dm} {gender}: dm"

        story = report.get("원국_스토리텔링", {})
        assert story.get("사주_한줄_핵심", ""), f"{exp_dm} {gender}: core"

        per = story.get("성격_분석", {})
        assert len(per.get("장점_5", [])) == 5
        assert len(set(per.get("장점_5", []))) == 5
        assert len(per.get("단점_5", [])) == 5

        career = story.get("직업_적성", {})
        assert len(career.get("최적_직군_TOP5", [])) >= 3

        unt = story.get("unteim_서사", {})
        assert unt.get("일간_심리", "") or unt.get("일간_심리_카드")
        assert unt.get("힐링_메시지", "")

        yong = report.get("yongsin", {})
        assert yong.get("용신_오행", "")
        assert yong.get("신강약_스토리", "")
        assert yong.get("용신_작용", "")

        cats = report.get("분석_카테고리", {})
        for key in CAT_KEYS:
            assert key in cats, f"{exp_dm} {gender}: {key}"

        issues = [i for i in scan_nulls(report) if i.startswith("None")]
        critical = [
            i
            for i in issues
            if any(
                k in i
                for k in (
                    "사주_한줄_핵심",
                    "장점",
                    "단점",
                    "용신_작용",
                    "일간_심리",
                )
            )
        ]
        assert not critical, f"{exp_dm} {gender}: {critical[:5]}"


def test_gender_diff_all_10() -> None:
    pairs = [
        (ALL_CASES[i], ALL_CASES[i + 1]) for i in range(0, len(ALL_CASES), 2)
    ]
    for (cal, y, m, d, h, mi, g1, dm), (_, _, _, _, _, _, g2, _) in pairs:
        male = _build(cal, y, m, d, h, mi, g1)
        female = _build(cal, y, m, d, h, mi, g2)
        m_core = male["원국_스토리텔링"]["사주_한줄_핵심"]
        f_core = female["원국_스토리텔링"]["사주_한줄_핵심"]
        assert m_core != f_core, f"{dm}: gender same core"
        assert "남편" not in m_core
        assert "아내" not in f_core


def test_yongsin_all_20() -> None:
    blob_parts = []
    for cal, y, m, d, h, mi, gender, exp_dm in ALL_CASES:
        report = _build(cal, y, m, d, h, mi, gender)
        yong = report.get("yongsin", {})
        assert yong.get("신강약_스토리", "")
        assert yong.get("용신_작용", "")
        assert yong.get("용신_생활", "")
        assert yong.get("기신_스토리", "")
        ls = yong.get("lifestyle") or {}
        assert ls.get("색상_좋음", "")
        assert ls.get("방위", "")
        assert len((yong.get("직업추천") or {}).get("추천_직군") or []) >= 2
        blob_parts.append(_yongsin_user_blob(yong))
    blob = "\n".join(blob_parts)
    assert "55.6%" not in blob
    assert "한신 閑神" not in blob
    assert "구신 仇神" not in blob


def test_wolwoon_all_20() -> None:
    for cal, y, m, d, h, mi, gender, exp_dm in ALL_CASES:
        report = _build(cal, y, m, d, h, mi, gender)
        months = (report.get("월운표") or {}).get("월별") or []
        assert len(months) == 12, f"{exp_dm}: count"
        stories = [str(x.get("월별_핵심스토리") or "") for x in months]
        assert all(stories), f"{exp_dm}: empty month"
        assert len(set(stories)) >= 6, f"{exp_dm}: diversity {len(set(stories))}"
        for w in months:
            tip = str(w.get("월별_실천팁") or "")
            core = str(w.get("월별_핵심스토리") or "")
            if tip and core:
                assert tip != core[: len(tip)], f"{exp_dm}: tip=core head"
