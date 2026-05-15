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

from typing import Any, Dict

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

# 사용자 안내용 — 각 운성을 한두 문장으로 풀어 설명 (입문·참고용)
STAGE_USER_GUIDE: Dict[str, str] = {
    "장생": "새 기운이 싹트는 단계입니다. 새 출발·이직·이사 등 변화를 추진할 때 생명력이 붙기 쉽습니다.",
    "목욕": "감수성과 매력이 드러나기 쉬운 단계입니다. 관계·이미지에 민감해질 수 있어 경계와 자기관리가 도움이 됩니다.",
    "관대": "겉으로 패기와 체면이 살아나는 때입니다. 사회적 역할·직함을 의식하고 성장 욕구가 커지기 쉽습니다.",
    "건록": "실속과 자립을 다지는 단계입니다. 내 힘으로 버티려는 성향이 강해지고 경제·실무에서 발돋움하기 좋습니다.",
    "제왕": "기운이 가장 왕성한 전성기 국면입니다. 추진력과 고집이 함께 커져 성과도 크지만 충돌 시 과열에 주의합니다.",
    "쇠": "급한 확장보다 정리와 유지에 어울리는 단계입니다. 안정·보수적 선택을 선호하게 되기 쉽습니다.",
    "병": "체력·감정 소모가 드러나기 쉬운 단계입니다. 휴식·치유·예술·섬세한 분야에서 오히려 강점이 나올 수 있습니다.",
    "사": "한번 접으면 확 줄어드는 기운이 있습니다. 종교·철학·내적 성찰, 또는 일의 마무리·전환기와 연결되기 쉽습니다.",
    "묘": "내부에 고이고 저장하는 성향입니다. 재물·지식·감정을 축적하지만 융통성은 부족해 보일 수 있습니다.",
    "절": "단절과 새 출발이 교차하는 단계입니다. 관계·일에서 끊고 새 길을 택하는 결단이 나오기 쉽습니다.",
    "태": "계획과 준비, 잉태되는 상태입니다. 아직 드러나지 않은 가능성을 키우며 무리한 노출보다 설계가 유리합니다.",
    "양": "보호와 성장을 받으며 다시 키워 가는 단계입니다. 멘토·가족의 도움, 학습을 통해 회복·축적하기 좋습니다.",
}

# 십이운성이 붙는 「궁」별로 무엇을 볼 때 쓰는지 (입문용)
PILLAR_FOCUS_KR: Dict[str, str] = {
    "year": "년주는 조상·가문 배경, 유년기 환경, 사회에 나아가기 전의 기본 분위기를 가늠할 때 참고합니다.",
    "month": "월주는 부모·형제 인연, 학업과 진로의 초기 환경, 사회에 발을 들이는 방식과 연결해 읽는 경우가 많습니다.",
    "day": "일주는 본인의 자아·건강·배우자 인연 등 성인 이후 삶의 중심축과 맞닿아 있다고 여겨집니다.",
    "hour": "시주는 자녀·노후·말년, 또 행동과 결과가 어떻게 드러나는지에 대한 보조적 경향으로 살펴봅니다.",
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


def pillar_twelve_stages(day_master: str, pillars: dict) -> Dict[str, Dict[str, Any]]:
    """연·월·일·시 지지 각각에 운성명과 의미(한 줄)를 붙여 반환."""
    dm_elem = gj.element_of_stem(day_master)
    yy = gj.STEM_YIN_YANG[gj.stem_index(day_master)]
    out: Dict[str, Dict[str, Any]] = {}
    for key in PILLAR_KEYS:
        zhi = pillars[key]["zhi"]
        bi = gj.branch_index(zhi)
        st = stage_for(day_master, zhi)
        mean = STAGE_MEANING[st]
        ju = JU_LABEL_KR[key]
        zi_lab = ZHI_LABEL_KR[key]
        zhi_kr = gj.BRANCH_KR[bi]
        stage_guide = STAGE_USER_GUIDE.get(st, mean)
        pillar_focus = PILLAR_FOCUS_KR[key]
        해설_통합 = (
            f"{ju} 지지 「{zhi}({zhi_kr})」에 십이운성 「{st}」이 붙습니다. "
            f"{stage_guide} "
            f"{pillar_focus}"
        )
        out[key] = {
            "주": ju,
            "지위": zi_lab,
            "zhi": zhi,
            "zhi_kr": zhi_kr,
            "stage": st,
            "meaning": mean,
            "단계_해설": stage_guide,
            "궁_역할": pillar_focus,
            "해설_통합": 해설_통합,
            "일간_오행": dm_elem,
            "일간_음양": yy,
            "한줄": f"{ju} {zhi}({zhi_kr}) · {st}: {mean}",
            "label": f"{zi_lab} {zhi_kr} → {st} ({mean})",
        }
    return out
