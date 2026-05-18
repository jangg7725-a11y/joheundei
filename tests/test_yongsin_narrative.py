# -*- coding: utf-8 -*-
"""용신 스토리·탭 데이터 검증."""

from __future__ import annotations

from saju import analysis as an

CASES_5 = [
    ("lunar", 1966, 11, 4, 2, 5, "female", "戊", "火"),
    ("solar", 1990, 3, 20, 14, 0, "male", "甲", "水"),
    ("solar", 1985, 7, 15, 8, 0, "female", "丙", "土"),
    ("solar", 2000, 12, 1, 22, 0, "male", "壬", "木"),
    ("solar", 1975, 9, 9, 6, 0, "female", "庚", "火"),
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


def test_yongsin_story_fields_five_charts() -> None:
    for cal, y, m, d, h, mi, gender, _dm, _yong_hint in CASES_5:
        r = _build(cal, y, m, d, h, mi, gender)
        yong = r.get("yongsin") or {}
        assert yong.get("신강약_스토리"), f"{gender} missing strength story"
        assert yong.get("용신_작용"), f"{gender} missing yong action"
        assert yong.get("용신_생활"), f"{gender} missing yong life"
        assert yong.get("기신_스토리"), f"{gender} missing gi story"
        ls = yong.get("lifestyle") or {}
        assert ls.get("색상_좋음"), f"{gender} missing color"
        assert ls.get("방위"), f"{gender} missing direction"
        career = yong.get("직업추천") or {}
        assert len(career.get("추천_직군") or []) >= 2
        assert career.get("추천_직군")[0].get("이유")


def _yongsin_user_blob(yong: dict) -> str:
    """탭·API에 노출되는 용신 필드만 검사."""
    import json

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


def test_yongsin_no_internal_labels_in_report() -> None:
    r = _build("lunar", 1966, 11, 4, 2, 5, "female")
    blob = _yongsin_user_blob(r.get("yongsin") or {})
    assert "55.6%" not in blob
    assert "한신 閑神" not in blob
    assert "구신 仇神" not in blob
    assert "비겁·인성 계열" not in blob
    assert " vs " not in blob


def test_yongsin_lifestyle_differs_by_element() -> None:
    r_fire = _build("lunar", 1966, 11, 4, 2, 5, "female")
    r_water = _build("solar", 1990, 3, 20, 14, 0, "male")
    c1 = (r_fire["yongsin"].get("lifestyle") or {}).get("색상_좋음", "")
    c2 = (r_water["yongsin"].get("lifestyle") or {}).get("색상_좋음", "")
    assert c1 and c2
    assert c1 != c2
