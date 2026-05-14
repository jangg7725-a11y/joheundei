# -*- coding: utf-8 -*-
"""
십이운성(十二運星) — 일간 천간 기준으로 네 지지에 장생~양까지 부착.

순서: 장생(長生) → 목욕(沐浴) → 관대(冠帶) → 건록(建祿) → 제왕(帝旺) →
쇠(衰) → 병(病) → 사(死) → 묘(墓) → 절(絶) → 태(胎) → 양(養).

계산: 동일 오행의 양간(甲·丙·戊·庚·壬)은 지지 순방향으로 장생점부터 진행하고,
음간(乙·丁·己·辛·癸)은 각각 대응하는 장생 지점에서 역방향으로 같은 열두 단계를 적용합니다.
(戊土·己土는 화 기준, 즉 丙·丁과 같은 장생 출발지를 씁니다.)
"""

from __future__ import annotations

from typing import Dict

from . import ganji as gj

STAGES_KR = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]

STAGE_MEANING: Dict[str, str] = {
    "장생": "새로운 시작, 생명력",
    "목욕": "도화, 색정, 감수성",
    "관대": "패기, 자존심",
    "건록": "독립, 전성기 준비",
    "제왕": "최전성기, 고집",
    "쇠": "안정, 보수적",
    "병": "허약, 예술성",
    "사": "종교, 철학",
    "묘": "저축, 고집",
    "절": "단절, 새출발",
    "태": "잉태, 계획",
    "양": "성장, 보호",
}

_YANG_START = {
    "甲": gj.branch_index("亥"),
    "丙": gj.branch_index("寅"),
    "戊": gj.branch_index("寅"),
    "庚": gj.branch_index("巳"),
    "壬": gj.branch_index("申"),
}

_YIN_START = {
    "乙": gj.branch_index("午"),
    "丁": gj.branch_index("酉"),
    "己": gj.branch_index("酉"),
    "辛": gj.branch_index("子"),
    "癸": gj.branch_index("卯"),
}

PILLAR_KEYS = ("year", "month", "day", "hour")
JU_LABEL_KR = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
ZHI_LABEL_KR = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}


def _stage_index_for(dm: str, zhi: str) -> int:
    zi = gj.branch_index(zhi)
    if gj.STEM_YIN_YANG[gj.stem_index(dm)] == "양":
        start = _YANG_START[dm]
        return (zi - start) % 12
    start = _YIN_START[dm]
    return (start - zi) % 12


def stage_for(day_master: str, zhi: str) -> str:
    idx = _stage_index_for(day_master, zhi)
    return STAGES_KR[idx]


def meaning_for_stage(stage: str) -> str:
    return STAGE_MEANING.get(stage, "")


def pillar_twelve_stages(day_master: str, pillars: dict) -> Dict[str, Dict[str, str]]:
    """연·월·일·시 지지 각각에 운성명과 의미(한 줄)를 붙여 반환."""
    dm_elem = gj.element_of_stem(day_master)
    yy = gj.STEM_YIN_YANG[gj.stem_index(day_master)]
    out: Dict[str, Dict[str, str]] = {}
    for key in PILLAR_KEYS:
        zhi = pillars[key]["zhi"]
        bi = gj.branch_index(zhi)
        st = stage_for(day_master, zhi)
        mean = STAGE_MEANING[st]
        ju = JU_LABEL_KR[key]
        zi_lab = ZHI_LABEL_KR[key]
        zhi_kr = gj.BRANCH_KR[bi]
        out[key] = {
            "주": ju,
            "지위": zi_lab,
            "zhi": zhi,
            "zhi_kr": zhi_kr,
            "stage": st,
            "meaning": mean,
            "일간_오행": dm_elem,
            "일간_음양": yy,
            "한줄": f"{ju} {zhi}({zhi_kr}) · {st}: {mean}",
            "label": f"{zi_lab} {zhi_kr} → {st} ({mean})",
        }
    return out
