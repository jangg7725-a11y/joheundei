# -*- coding: utf-8 -*-
"""스토리·월운·합충 출력에 금지 패턴이 없는지 검증."""

from __future__ import annotations

import json

from saju import analysis as an


FORBIDDEN = (
    "여명 해석입니다",
    "여명 기준 년주",
    "여명 기준 월주",
    "여명 기준 일주",
    "여명 기준 시주",
    "남명 기준 년주",
    "여명에서 년주",
    "여명에서 월주",
    "여명에서 일주",
    "여명에서 시주",
    "여명 직업 해석",
    "남명 직업 해석",
    "분석 기간에 마감을 정하세요",
    "같은 주제도 성별에 따라 다른 무게로 읽힙니다",
    "기준 참고입니다",
    "여명·戊일간",
    "여명·",
    "남명·",
    "이 슬롯은",
    "동일 원국이라도 여명 해석",
    "동일 원국이라도 남명 해석",
)


def _collect_strings(obj, out: list) -> None:
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_strings(v, out)


def _assert_no_forbidden(report: dict, label: str) -> None:
    texts: list = []
    _collect_strings(report, texts)
    blob = "\n".join(texts)
    for pat in FORBIDDEN:
        assert pat not in blob, f"{label}: forbidden pattern {pat!r}"


def _build(calendar: str, y: int, m: int, d: int, hour: int, gender: str) -> dict:
    return an.build_report(
        calendar=calendar,
        year=y,
        month=m,
        day=d,
        hour=hour,
        minute=0 if calendar == "solar" else 5,
        gender=gender,
        lunar_leap=False,
    )


def test_verification_female_lunar_1966():
    r = _build("lunar", 1966, 11, 4, 2, "female")
    _assert_no_forbidden(r, "1966-female")
    story = r["원국_스토리텔링"]
    top5 = story["직업_적성"]["최적_직군_TOP5"]
    assert top5
    assert "슬롯" not in top5[0]["이유"]
    assert "동일 원국이라도" not in top5[0]["이유"]

    wol = r["월운표"]["월별"]
    s7 = wol[6]["월별_핵심스토리"]
    s8 = wol[7]["월별_핵심스토리"]
    s9 = wol[8]["월별_핵심스토리"]
    assert len({s7, s8, s9}) >= 2, "7~9절월 스토리가 모두 같음"
    s10 = wol[9]["월별_핵심스토리"]
    s11 = wol[10]["월별_핵심스토리"]
    s12 = wol[11]["월별_핵심스토리"]
    assert len({s10, s11, s12}) >= 2, "10~12절월 스토리가 모두 같음"

    hap = (story.get("unteim_서사") or {}).get("합충_서사") or ""
    for z in ("巳", "亥", "寅", "未"):
        if z not in r["pillars"]["year"]["zhi"] + r["pillars"]["month"]["zhi"]:
            if z not in r["pillars"]["day"]["zhi"] + r["pillars"]["hour"]["zhi"]:
                assert z not in hap or "【" not in hap, f"원국에 없는 {z} 해설"


def test_solar_1990_male():
    r = _build("solar", 1990, 3, 20, 14, "male")
    _assert_no_forbidden(r, "1990-male")


def test_solar_1985_female():
    r = _build("solar", 1985, 7, 15, 8, "female")
    _assert_no_forbidden(r, "1985-female")
