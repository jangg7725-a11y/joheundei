# -*- coding: utf-8 -*-
"""만세력 단독 페이지 — 사주 계산 결과 → 문헌 매칭 파라미터."""

from __future__ import annotations

from typing import Any

from . import ilwoon as il
from . import ohaeng as oh
from . import saju_calc as sc
from . import sinsal as sn
from . import sipsin as sp
from . import yongsin as ys

PILLAR_KEYS = ("year", "month", "day", "hour")
PILLAR_LABEL = {"year": "년", "month": "월", "day": "일", "hour": "시"}

MATCH_SINSAL_NAMES = (
    "역마살",
    "도화살",
    "괴강살",
    "공망",
    "겁살",
    "원진살",
    "고과살",
    "태양도림",
    "삼재",
    "백호살",
    "양인살",
)

MATCH_GYEOK_SUFFIX = "격"


def extract_match_params(
    day_master: str,
    pillars: dict,
    *,
    gender: str,
    counts: dict[str, int],
    yong_block: dict[str, Any],
    sinsal_block: dict[str, Any],
    sip_stems: dict[str, Any],
) -> dict[str, str]:
    """만세력 saju-match API용 쿼리 값 추출."""
    month_sip = ""
    if isinstance(sip_stems.get("month"), dict):
        month_sip = str(sip_stems["month"].get("sipsin") or "")
    elif isinstance(sip_stems.get("month"), str):
        month_sip = sip_stems["month"]

    gyeokguk = f"{month_sip}{MATCH_GYEOK_SUFFIX}" if month_sip else ""

    sinsal_name = ""
    for row in sinsal_block.get("신살_목록") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("신살") or "")
        if name in MATCH_SINSAL_NAMES:
            sinsal_name = name
            break
    if not sinsal_name:
        for row in sinsal_block.get("신살_목록") or []:
            if isinstance(row, dict) and row.get("신살"):
                sinsal_name = str(row["신살"])
                break

    ohaeng = str(yong_block.get("용신_오행") or "")

    return {
        "shinsin": month_sip,
        "sinsal": sinsal_name,
        "gyeokguk": gyeokguk,
        "ohaeng": ohaeng,
    }


def _pillars_summary(pillars: dict) -> list[dict[str, str]]:
    rows = []
    for pk in PILLAR_KEYS:
        p = pillars[pk]
        rows.append(
            {
                "key": pk,
                "label": PILLAR_LABEL[pk],
                "pillar": p.get("pillar", ""),
                "label_kr": p.get("label_kr", ""),
                "nayin": p.get("nayin", ""),
            }
        )
    return rows


def compute_manseryeok_profile(
    *,
    calendar: str,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "male",
    lunar_leap: bool = False,
    ya_jasi: bool = False,
    hour_unknown: bool = False,
    user_name: str = "",
) -> dict[str, Any]:
    """생년월일시 → 원국 요약 + 매칭 파라미터 + 오늘 일운."""
    calc_hour = 12 if hour_unknown else hour
    calc_minute = 0 if hour_unknown else minute
    calc_ya = False if hour_unknown else ya_jasi

    birth = sc.BirthInput(
        calendar=calendar,
        year=year,
        month=month,
        day=day,
        hour=calc_hour,
        minute=calc_minute,
        lunar_leap=lunar_leap,
        gender=gender,
        ya_jasi=calc_ya,
    )
    raw = sc.compute_saju(birth)
    pillars = raw["pillars"]
    dm = raw["day_master"]
    counts = oh.count_elements(pillars, include_hidden=True)

    sip_full = sp.full_eight_char_sipsin(dm, pillars, gender)
    sip_stems = sip_full.get("천간") or {}
    yong_block = ys.suggest_useful_gods(
        counts, dm, pillars["month"]["zhi"], pillars=pillars
    )
    sinsal_block = sn.analyze_sinsal(dm, pillars, gender=gender)
    match_params = extract_match_params(
        dm,
        pillars,
        gender=gender,
        counts=counts,
        yong_block=yong_block,
        sinsal_block=sinsal_block,
        sip_stems=sip_stems,
    )

    il_pack = il.ilwoon_snapshot_pack(dm, pillars)
    today = il_pack.get("오늘") or {}

    return {
        "user_name": (user_name or "").strip(),
        "calendar_input": calendar,
        "solar": raw.get("solar"),
        "lunar": raw.get("lunar"),
        "is_leap_month": raw.get("is_leap_month"),
        "jieqi_embedded_year": raw.get("jieqi_embedded_year"),
        "day_master": dm,
        "day_master_kr": raw.get("day_master_kr"),
        "day_master_element": raw.get("day_master_element"),
        "pillars": _pillars_summary(pillars),
        "eight_char_string": raw.get("eight_char_string"),
        "yongsin": {
            "용신_오행": yong_block.get("용신_오행"),
            "기신_오행": yong_block.get("기신_오행"),
            "판단_요약": yong_block.get("판단_요약"),
        },
        "match_params": match_params,
        "sinsal_highlights": [
            {
                "신살": r.get("신살"),
                "길흉": r.get("길흉"),
                "해석": (r.get("해석") or "")[:120],
            }
            for r in (sinsal_block.get("신살_목록") or [])[:6]
            if isinstance(r, dict)
        ],
        "ilwoon_today": {
            "양력문자열": today.get("양력문자열"),
            "간지": today.get("간지"),
            "간지한글": today.get("간지한글"),
            "길흉등급": today.get("길흉등급"),
            "한줄판정": today.get("한줄판정"),
        },
        "birth_month_label": f"{month}월",
        "meta": {
            "hour_unknown": hour_unknown,
            "ya_jasi_applied": calc_ya,
        },
    }
