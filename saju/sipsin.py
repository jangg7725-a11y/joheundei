# -*- coding: utf-8 -*-
"""
십신(十神) 및 성별에 따른 육친 참고 매핑.

일간(日干) 기준으로 각 천간과의 관계를 정인·편인·정관·편관·정재·편재·식신·상관·비견·겁재로 분류하고,
사주 팔자 전체(천간 4 + 지지 지장간)에 적용합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import ganji as gj

PILLAR_KEYS = ("year", "month", "day", "hour")
PILLAR_LABELS_KR = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}

_ELEM_IDX = {"목": 0, "화": 1, "토": 2, "금": 3, "수": 4}


def _stem_element_idx(gan: str) -> int:
    return _ELEM_IDX[gj.element_of_stem(gan)]


def _same_yinyang(dm: str, tg: str) -> bool:
    return gj.STEM_YIN_YANG[gj.stem_index(dm)] == gj.STEM_YIN_YANG[gj.stem_index(tg)]


def classify_sipsin(day_master: str, target_gan: str) -> str:
    """
    일간 대비 대상 천간의 십신.

    비견·겁재·식신·상관·편재·정재·편관·정관·편인·정인 규칙
    (같은 오행 / 일간이 생·극 당하는 관계 / 음양 동일 여부).
    """
    dm = day_master
    tg = target_gan
    if dm == tg:
        return "일간"

    de = _stem_element_idx(dm)
    te = _stem_element_idx(tg)
    sy = _same_yinyang(dm, tg)

    if te == de:
        return "비견" if sy else "겁재"
    if te == (de + 1) % 5:
        return "식신" if sy else "상관"
    if te == (de + 2) % 5:
        return "편재" if sy else "정재"
    if te == (de + 3) % 5:
        return "편관" if sy else "정관"
    if te == (de + 4) % 5:
        return "편인" if sy else "정인"

    return "미상"


def is_female_gender(gender: str) -> bool:
    g = gender.strip().lower()
    return g in ("female", "f", "여", "여성")


def yukchin_roles(sipsin: str, *, female: bool) -> List[str]:
    """십신별 육친 태그(참고용·파종에 따라 달라질 수 있음)."""
    if sipsin in ("일간", "미상"):
        return []

    if female:
        if sipsin == "정관":
            return ["남편"]
        if sipsin in ("식신", "상관"):
            return ["자녀"]
        if sipsin in ("정인", "편인"):
            return ["모친"]
        if sipsin in ("편재", "정재"):
            return ["부친"]
        if sipsin in ("비견", "겁재"):
            return ["형제"]
        return []

    # 남성
    if sipsin == "편재":
        return ["부친"]
    if sipsin == "정재":
        return ["아내", "부친"]
    if sipsin in ("편관", "정관"):
        return ["자녀"]
    if sipsin in ("정인", "편인"):
        return ["모친"]
    if sipsin in ("비견", "겁재"):
        return ["형제"]
    return []


def _fixed_yukchin_legend() -> Dict[str, Any]:
    return {
        "여성": {
            "남편": ["정관"],
            "자녀": ["식신", "상관"],
            "모친": ["정인", "편인"],
            "부친": ["편재", "정재"],
            "형제": ["비견", "겁재"],
        },
        "남성": {
            "아내": ["정재"],
            "자녀": ["편관", "정관"],
            "모친": ["정인", "편인"],
            "부친": ["편재", "정재"],
            "형제": ["비견", "겁재"],
        },
    }


def _stem_row(day_master: str, gan: str, pillar_key: str, female: bool) -> Dict[str, Any]:
    if pillar_key == "day":
        return {
            "gan": gan,
            "gan_kr": gj.STEM_KR[gj.stem_index(gan)],
            "name": "일간(본인)",
            "sipsin": "일간",
            "yukchin": [],
        }

    sip = classify_sipsin(day_master, gan)
    return {
        "gan": gan,
        "gan_kr": gj.STEM_KR[gj.stem_index(gan)],
        "name": f"{PILLAR_LABELS_KR[pillar_key]} 천간",
        "sipsin": sip,
        "yukchin": yukchin_roles(sip, female=female),
    }


def _branch_block(day_master: str, zhi: str, pillar_key: str, female: bool) -> Dict[str, Any]:
    hidden_gans = gj.jijanggan_ordered(zhi)
    items: List[Dict[str, Any]] = []
    for gan in hidden_gans:
        sip = classify_sipsin(day_master, gan)
        items.append(
            {
                "gan": gan,
                "gan_kr": gj.STEM_KR[gj.stem_index(gan)],
                "sipsin": sip,
                "yukchin": yukchin_roles(sip, female=female),
            }
        )

    return {
        "zhi": zhi,
        "zhi_kr": gj.BRANCH_KR[gj.branch_index(zhi)],
        "pillar_label": PILLAR_LABELS_KR[pillar_key],
        "hidden": items,
        "summary": " · ".join(f"{x['gan']}→{x['sipsin']}" for x in items) if items else "",
    }


def full_eight_char_sipsin(day_master: str, pillars: dict, gender: str) -> Dict[str, Any]:
    """팔자 전체: 천간 4 + 각 지지의 지장간 간마다 십신·육친 참고."""
    female = is_female_gender(gender)
    stems = {k: _stem_row(day_master, pillars[k]["gan"], k, female) for k in PILLAR_KEYS}
    branches = {k: _branch_block(day_master, pillars[k]["zhi"], k, female) for k in PILLAR_KEYS}

    flat_eight: List[Dict[str, Any]] = []
    seq = [
        ("년간", "stem", "year"),
        ("월간", "stem", "month"),
        ("일간", "stem", "day"),
        ("시간", "stem", "hour"),
        ("년지", "branch", "year"),
        ("월지", "branch", "month"),
        ("일지", "branch", "day"),
        ("시지", "branch", "hour"),
    ]
    for label, kind, pk in seq:
        if kind == "stem":
            row = stems[pk]
            flat_eight.append(
                {
                    "위치": label,
                    "글자": row["gan"],
                    "글자_한글": row["gan_kr"],
                    "층": "천간",
                    "십신": row["sipsin"],
                    "육친": row["yukchin"],
                }
            )
        else:
            br = branches[pk]
            for h in br["hidden"]:
                flat_eight.append(
                    {
                        "위치": f'{label}·{h["gan"]}',
                        "글자": br["zhi"],
                        "글자_한글": br["zhi_kr"],
                        "층": "지장간",
                        "십신": h["sipsin"],
                        "육친": h["yukchin"],
                    }
                )

    return {
        "day_master": day_master,
        "gender_basis": "여성 육친표" if female else "남성 육친표",
        "육친_매핑_안내": _fixed_yukchin_legend(),
        "천간": stems,
        "지지": branches,
        "팔자_펼침": flat_eight,
    }


def sipsin_for_pillar_stems(day_master: str, pillars: dict, gender: str = "") -> Dict[str, Dict[str, Any]]:
    """천간 십신만 (기존 API 호환: gan, name, sipsin + yukchin·gan_kr)."""
    female = is_female_gender(gender)
    return {k: _stem_row(day_master, pillars[k]["gan"], k, female) for k in PILLAR_KEYS}


def sipsin_for_hidden_stems(
    day_master: str,
    zhi: str,
    hidden: List[str],
    gender: str = "",
) -> List[Dict[str, Any]]:
    """지장간 각 간의 십신(zhi는 호환용 미사용—ganji 지장간과 동일 목록 권장)."""
    female = is_female_gender(gender)
    rows: List[Dict[str, Any]] = []
    for gan in hidden:
        sip = classify_sipsin(day_master, gan)
        rows.append(
            {
                "gan": gan,
                "gan_kr": gj.STEM_KR[gj.stem_index(gan)],
                "sipsin": sip,
                "yukchin": yukchin_roles(sip, female=female),
            }
        )
    return rows
