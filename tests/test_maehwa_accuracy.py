# -*- coding: utf-8 -*-
"""매화역수·수리 계산 정확도 — 남/여 다수 사주 수동 기대값 대조."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from saju.maehwa import (
    _flip_line,
    _hour_shi_index,
    _lines_to_gua,
    _mod6,
    _mod8,
    _mod9,
    _year_digit_sum,
    build_reading,
    calc_basic_suri,
    calc_year_suri,
    resolve_lunar_input,
)

_HEX64 = json.loads(
    (Path(__file__).resolve().parents[1] / "saju/data/maehwa/hex64.json").read_text(
        encoding="utf-8"
    )
)
_GL = {
    int(k): v
    for k, v in json.loads(
        (Path(__file__).resolve().parents[1] / "saju/data/maehwa/trigram_lines.json").read_text(
            encoding="utf-8"
        )
    ).items()
}


def _ref_gua(lunar_year: int, lunar_month: int, lunar_day: int, lunar_hour: int) -> dict:
    """maehwa.py와 동일한 괘·동효·변괘 산식 (음력 기준)."""
    yn = _year_digit_sum(lunar_year)
    hn = _hour_shi_index(lunar_hour)
    s3 = yn + lunar_month + lunar_day
    s4 = s3 + hn
    yong = _mod8(s3)
    che = _mod8(s4)
    dong = _mod6(s4)

    che_lines = list(_GL[che])
    yong_lines = list(_GL[yong])
    if dong <= 3:
        che_lines = _flip_line(che_lines, dong)
        changed_lower = _lines_to_gua(che_lines, _GL)
        changed_upper = yong
    else:
        yong_lines = _flip_line(yong_lines, dong)
        changed_lower = che
        changed_upper = _lines_to_gua(yong_lines, _GL)

    ben_key = f"{yong}-{che}"
    zhi_key = f"{changed_upper}-{changed_lower}"
    return {
        "yn": yn,
        "hn": hn,
        "s3": s3,
        "s4": s4,
        "yong": yong,
        "che": che,
        "dong": dong,
        "ben_key": ben_key,
        "ben_name": _HEX64[ben_key]["name"],
        "zhi_key": zhi_key,
        "zhi_name": _HEX64[zhi_key]["name"],
    }


# (calendar, y, m, d, h, mi, gender, leap, label, expected after lunar resolve)
# expected: lunar_ymd, suri_basic, gua fields — gender는 결과에 영향 없음
ACCURACY_CASES = [
    {
        "label": "양1990-03-20 14시 남",
        "input": ("solar", 1990, 3, 20, 14, 0, "male", False),
        "lunar": (1990, 2, 24, 14),
        "suri_basic": 9,
        "suri_name": "문서수(文書數)",
        "gua": {"ben_key": "5-5", "ben_name": "손위풍", "dong": 5, "zhi_key": "7-5", "zhi_name": "산풍고"},
    },
    {
        "label": "양1990-03-20 14시 여",
        "input": ("solar", 1990, 3, 20, 14, 0, "female", False),
        "lunar": (1990, 2, 24, 14),
        "suri_basic": 9,
        "suri_name": "문서수(文書數)",
        "gua": {"ben_key": "5-5", "ben_name": "손위풍", "dong": 5, "zhi_key": "7-5", "zhi_name": "산풍고"},
    },
    {
        "label": "양1985-06-15 08시 남",
        "input": ("solar", 1985, 6, 15, 8, 0, "male", False),
        "lunar": (1985, 4, 27, 8),
        "suri_basic": 5,
        "suri_name": "경파수(驚破數)",
        "gua": {"ben_key": "6-3", "ben_name": "수화기제", "dong": 5, "zhi_key": "8-3", "zhi_name": "지화명이"},
    },
    {
        "label": "양1985-07-15 08시 여",
        "input": ("solar", 1985, 7, 15, 8, 0, "female", False),
        "lunar": (1985, 5, 28, 8),
        "suri_basic": 7,
        "suri_name": "병퇴식수(病退食數)",
        "gua": {"ben_key": "8-5", "ben_name": "지풍승", "dong": 1, "zhi_key": "8-1", "zhi_name": "지천태"},
    },
    {
        "label": "양1970-01-06 10시 남",
        "input": ("solar", 1970, 1, 6, 10, 0, "male", False),
        "lunar": (1969, 11, 29, 10),
        "suri_basic": 5,
        "suri_name": "경파수(驚破數)",
        "gua": {"ben_key": "1-7", "ben_name": "천산둔", "dong": 5, "zhi_key": "3-7", "zhi_name": "화산려"},
    },
    {
        "label": "양1970-01-06 10시 여",
        "input": ("solar", 1970, 1, 6, 10, 0, "female", False),
        "lunar": (1969, 11, 29, 10),
        "suri_basic": 5,
        "suri_name": "경파수(驚破數)",
        "gua": {"ben_key": "1-7", "ben_name": "천산둔", "dong": 5, "zhi_key": "3-7", "zhi_name": "화산려"},
    },
    {
        "label": "음1966-11-04 02:05 여 (검증 사주)",
        "input": ("lunar", 1966, 11, 4, 2, 5, "female", False),
        "lunar": (1966, 11, 4, 2),
        "suri_basic": 7,
        "suri_name": "병퇴식수(病退食數)",
        "gua": {"ben_key": "5-7", "ben_name": "풍산점", "dong": 3, "zhi_key": "5-8", "zhi_name": "풍지관"},
    },
    {
        "label": "음1985-08-15 14시 남",
        "input": ("lunar", 1985, 8, 15, 14, 0, "male", False),
        "lunar": (1985, 8, 15, 14),
        "suri_basic": 6,
        "suri_name": "관수(官數)",
        "gua": {"ben_key": "6-6", "ben_name": "감위수", "dong": 6, "zhi_key": "5-6", "zhi_name": "풍수환"},
    },
    {
        "label": "음1985-08-15 14시 여",
        "input": ("lunar", 1985, 8, 15, 14, 0, "female", False),
        "lunar": (1985, 8, 15, 14),
        "suri_basic": 6,
        "suri_name": "관수(官數)",
        "gua": {"ben_key": "6-6", "ben_name": "감위수", "dong": 6, "zhi_key": "5-6", "zhi_name": "풍수환"},
    },
    {
        "label": "양2000-01-01 23시 자시 남",
        "input": ("solar", 2000, 1, 1, 23, 0, "male", False),
        "lunar": (1999, 11, 25, 23),
        "suri_basic": 1,
        "suri_name": "신생수(新生數)",
        "gua": {"ben_key": "8-1", "ben_name": "지천태", "dong": 5, "zhi_key": "6-1", "zhi_name": "수천수"},
    },
]


@pytest.mark.parametrize("case", ACCURACY_CASES, ids=[c["label"] for c in ACCURACY_CASES])
def test_maehwa_case_matches_reference(case: dict) -> None:
    cal, y, m, d, h, mi, gender, leap = case["input"]
    r = build_reading(cal, y, m, d, h, mi, gender=gender, lunar_leap=leap)

    ly, lm, ld, lh = case["lunar"]
    lunar = r["datetime"]["lunar"]
    assert (lunar["year"], lunar["month"], lunar["day"], lunar["hour"]) == (ly, lm, ld, lh)

    assert r["suri"]["basic_num"] == case["suri_basic"]
    assert r["suri"]["name"] == case["suri_name"]
    assert calc_basic_suri(lm, ld) == case["suri_basic"]

    ref = _ref_gua(ly, lm, ld, lh)
    exp = case["gua"]
    ben = r["gua_flow"]["ben"]
    zhi = r["gua_flow"]["zhi"]
    dong = r["gua_flow"]["dong"]

    assert ben["key"] == exp["ben_key"] == ref["ben_key"]
    assert ben["name"] == exp["ben_name"] == ref["ben_name"]
    assert zhi["key"] == exp["zhi_key"] == ref["zhi_key"]
    assert zhi["name"] == exp["zhi_name"] == ref["zhi_name"]
    assert dong["index"] == exp["dong"] == ref["dong"]
    assert ben["upper"]["num"] == ref["yong"]
    assert ben["lower"]["num"] == ref["che"]


def test_gender_does_not_change_gua_or_suri() -> None:
    """동일 생시 — 남/여는 괘·수리만 동일, gender 필드만 다름."""
    pairs = [
        (("solar", 1990, 3, 20, 14, 0), "male", "female"),
        (("lunar", 1985, 8, 15, 14, 0), "male", "female"),
        (("solar", 1970, 1, 6, 10, 0), "male", "female"),
    ]
    for birth, g1, g2 in pairs:
        cal, y, m, d, h, mi = birth
        r1 = build_reading(cal, y, m, d, h, mi, gender=g1)
        r2 = build_reading(cal, y, m, d, h, mi, gender=g2)
        assert r1["gua_flow"]["ben"]["key"] == r2["gua_flow"]["ben"]["key"]
        assert r1["gua_flow"]["zhi"]["key"] == r2["gua_flow"]["zhi"]["key"]
        assert r1["suri"]["basic_num"] == r2["suri"]["basic_num"]
        assert r1["gender"] != r2["gender"]


def test_year_suri_formula_samples() -> None:
    """연도별 수: mod9(나이자리합 + 기본수 - 1)."""
    # 1990생 2026년: 37세 → 3+7=10 → mod9(10+9-1)=9
    assert calc_year_suri(9, 1990, 2026) == 9
    assert calc_year_suri(6, 1985, 1985) == 6  # 1세 → 1+6-1=6
    # 1966생 2026년: 61세 → 6+1=7 → mod9(7+7-1)=4
    assert calc_year_suri(7, 1966, 2026) == 4


def test_full_year_digit_sum_not_last_two() -> None:
    """년합은 전체 연도 자릿수 합(매화 v2 프로토타입의 끝2자리 방식과 구분)."""
    ly = 1990
    assert _year_digit_sum(ly) == 19
    assert _year_digit_sum(ly) != sum(int(c) for c in str(ly)[-2:])  # 9+0=9


def test_hour_shi_index_edge() -> None:
    assert _hour_shi_index(23) == 1
    assert _hour_shi_index(0) == 1
    assert _hour_shi_index(1) == 2
    assert _hour_shi_index(14) == 8


def test_moving_line_on_hex(case=ACCURACY_CASES[6]) -> None:
    """동효 위치가 lines 배열에 정확히 표시."""
    cal, y, m, d, h, mi, gender, leap = case["input"]
    r = build_reading(cal, y, m, d, h, mi, gender=gender, lunar_leap=leap)
    dong_idx = r["gua_flow"]["dong"]["index"]
    moving = [ln for ln in r["gua_flow"]["ben"]["lines"] if ln["moving"]]
    assert len(moving) == 1
    assert moving[0]["index"] == dong_idx


def test_api_maehwa_reading(client) -> None:
    """FastAPI 엔드포인트가 엔진과 동일 결과."""
    from fastapi.testclient import TestClient
    from main import app

    tc = TestClient(app)
    body = {
        "calendar": "lunar",
        "year": 1966,
        "month": 11,
        "day": 4,
        "hour": 2,
        "minute": 5,
        "gender": "female",
        "lunar_leap": False,
        "user_name": "검증",
    }
    res = tc.post("/api/maehwa/reading", json=body)
    assert res.status_code == 200
    data = res.json()
    assert data["gua_flow"]["ben"]["key"] == "5-7"
    assert data["suri"]["basic_num"] == 7


@pytest.fixture
def client():
    pytest.importorskip("fastapi")
    return True
