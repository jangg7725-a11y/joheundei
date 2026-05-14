# -*- coding: utf-8 -*-
"""
두 명의 원국을 바탕으로 한 종합 궁합 분석.

분석 항목:
  1. 일지 궁합 상세 (충/합/파/해/형 + 스토리텔링 + 커플 태그)
  2. 전체 8글자 지지 대조 (합/충/파/해 카운트)
  3. 오행 궁합 상세 (분포 나란히 + 보완 스토리)
  4. 일간 궁합 상세 (생/극/비화/설 + 연애/결혼 해석)
  5. 십신으로 보는 궁합
  6. 천간합
  7. 용신 궁합 상세
  8. 세운 궁합 (연도별 + 월별 12개월)
  9. 종합 총평 + 강점/과제/결혼 적합도

정식 명리 학파·파종별 해석과 다를 수 있으며 참고용입니다.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from . import ganji as gj
from . import ohaeng as oh
from . import sewoon as sw
from . import sipsin as sp
from . import wolwoon as ww
from . import yongsin as ys

PILLAR_KEYS = ("year", "month", "day", "hour")
PILLAR_KR = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
_ELEM_ORDER = ("목", "화", "토", "금", "수")
_ELEM_BODY = {"목": "간·담·눈", "화": "심장·소장·혈압", "토": "위장·비장·면역", "금": "폐·대장·피부", "수": "신장·방광·뼈"}
_ELEM_TRAIT = {
    "목": "성장·추진력·창의", "화": "열정·표현력·사교",
    "토": "안정·신뢰·현실감", "금": "결단력·원칙·집중",
    "수": "감성·직관·유연성",
}

_CHONG_SET = {tuple(sorted(p)) for p in gj.CHONG_PAIRS}
_PO_SET = {tuple(sorted(p)) for p in gj.LIU_PO}
_HAI_SET = {tuple(sorted(p)) for p in gj.LIU_HAI}
_HE_SET = {tuple(sorted(p)) for p in gj.LIU_HE}

# 삼형 판정용
_XING_GROUPS = [
    frozenset(gj.XING_SAN_INSAM),
    frozenset(gj.XING_SAN_GOJI),
    frozenset(gj.XING_SANG_JAMYO),
    frozenset(gj.XING_ZI_BRANCHES),
]

CHEON_GAN_HAP_LABEL: Dict[frozenset, str] = {
    frozenset(("甲", "己")): "甲己합(토화)",
    frozenset(("乙", "庚")): "乙庚합(금화)",
    frozenset(("丙", "辛")): "丙辛합(수화)",
    frozenset(("丁", "壬")): "丁壬합(목화)",
    frozenset(("戊", "癸")): "戊癸합(화화)",
}

_COUPLE_TAG = {
    "육합":   ("#천생연분", "#자연스러운끌림", "#인연형"),
    "충":     ("#불꽃커플", "#자극형", "#성장형"),
    "파":     ("#서서히멀어지는형", "#소통필수"),
    "해":     ("#잠재갈등형", "#배려필수"),
    "형":     ("#긴장형", "#규칙충돌"),
    "중립":   ("#동반자형", "#안정형"),
}

_SIPSIN_PARTNER_MSG: Dict[str, str] = {
    "정관": "든든한 버팀목이자 이상형으로 안정감을 줍니다.",
    "편관": "강렬한 매력과 긴장감이 공존하는 상대입니다.",
    "정재": "현실적으로 잘 맞고 살림이 안정되는 상대입니다.",
    "편재": "활력과 재미를 주나 예측이 어려운 상대입니다.",
    "식신": "편안하고 풍요로운 에너지를 나누는 상대입니다.",
    "상관": "창의·표현이 넘치나 자유분방해 조율이 필요합니다.",
    "정인": "어머니처럼 포용하고 보호해주는 상대입니다.",
    "편인": "독창적이고 신비한 매력의 상대이지만 소통이 중요합니다.",
    "비견": "동등한 관계로 서로 자극을 주나 자존심 충돌에 유의하세요.",
    "겁재": "경쟁·갈등 관계로 주도권 다툼이 생기기 쉽습니다.",
    "일간": "일간이 같아 비견과 동일, 동등·경쟁 관계입니다.",
    "미상": "십신 분류가 어렵습니다.",
}


# ── 내부 유틸 ────────────────────────────────────────────────────────────────

def _pair_key(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted((a, b)))


def _zhi_pair_relations(za: str, zb: str) -> List[str]:
    """두 지지 사이 모든 관계 태그 반환."""
    key = _pair_key(za, zb)
    tags: List[str] = []
    if key in _CHONG_SET:
        tags.append("충")
    if key in _PO_SET:
        tags.append("파")
    if key in _HAI_SET:
        tags.append("해")
    if key in _HE_SET:
        tags.append("육합")
    for xg in _XING_GROUPS:
        if za in xg and zb in xg and za != zb:
            tags.append("형")
            break
    return tags


def _star_bar(n: float) -> Tuple[int, str]:
    v = max(1, min(5, int(round(n))))
    return v, "★" * v + "☆" * (5 - v)


def _pct_bar(pct: int, width: int = 10) -> str:
    filled = max(0, min(width, round(pct / 10)))
    return "█" * filled + "░" * (width - filled)


def _heart_emoji(star: int) -> str:
    return "❤️" * star + "🤍" * (5 - star)


# ── 1-1. 일지 궁합 상세 ───────────────────────────────────────────────────────

_ILJI_STORY: Dict[str, str] = {
    "육합": (
        "첫 만남부터 강한 끌림이 있어 자연스럽게 가까워지는 천생연분형 커플입니다. "
        "일지 육합은 생활 리듬과 감성이 맞아 편안함을 주는 인연의 표시입니다."
    ),
    "충": (
        "강렬한 끌림이 있으나 가치관·생활 패턴 충돌이 잦은 불꽃형 커플입니다. "
        "서로 자극을 주고 성장시키는 면이 있으나 감정 조절과 대화가 핵심입니다."
    ),
    "파": (
        "초반엔 잘 맞는 듯하나 시간이 지날수록 균열이 생기는 서서히 멀어지는 형입니다. "
        "서로의 기대치를 솔직히 이야기하는 소통 습관이 관계를 오래 유지하는 열쇠입니다."
    ),
    "해": (
        "보이지 않는 갈등이 누적되는 형으로 대화와 배려가 특히 중요합니다. "
        "사소한 불만을 쌓아두지 말고 표현하는 것이 관계의 건강을 지킵니다."
    ),
    "형": (
        "서로의 규칙·원칙이 부딪히는 긴장형 커플입니다. "
        "각자의 기준을 존중하고 역할을 명확히 하면 안정을 찾을 수 있습니다."
    ),
    "중립": (
        "일지만으로는 뚜렷한 충·합·파·해 패턴이 없습니다. "
        "다른 주와 대운 흐름이 전체 관계의 색을 결정합니다."
    ),
}


def analyze_ilji_relations(zhi_a: str, zhi_b: str) -> Dict[str, Any]:
    """두 일지 지지 관계 — 충/합/파/해/형 판정 + 스토리 + 커플 태그."""
    tags = _zhi_pair_relations(zhi_a, zhi_b)

    if "육합" in tags:
        main_type = "육합"
        couple_type = "천생연분형"
    elif "충" in tags:
        main_type = "충"
        couple_type = "불꽃커플형"
    elif "파" in tags:
        main_type = "파"
        couple_type = "서서히 멀어지는 형"
    elif "해" in tags:
        main_type = "해"
        couple_type = "잠재갈등 주의형"
    elif "형" in tags:
        main_type = "형"
        couple_type = "긴장형"
    else:
        main_type = "중립"
        couple_type = "동반자형"

    couple_tags = list(_COUPLE_TAG.get(main_type, _COUPLE_TAG["중립"]))

    return {
        "지지_A": zhi_a,
        "지지_B": zhi_b,
        "관계_표기": tags,
        "주_관계": main_type,
        "커플_유형": couple_type,
        "커플_태그": couple_tags,
        "스토리": _ILJI_STORY.get(main_type, _ILJI_STORY["중립"]),
        "해설": _ILJI_STORY.get(main_type, _ILJI_STORY["중립"]),
    }


# ── 1-2. 전체 8글자 지지 대조 ────────────────────────────────────────────────

def analyze_all_zhi(pillars_a: Dict, pillars_b: Dict) -> Dict[str, Any]:
    """두 사람 년/월/일/시 지지 전체 대조 — 합/충/파/해/형 카운트."""
    hap_list: List[Dict] = []
    chong_list: List[Dict] = []
    other_list: List[Dict] = []

    for ka in PILLAR_KEYS:
        za = pillars_a[ka]["zhi"]
        for kb in PILLAR_KEYS:
            zb = pillars_b[kb]["zhi"]
            tags = _zhi_pair_relations(za, zb)
            if not tags:
                continue
            entry = {
                "A_궁": PILLAR_KR[ka], "A_지": za,
                "B_궁": PILLAR_KR[kb], "B_지": zb,
                "관계": tags,
            }
            if "육합" in tags:
                hap_list.append(entry)
            elif "충" in tags:
                chong_list.append(entry)
            else:
                other_list.append(entry)

    hap_n = len(hap_list)
    chong_n = len(chong_list)

    if hap_n >= 3:
        inyon = "매우 강한 인연 — 여러 궁에서 합이 성립해 강력한 끌림과 유대감이 있습니다."
    elif hap_n >= 1 and chong_n == 0:
        inyon = "좋은 인연 — 합이 있고 충이 없어 관계가 부드럽게 흐를 수 있습니다."
    elif chong_n >= 3:
        inyon = "갈등이 많은 인연 — 여러 궁 충으로 마찰이 잦고 조율이 필요합니다."
    elif chong_n > hap_n:
        inyon = "긴장 인연 — 충이 합보다 많아 서로 자극하고 부딪히는 편입니다."
    elif hap_n > 0 and chong_n > 0:
        inyon = "복합 인연 — 끌림과 갈등이 공존하는 다이나믹한 관계입니다."
    else:
        inyon = "평범한 인연 — 뚜렷한 합·충 없이 무난하게 흘러가는 편입니다."

    return {
        "합_목록": hap_list,
        "충_목록": chong_list,
        "기타_목록": other_list,
        "합_개수": hap_n,
        "충_개수": chong_n,
        "인연_강도_판정": inyon,
    }


# ── 1-3. 오행 궁합 상세 ───────────────────────────────────────────────────────

def analyze_ohaeng_overlap(
    counts_a: Dict[str, int],
    counts_b: Dict[str, int],
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, Any]:
    """오행 분포 비교·보완·과다 충돌 + 분포 표시 + 스토리."""
    dom_a = oh.dominant_weak_elements(counts_a)
    dom_b = oh.dominant_weak_elements(counts_b)
    strong_a: Set[str] = set(dom_a.get("strong") or [])
    weak_a: Set[str] = set(dom_a.get("weak") or [])
    strong_b: Set[str] = set(dom_b.get("strong") or [])
    weak_b: Set[str] = set(dom_b.get("weak") or [])

    total_a = sum(counts_a.get(e, 0) for e in _ELEM_ORDER) or 1
    total_b = sum(counts_b.get(e, 0) for e in _ELEM_ORDER) or 1
    avg_a = total_a / 5
    avg_b = total_b / 5

    fill_ab: List[str] = []   # A 결핍, B 충족
    fill_ba: List[str] = []   # B 결핍, A 충족
    clash_elems: List[str] = []

    for e in _ELEM_ORDER:
        if e in weak_a and e in strong_b:
            fill_ab.append(e)
        if e in weak_b and e in strong_a:
            fill_ba.append(e)
        if e in strong_a and e in strong_b:
            if counts_a.get(e, 0) >= avg_a + 0.01 and counts_b.get(e, 0) >= avg_b + 0.01:
                clash_elems.append(e)

    # 분포 표시 (예: "木1 火3 土2 金1 水0")
    def dist_str(c: Dict[str, int]) -> str:
        return "  ".join(f"{e}{c.get(e, 0)}" for e in ("木", "火", "土", "金", "水")
                         if True)  # always show all

    dist_kr_a = "  ".join(f"{e}{counts_a.get(e,0)}" for e in _ELEM_ORDER)
    dist_kr_b = "  ".join(f"{e}{counts_b.get(e,0)}" for e in _ELEM_ORDER)

    # 스토리 생성
    story_parts: List[str] = []
    if fill_ab:
        elems_str = "·".join(fill_ab)
        traits = "·".join(_ELEM_TRAIT.get(e, e) for e in fill_ab)
        story_parts.append(
            f"{label_a}는 {elems_str} 기운이 부족해 {traits} 면이 약한데, "
            f"{label_b}의 강한 {elems_str} 기운이 이를 채워줍니다."
        )
    if fill_ba:
        elems_str = "·".join(fill_ba)
        traits = "·".join(_ELEM_TRAIT.get(e, e) for e in fill_ba)
        story_parts.append(
            f"{label_b}는 {elems_str} 기운이 약해 {traits} 면이 필요한데, "
            f"{label_a}의 {elems_str} 기운이 활력을 불어넣어 줍니다."
        )
    if clash_elems:
        elems_str = "·".join(clash_elems)
        story_parts.append(
            f"두 분 모두 {elems_str} 기운이 강해 고집·주도권 충돌이 생기기 쉬우니 역할 분담이 필요합니다."
        )
    if not story_parts:
        story_parts.append(
            "오행 분포가 비슷해 서로 보완보다는 평행하게 흐르는 편입니다. "
            "공통 관심사가 관계의 접착제가 됩니다."
        )

    보완_점수 = min(5, max(1, len(fill_ab) + len(fill_ba) + (0 if clash_elems else 1)))

    return {
        f"{label_a}_오행_분포": dist_kr_a,
        f"{label_b}_오행_분포": dist_kr_b,
        "A_강함": sorted(strong_a),
        "A_약함": sorted(weak_a),
        "B_강함": sorted(strong_b),
        "B_약함": sorted(weak_b),
        "A가_부족_B가_보완": fill_ab,
        "B가_부족_A가_보완": fill_ba,
        "동일_과다_충돌후보": clash_elems,
        "오행_보완_점수": 보완_점수,
        "스토리": " ".join(story_parts),
        "요약_문장": story_parts,
    }


# ── 1-4. 일간 궁합 상세 ───────────────────────────────────────────────────────

_ILGAN_LOVE_MSG = {
    "생(A→B)": (
        "A가 B를 도우며 성장시키는 헌신형 구조입니다. "
        "A는 베푸는 역할이 자연스럽고 B는 기대고 싶어질 수 있어, "
        "균형을 맞추면 안정적이고 따뜻한 관계가 됩니다."
    ),
    "생(B→A)": (
        "B가 A를 돌보고 지지하는 의존형 구조입니다. "
        "B의 헌신이 크게 나타날 수 있어 B가 지치지 않도록 "
        "A가 감사와 배려를 자주 표현하는 것이 중요합니다."
    ),
    "극(A→B)": (
        "A가 B를 통제·압박하는 주도형 구조입니다. "
        "연애 초기에는 A의 리더십이 매력으로 보이나, "
        "장기적으로 B가 압박을 느낄 수 있어 존중이 핵심입니다."
    ),
    "극(B→A)": (
        "B가 A를 압박하는 구조로 A가 종속적 위치에 서기 쉽습니다. "
        "A가 자신의 의견을 당당히 표현하고 B가 이를 존중하는 "
        "훈련이 관계의 건강을 지킵니다."
    ),
    "설(A→B)": (
        "A의 에너지를 B가 흡수하는 구조입니다. "
        "A는 생기가 빠져나가는 느낌을 받을 수 있어 "
        "서로의 에너지 균형에 주의가 필요합니다."
    ),
    "설(B→A)": (
        "B의 에너지를 A가 흡수하는 구조로 B가 소진되기 쉽습니다. "
        "A가 B의 피로를 세심히 살피고 충전 시간을 배려해야 합니다."
    ),
    "비화": (
        "두 분은 오행이 같은 대등한 관계입니다. "
        "서로를 잘 이해하나 경쟁심과 자존심이 부딪힐 수 있습니다. "
        "공동 목표를 세우면 강력한 동반자가 됩니다."
    ),
}

_ILGAN_MARRIAGE_MSG = {
    "생(A→B)": "결혼하면 A가 가정의 기둥이 되기 쉬운 구조. A의 희생이 크지 않도록 역할을 조율하세요.",
    "생(B→A)": "B가 살림·정서적 지지를 담당하기 쉬운 구조. B가 번아웃되지 않도록 A의 감사 표현이 필수입니다.",
    "극(A→B)": "A 주도 결혼 생활. 결정권을 A가 갖기 쉬우나 B의 의사도 존중받아야 장기 안정됩니다.",
    "극(B→A)": "B 주도 결혼 생활. A가 억눌리지 않도록 독립적 공간과 역할이 필요합니다.",
    "설(A→B)": "A가 에너지를 많이 쏟는 결혼. A의 개인 시간과 재충전 공간을 보장하세요.",
    "설(B→A)": "B가 에너지를 많이 쏟는 결혼. B의 취미·사회 활동이 관계의 활력소가 됩니다.",
    "비화": "대등한 파트너십. 역할 분담을 명확히 하고 서로의 방식을 인정하면 강한 결혼 생활을 합니다.",
}


def _ilgan_type(dm_a: str, dm_b: str) -> str:
    ea = gj.element_of_stem(dm_a)
    eb = gj.element_of_stem(dm_b)
    if ea == eb:
        return "비화"
    gm = ys.GENERATE_MAP
    cm = ys.CONTROL_MAP
    if gm[ea] == eb:
        return "생(A→B)"
    if gm[eb] == ea:
        return "생(B→A)"
    if cm[ea] == eb:
        return "극(A→B)"
    if cm[eb] == ea:
        return "극(B→A)"
    # 설(洩): A가 B를 생해주는 역관계 = B가 A를 설기
    if gm[eb] == ea:
        return "설(A→B)"
    if gm[ea] == eb:
        return "설(B→A)"
    return "비화"


def analyze_ilgan_relation(dm_a: str, dm_b: str) -> Dict[str, Any]:
    """일간 오행의 생·극·비화·설 + 연애·결혼 해석."""
    ea = gj.element_of_stem(dm_a)
    eb = gj.element_of_stem(dm_b)
    t = _ilgan_type(dm_a, dm_b)

    return {
        "유형": t,
        "오행_A": ea,
        "오행_B": eb,
        "연애_해석": _ILGAN_LOVE_MSG.get(t, "오행 관계를 단순 생극으로 분류하기 어렵습니다."),
        "결혼_해석": _ILGAN_MARRIAGE_MSG.get(t, "상황에 따라 유동적으로 역할이 형성됩니다."),
        "해설": _ILGAN_LOVE_MSG.get(t, "오행 관계를 단순 생극으로 분류하기 어렵습니다."),
    }


# ── 1-5. 십신 궁합 ────────────────────────────────────────────────────────────

def analyze_sipsin_goonghap(dm_a: str, dm_b: str, label_a: str = "A", label_b: str = "B") -> Dict[str, Any]:
    """A 기준 B의 십신 / B 기준 A의 십신."""
    sip_ab = sp.classify_sipsin(dm_a, dm_b)   # A 눈에 B가
    sip_ba = sp.classify_sipsin(dm_b, dm_a)   # B 눈에 A가

    # "일간" 마커 → "비견"으로 표시
    if sip_ab == "일간":
        sip_ab = "비견"
    if sip_ba == "일간":
        sip_ba = "비견"

    msg_ab = _SIPSIN_PARTNER_MSG.get(sip_ab, "관계 설명을 참고하세요.")
    msg_ba = _SIPSIN_PARTNER_MSG.get(sip_ba, "관계 설명을 참고하세요.")

    return {
        f"{label_a}_눈에_{label_b}의_십신": sip_ab,
        f"{label_b}_눈에_{label_a}의_십신": sip_ba,
        f"{label_a}_입장_해설": f"{label_b}는 {label_a}에게 {sip_ab}(으)로, {msg_ab}",
        f"{label_b}_입장_해설": f"{label_a}는 {label_b}에게 {sip_ba}(으)로, {msg_ba}",
        "십신_A기준_B": sip_ab,
        "십신_B기준_A": sip_ba,
    }


# ── 1-6. 천간합 ───────────────────────────────────────────────────────────────

def analyze_cheon_gan_hap(dm_a: str, dm_b: str) -> Dict[str, Any]:
    key = frozenset((dm_a, dm_b))
    if key not in ys.CHEON_GAN_HAP_ELEM:
        return {
            "성립": False,
            "화기_오행": "—",
            "표기": "—",
            "해설": "일간 천간합 패턴은 아닙니다.",
        }
    label = CHEON_GAN_HAP_LABEL.get(key, "천간합")
    elem = ys.CHEON_GAN_HAP_ELEM[key]
    return {
        "성립": True,
        "화기_오행": elem,
        "표기": label,
        "해설": (
            f"{label}이 성립합니다. 천간합은 두 사람의 에너지가 강하게 끌리는 "
            "인연 신호로, 처음 만났을 때 강한 이끌림을 느끼기 쉬운 조합입니다."
        ),
    }


# ── 1-7. 용신 궁합 상세 ───────────────────────────────────────────────────────

def _yongsin_match_detail(my_yong: Dict[str, Any], partner_dm: str, my_label: str, partner_label: str) -> Dict[str, Any]:
    pe = gj.element_of_stem(partner_dm)
    y_elem = my_yong.get("용신_오행") or ""
    hee_list = list(my_yong.get("희신") or [])
    gi_list = list(my_yong.get("기신") or [])

    if y_elem and pe == y_elem:
        grade, grade_kr = "최상", "최상"
        msg = (
            f"{partner_label}의 일간 오행({pe})이 {my_label}의 용신({y_elem})과 일치합니다. "
            f"{partner_label}의 존재 자체가 {my_label}의 균형과 에너지를 보완해주는 최적 조합입니다."
        )
    elif pe in hee_list:
        grade, grade_kr = "양호", "양호"
        msg = (
            f"{partner_label}의 일간 오행({pe})이 {my_label}의 희신 방향과 맞습니다. "
            f"긍정적 보완이 기대되는 좋은 에너지 조합입니다."
        )
    elif pe in gi_list:
        grade, grade_kr = "주의", "주의"
        msg = (
            f"{partner_label}의 일간 오행({pe})이 {my_label}의 기신 쪽에 해당합니다. "
            f"생활 방식·가치관에서 마찰이 생기기 쉬우니 서로 배려가 필요합니다."
        )
    else:
        grade, grade_kr = "보통", "보통"
        msg = (
            f"{partner_label}의 일간 오행({pe})이 {my_label}의 용신·기신과 직접 겹치지는 않습니다. "
            f"다른 원국 요소로 보완되며 무난한 에너지 조합입니다."
        )

    return {
        "상대_일간_오행": pe,
        "등급": grade,
        "등급_한글": grade_kr,
        "해설": msg,
    }


def analyze_yongsin_pair(
    yong_a: Dict[str, Any],
    yong_b: Dict[str, Any],
    dm_a: str,
    dm_b: str,
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, Any]:
    match_ab = _yongsin_match_detail(yong_a, dm_b, label_a, label_b)
    match_ba = _yongsin_match_detail(yong_b, dm_a, label_b, label_a)

    grades = {match_ab["등급"], match_ba["등급"]}
    if grades == {"최상"}:
        overall = "서로가 서로의 용신 — 최상의 에너지 조합입니다."
    elif "최상" in grades:
        overall = "한쪽이 상대의 용신 — 좋은 에너지 보완 관계입니다."
    elif "주의" in grades and "최상" not in grades and "양호" not in grades:
        overall = "서로가 서로의 기신 방향 — 에너지 충돌에 주의가 필요합니다."
    elif "주의" in grades:
        overall = "한쪽이 상대의 기신 방향 — 배려와 조율이 필요한 관계입니다."
    else:
        overall = "용신·기신과 무관한 중립적 에너지 조합입니다."

    return {
        "A가_느끼는_상대": match_ab,
        "B가_느끼는_상대": match_ba,
        "종합_평가": overall,
    }


# ── 2. 세운 궁합 (연도별 + 월별) ─────────────────────────────────────────────

def _sewoon_grade_emoji(grade: str) -> str:
    return {"대길운": "🟢", "길운": "🟢", "보통운": "⚪", "흉운": "🔴", "대흉운": "🔴"}.get(grade, "⚪")


def _month_compat_grade(grade_a: str, grade_b: str) -> Tuple[str, str]:
    """두 사람 월운 등급 → 궁합 등급 + 이모지."""
    BAD = {"대흉우려", "흉"}
    GOOD = {"대길", "길"}
    a_bad = grade_a in BAD
    b_bad = grade_b in BAD
    a_good = grade_a in GOOD
    b_good = grade_b in GOOD

    if a_good and b_good:
        return "💚", "함께 좋은 달"
    if a_bad and b_bad:
        return "🔴", "함께 주의할 달"
    if a_bad or b_bad:
        return "🟡", "한쪽 주의 달"
    return "⚪", "보통"


def analyze_sewoon_goonghap(
    raw_a: Dict[str, Any],
    raw_b: Dict[str, Any],
    counts_a: Dict[str, int],
    counts_b: Dict[str, int],
    gender_a: str,
    gender_b: str,
    current_year: int,
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, Any]:
    """세운 궁합 — 연도 세운 각각 + 월별 12개월 궁합."""
    pillars_a = raw_a["pillars"]
    pillars_b = raw_b["pillars"]
    dm_a = raw_a["day_master"]
    dm_b = raw_b["day_master"]

    sew_a = sw.analyze_sewoon_year(dm_a, pillars_a, gender_a, current_year, counts=counts_a)
    sew_b = sw.analyze_sewoon_year(dm_b, pillars_b, gender_b, current_year, counts=counts_b)

    gz = sew_a.get("간지") or str(current_year)
    grade_a = sew_a.get("운세등급") or "보통운"
    grade_b = sew_b.get("운세등급") or "보통운"
    star_a = (sew_a.get("별점_문자") or "")
    star_b = (sew_b.get("별점_문자") or "")

    # 세운이 두 사람 일지에 미치는 영향 분석
    sew_zhi = sew_a.get("지지") or ""
    zhi_a = pillars_a["day"]["zhi"]
    zhi_b = pillars_b["day"]["zhi"]

    chong_a = any(tuple(sorted((sew_zhi, zhi_a))) in _CHONG_SET for _ in [1]) if sew_zhi else False
    chong_b = any(tuple(sorted((sew_zhi, zhi_b))) in _CHONG_SET for _ in [1]) if sew_zhi else False
    hap_a = any(tuple(sorted((sew_zhi, zhi_a))) in _HE_SET for _ in [1]) if sew_zhi else False
    hap_b = any(tuple(sorted((sew_zhi, zhi_b))) in _HE_SET for _ in [1]) if sew_zhi else False

    if hap_a and hap_b:
        sew_couple_msg = (
            f"올해 {gz} 세운이 두 분 모두의 일지와 합하여 "
            "관계가 깊어지고 안정적 에너지가 흐르는 좋은 해입니다."
        )
        sew_compat = "좋음"
    elif chong_a and chong_b:
        sew_couple_msg = (
            f"올해 {gz} 세운이 두 분 일지를 모두 충하여 "
            "큰 변화와 전환점이 될 수 있는 해입니다. 관계 방향을 함께 점검하세요."
        )
        sew_compat = "주의"
    elif chong_a or chong_b:
        who = label_a if chong_a else label_b
        sew_couple_msg = (
            f"올해 세운이 {who}의 일지를 충하여 "
            f"{who}가 불안정해질 수 있습니다. 상대방의 세심한 지지가 중요한 해입니다."
        )
        sew_compat = "보통"
    elif hap_a or hap_b:
        who = label_a if hap_a else label_b
        sew_couple_msg = (
            f"올해 세운이 {who}에게 합의 기운을 가져와 "
            "관계에 새로운 인연·기회가 생기기 좋은 흐름입니다."
        )
        sew_compat = "좋음"
    else:
        sew_couple_msg = (
            f"올해 {gz} 세운이 두 분 일지와 직접적인 충·합은 없습니다. "
            "각자의 대운 흐름에 집중하면서 안정적으로 관계를 이어갈 수 있습니다."
        )
        sew_compat = "보통"

    # 월별 궁합 12개월
    wol_a = ww.wolwoon_year_pack(dm_a, pillars_a, current_year, gender=gender_a, counts=counts_a)
    wol_b = ww.wolwoon_year_pack(dm_b, pillars_b, current_year, gender=gender_b, counts=counts_b)

    months_a = {m["절월번호"]: m for m in (wol_a.get("월별") or [])}
    months_b = {m["절월번호"]: m for m in (wol_b.get("월별") or [])}

    good_months: List[int] = []
    bad_months: List[int] = []
    monthly: List[Dict[str, Any]] = []

    for mn in range(1, 13):
        ma = months_a.get(mn, {})
        mb = months_b.get(mn, {})
        ga = ma.get("길흉판정") or ma.get("길흉등급_5단계") or "평"
        gb = mb.get("길흉판정") or mb.get("길흉등급_5단계") or "평"
        gz_mon = ma.get("월주간지") or f"{mn}절월"
        emoji, label_compat = _month_compat_grade(ga, gb)

        if emoji == "💚":
            good_months.append(mn)
        elif emoji == "🔴":
            bad_months.append(mn)

        story_a = ma.get("월별_핵심스토리") or f"{label_a} {ga} 달"
        story_b = mb.get("월별_핵심스토리") or f"{label_b} {gb} 달"

        monthly.append({
            "절월": mn,
            "월주간지": gz_mon,
            f"{label_a}_길흉": ga,
            f"{label_b}_길흉": gb,
            "궁합_등급": label_compat,
            "이모지": emoji,
            "핵심한마디": f"{label_a}: {story_a[:30]} / {label_b}: {story_b[:30]}",
        })

    good_top3 = good_months[:3]
    bad_top3 = bad_months[:3]

    # 상/하반기 총평
    first_half = [m for m in monthly if m["절월"] <= 6]
    second_half = [m for m in monthly if m["절월"] > 6]

    def _half_summary(months_list: List[Dict], half_name: str) -> str:
        good_n = sum(1 for m in months_list if m["이모지"] == "💚")
        bad_n = sum(1 for m in months_list if m["이모지"] == "🔴")
        if good_n >= 3:
            return f"{half_name}: 함께 좋은 달이 많아 관계가 활발하게 발전하기 좋은 시기입니다."
        if bad_n >= 3:
            return f"{half_name}: 두 분 모두 어려운 달이 겹쳐 서로의 지지가 특히 중요한 시기입니다."
        if good_n >= 2:
            return f"{half_name}: 함께 순풍인 달이 있어 주요 결정을 그 타이밍에 맞추면 좋습니다."
        return f"{half_name}: 큰 기복 없이 무난하게 흐르는 시기입니다. 꾸준한 소통이 관건입니다."

    half1 = _half_summary(first_half, "상반기")
    half2 = _half_summary(second_half, "하반기")

    # 올해 주요 이슈 - 결혼/이별/재물 가능성
    # 관성합 or 도화 여부 (seowon에서 플래그 참조)
    marriage_flag = False
    conflict_flag = chong_a or chong_b
    for sew in [sew_a, sew_b]:
        tree = sew.get("출력_트리텍스트") or ""
        if "도화" in tree or "관성합" in tree or "결혼" in tree:
            marriage_flag = True

    올해_주요이슈 = {
        "결혼_동거_가능성": "관성합·도화 발동 신호 있음 — 올해 관계 진전의 기회가 생길 수 있습니다." if marriage_flag else "특별한 결혼·인연 발동 신호는 없습니다.",
        "갈등_주의": f"일지충 발동 주의 달: {bad_top3}절월 전후" if conflict_flag and bad_top3 else "뚜렷한 일지충 발동은 없습니다.",
        "함께_좋은_달_TOP3": [f"{m}절월" for m in good_top3] if good_top3 else ["특별히 두드러지는 달 없음"],
        "함께_주의할_달_TOP3": [f"{m}절월" for m in bad_top3] if bad_top3 else ["특별히 두드러지는 달 없음"],
    }

    return {
        "연도": current_year,
        "세운_간지": gz,
        f"{label_a}_세운": {
            "간지": sew_a.get("간지") or gz,
            "운세등급": grade_a,
            "별점": star_a,
            "세운_총평": (sew_a.get("세운_총평_한줄") or sew_a.get("이해_총평_한마디") or f"{current_year}년 {label_a}의 세운입니다."),
        },
        f"{label_b}_세운": {
            "간지": sew_b.get("간지") or gz,
            "운세등급": grade_b,
            "별점": star_b,
            "세운_총평": (sew_b.get("세운_총평_한줄") or sew_b.get("이해_총평_한마디") or f"{current_year}년 {label_b}의 세운입니다."),
        },
        "궁합_세운_분석": sew_couple_msg,
        "궁합_세운_등급": sew_compat,
        "올해_주요이슈": 올해_주요이슈,
        "월별_궁합": monthly,
        "상반기_총평": half1,
        "하반기_총평": half2,
        "올해_커플_종합조언": (
            f"올해 {current_year}년은 {sew_couple_msg} "
            f"상반기에는 {half1.split(':')[1].strip() if ':' in half1 else half1} "
            f"하반기에는 {half2.split(':')[1].strip() if ':' in half2 else half2}"
        ),
    }


# ── 3. 종합 점수 + 총평 ───────────────────────────────────────────────────────

def _score_stars(
    ilji: Dict[str, Any],
    ilgan: Dict[str, Any],
    cheon: Dict[str, Any],
    ohaeng: Dict[str, Any],
    yong_pair: Dict[str, Any],
    all_zhi: Dict[str, Any],
    sew_gh: Optional[Dict[str, Any]] = None,
) -> Tuple[int, int, int, int, int]:
    """인연, 갈등, 경제, 성격, 종합 별(1~5)."""
    tags = set(ilji.get("관계_표기") or [])
    hap_n = all_zhi.get("합_개수", 0)
    chong_n = all_zhi.get("충_개수", 0)

    bond = 3 + hap_n - chong_n
    if "육합" in tags:
        bond += 1
    if "충" in tags:
        bond -= 1
    if cheon.get("성립"):
        bond += 1
    y_a = (yong_pair.get("A가_느끼는_상대") or {}).get("등급", "보통")
    y_b = (yong_pair.get("B가_느끼는_상대") or {}).get("등급", "보통")
    if y_a == "최상" or y_b == "최상":
        bond += 1
    if y_a == "주의" and y_b == "주의":
        bond -= 1

    il_type = str(ilgan.get("유형") or "")
    if "생(" in il_type:
        bond += 1
    if "극(" in il_type:
        bond -= 1

    conflict = 2 + chong_n
    if "충" in tags:
        conflict += 1
    if "파" in tags or "해" in tags:
        conflict += 1
    if "형" in tags:
        conflict += 1
    if "극(" in il_type:
        conflict += 1
    if ohaeng.get("동일_과다_충돌후보"):
        conflict += 1

    econ = 3
    if "충" in tags:
        econ -= 1
    if cheon.get("성립"):
        econ += 1
    if "육합" in tags:
        econ += 1
    보완 = ohaeng.get("오행_보완_점수", 2)
    econ += max(0, 보완 - 2)
    if ohaeng.get("동일_과다_충돌후보"):
        econ -= 1
    if sew_gh and sew_gh.get("궁합_세운_등급") == "좋음":
        econ += 1

    pers = 3
    if il_type == "비화":
        pers += 1
    if "생(" in il_type:
        pers += 1
    if "극(" in il_type:
        pers -= 1
    if ohaeng.get("동일_과다_충돌후보"):
        pers -= 1

    bond = max(1, min(5, bond))
    conflict = max(1, min(5, conflict))
    econ = max(1, min(5, econ))
    pers = max(1, min(5, pers))
    overall_raw = (bond + econ + pers + (6 - conflict)) / 4.0
    overall = max(1, min(5, int(round(overall_raw))))
    return bond, conflict, econ, pers, overall


def _marriage_suitability(overall: int, conflict: int, bond: int) -> Tuple[str, str]:
    # bond가 4이상이거나 conflict가 적으면 최적으로 판정
    if overall >= 4 and (conflict <= 3 or bond >= 4):
        return "최적", "🏆 최적"
    if overall >= 3 and conflict <= 4:
        return "노력필요", "⭐ 노력필요"
    if overall >= 2:
        return "신중히", "⚠️ 신중히"
    return "재고권장", "❌ 재고권장"


def _build_strengths_challenges(
    ilji: Dict,
    ilgan: Dict,
    ohaeng: Dict,
    yong_pair: Dict,
    cheon: Dict,
    all_zhi: Dict,
    label_a: str,
    label_b: str,
) -> Tuple[List[str], List[str], str]:
    strengths: List[str] = []
    challenges: List[str] = []

    # 강점
    if "육합" in (ilji.get("관계_표기") or []):
        strengths.append(f"일지 육합 — 생활 리듬과 감성이 잘 맞는 천생연분 인연")
    if cheon.get("성립"):
        strengths.append(f"일간 천간합({cheon.get('표기','')}) — 천간 차원의 강한 끌림과 인연")
    if ohaeng.get("A가_부족_B가_보완") or ohaeng.get("B가_부족_A가_보완"):
        strengths.append("오행 보완 관계 — 서로의 부족한 기운을 채워주는 이상적 조합")
    if (yong_pair.get("A가_느끼는_상대") or {}).get("등급") == "최상":
        strengths.append(f"{label_b}가 {label_a}의 용신 — 에너지 균형에 최적인 파트너")
    if (yong_pair.get("B가_느끼는_상대") or {}).get("등급") == "최상":
        strengths.append(f"{label_a}가 {label_b}의 용신 — 에너지 균형에 최적인 파트너")
    if all_zhi.get("합_개수", 0) >= 2:
        strengths.append(f"8글자 지지 합이 {all_zhi['합_개수']}개 — 여러 자리에서 인연 신호 겹침")
    il_t = ilgan.get("유형", "")
    if "생(" in il_t:
        strengths.append("일간 생 관계 — 한쪽이 다른 쪽을 자연스럽게 돕고 성장시키는 구조")

    # 과제
    if "충" in (ilji.get("관계_표기") or []):
        challenges.append("일지 충 — 가치관·생활 리듬 차이를 대화로 조율하는 것이 핵심")
    if all_zhi.get("충_개수", 0) >= 2:
        challenges.append(f"8글자 지지 충이 {all_zhi['충_개수']}개 — 여러 자리 마찰, 역할 분담이 필요")
    if "극(" in il_t:
        challenges.append("일간 극 관계 — 주도·종속 패턴이 생기지 않도록 서로 존중하는 훈련 필요")
    if il_t == "비화":
        challenges.append("일간 비화 — 자존심·경쟁심이 부딪히지 않도록 공동 목표 설정 필요")
    if ohaeng.get("동일_과다_충돌후보"):
        challenges.append(f"동일 오행 과다({','.join(ohaeng['동일_과다_충돌후보'])}) — 같은 방향 고집으로 충돌 가능, 역할 분리 필요")
    if (yong_pair.get("A가_느끼는_상대") or {}).get("등급") == "주의":
        challenges.append(f"{label_b}가 {label_a}의 기신 방향 — 에너지 충돌 주의, 서로 배려 필요")
    if (yong_pair.get("B가_느끼는_상대") or {}).get("등급") == "주의":
        challenges.append(f"{label_a}가 {label_b}의 기신 방향 — 에너지 충돌 주의, 서로 배려 필요")

    # 형 관계도 과제에 추가
    if "형" in (ilji.get("관계_표기") or []) and not any("형" in c for c in challenges):
        challenges.append("일지 삼형 관계 — 서로의 원칙·규칙이 충돌할 수 있으니 유연성이 중요합니다.")
    # 과제가 부족할 때 일반 과제 추가
    if len(challenges) < 2:
        challenges.append("갈등을 쌓아두지 말고 그때그때 표현하는 소통 습관이 관계의 건강을 지킵니다.")
    if len(challenges) < 3:
        challenges.append("각자의 공간과 개인 시간을 존중하면 더욱 건강한 관계가 됩니다.")

    # 3개만
    strengths = strengths[:3] if strengths else ["서로를 향한 노력과 의지가 관계의 가장 큰 강점입니다."]
    challenges = challenges[:3] if challenges else ["뚜렷한 충돌 신호는 없으나 꾸준한 소통이 관계를 지킵니다."]

    # 핵심 조언
    if "충" in (ilji.get("관계_표기") or []) and "생(" in il_t:
        advice = "갈등은 성장의 연료입니다. 충돌 후 대화로 회복하는 루틴을 만들어 보세요."
    elif cheon.get("성립") and ohaeng.get("오행_보완_점수", 0) >= 3:
        advice = "천간합과 오행 보완이 함께 있어 잠재력이 큰 커플입니다. 서로의 강점을 인정하는 것이 출발점입니다."
    elif "극(" in il_t:
        advice = "주도권을 놓고 다투기보다 각자의 영역을 인정하고 역할을 명확히 하는 것이 관계의 핵심입니다."
    elif all_zhi.get("합_개수", 0) >= 2:
        advice = "인연의 씨앗이 많이 뿌려진 관계입니다. 일상의 작은 배려와 감사 표현으로 인연을 꽃피우세요."
    else:
        advice = "특별한 운명보다 매일의 선택이 관계를 만들어 갑니다. 서로의 다름을 존중하는 것이 핵심입니다."

    return strengths, challenges, advice


def build_narrative_story(
    ilji: Dict,
    ilgan: Dict,
    cheon: Dict,
    ohaeng: Dict,
    yong_pair: Dict,
    all_zhi: Dict,
    sipsin_gh: Dict,
    sew_gh: Optional[Dict],
    label_a: str,
    label_b: str,
) -> str:
    """5~7줄 스토리텔링 총평."""
    parts: List[str] = []

    # 일지 인연
    rel = ilji.get("관계_표기") or []
    if "육합" in rel:
        parts.append(
            f"두 분은 일지 육합으로 첫 만남부터 자연스러운 끌림이 있는 인연입니다."
        )
    elif "충" in rel:
        parts.append(
            f"두 분은 일지 충으로 가치관 차이가 뚜렷하지만 서로를 강하게 자극하는 불꽃형 커플입니다."
        )
    else:
        parts.append(
            f"두 분의 일지 관계는 {ilji.get('주_관계','중립')}로, {ilji.get('커플_유형','동반자형')} 성향의 커플입니다."
        )

    # 8글자 대조
    hap_n = all_zhi.get("합_개수", 0)
    chong_n = all_zhi.get("충_개수", 0)
    if hap_n > 0 or chong_n > 0:
        parts.append(
            f"8글자 전체 지지 대조에서 합이 {hap_n}개, 충이 {chong_n}개로 "
            + all_zhi.get("인연_강도_판정", "")
        )

    # 오행 보완
    fill_ab = ohaeng.get("A가_부족_B가_보완") or []
    fill_ba = ohaeng.get("B가_부족_A가_보완") or []
    if fill_ab and fill_ba:
        parts.append(
            f"오행적으로 {label_a}의 부족한 {'·'.join(fill_ab)} 기운을 {label_b}가 채워주고, "
            f"{label_b}의 부족한 {'·'.join(fill_ba)} 기운을 {label_a}가 불어넣어주는 "
            "서로를 완성시켜주는 보완형 커플입니다."
        )
    elif fill_ab:
        parts.append(
            f"{label_b}의 {','.join(fill_ab)} 기운이 {label_a}에게 부족한 부분을 채워주는 든든한 파트너입니다."
        )
    elif fill_ba:
        parts.append(
            f"{label_a}의 {','.join(fill_ba)} 기운이 {label_b}에게 부족한 부분을 채워주는 든든한 파트너입니다."
        )

    # 일간 관계
    il_t = ilgan.get("유형", "")
    if il_t and il_t != "기타":
        love_msg = ilgan.get("연애_해석", "")
        parts.append(
            f"일간은 {il_t} 관계로 {love_msg}"
        )

    # 천간합 또는 용신
    if cheon.get("성립"):
        parts.append(f"일간 {cheon.get('표기','')}이 있어 천간 차원의 강한 인연 신호가 함께 붙습니다.")
    else:
        y_a = (yong_pair.get("A가_느끼는_상대") or {}).get("등급", "보통")
        y_b = (yong_pair.get("B가_느끼는_상대") or {}).get("등급", "보통")
        if y_a == "최상" or y_b == "최상":
            parts.append("한쪽 또는 양쪽 모두 상대 일간이 자신의 용신과 맞아 에너지 면에서 긍정적인 조합입니다.")

    # 세운
    if sew_gh:
        cy = sew_gh.get("연도", datetime.date.today().year)
        sew_msg = sew_gh.get("궁합_세운_분석", "")
        if sew_msg:
            parts.append(f"{cy}년은 {sew_msg}")

    return "\n".join(parts)


# ── 원국 스냅샷 ───────────────────────────────────────────────────────────────

def pillar_snapshot(raw: Dict[str, Any], label: str) -> Dict[str, Any]:
    pillars = raw["pillars"]
    return {
        "표시_이름": label,
        "eight_char_string": raw.get("eight_char_string") or "",
        "양력": (raw.get("solar") or {}).get("label") or "",
        "음력": (raw.get("lunar") or {}).get("label") or "",
        "일간": raw.get("day_master") or "",
        "일간_한글": raw.get("day_master_kr") or "",
        "일간_오행": raw.get("day_master_element") or gj.element_of_stem(raw.get("day_master", "甲")),
        "주": {
            k: {
                "간": pillars[k]["gan"],
                "지": pillars[k]["zhi"],
                "간지": pillars[k]["pillar"],
            }
            for k in PILLAR_KEYS
        },
    }


# ── 메인 오케스트레이터 ───────────────────────────────────────────────────────

def analyze_goonghap_pair(
    *,
    raw_a: Dict[str, Any],
    raw_b: Dict[str, Any],
    counts_a: Dict[str, int],
    counts_b: Dict[str, int],
    yong_a: Dict[str, Any],
    yong_b: Dict[str, Any],
    label_a: str = "A",
    label_b: str = "B",
    gender_a: str = "female",
    gender_b: str = "male",
    current_year: Optional[int] = None,
) -> Dict[str, Any]:
    cy = current_year if current_year is not None else datetime.date.today().year
    pillars_a = raw_a["pillars"]
    pillars_b = raw_b["pillars"]
    dm_a = raw_a["day_master"]
    dm_b = raw_b["day_master"]
    z_a = pillars_a["day"]["zhi"]
    z_b = pillars_b["day"]["zhi"]

    # 각 분석
    ilji = analyze_ilji_relations(z_a, z_b)
    all_zhi = analyze_all_zhi(pillars_a, pillars_b)
    ohaeng = analyze_ohaeng_overlap(counts_a, counts_b, label_a, label_b)
    ilgan = analyze_ilgan_relation(dm_a, dm_b)
    sipsin_gh = analyze_sipsin_goonghap(dm_a, dm_b, label_a, label_b)
    cheon = analyze_cheon_gan_hap(dm_a, dm_b)
    yong_pair = analyze_yongsin_pair(yong_a, yong_b, dm_a, dm_b, label_a, label_b)
    sew_gh = analyze_sewoon_goonghap(
        raw_a, raw_b, counts_a, counts_b,
        gender_a, gender_b, cy, label_a, label_b
    )

    # 점수
    b_star, c_star, e_star, p_star, o_star = _score_stars(
        ilji, ilgan, cheon, ohaeng, yong_pair, all_zhi, sew_gh
    )

    bond_n, bond_s = _star_bar(float(b_star))
    conflict_n, conflict_s = _star_bar(float(c_star))
    econ_n, econ_s = _star_bar(float(e_star))
    pers_n, pers_s = _star_bar(float(p_star))
    overall_n, overall_s = _star_bar(float(o_star))
    heart_pct = min(100, max(5, int(round(overall_n / 5.0 * 100))))

    # 게이지 바
    bond_bar = _pct_bar(bond_n * 20)
    conflict_bar = _pct_bar(conflict_n * 20)
    econ_bar = _pct_bar(econ_n * 20)
    pers_bar = _pct_bar(pers_n * 20)
    overall_bar = _pct_bar(overall_n * 20)

    # 총평 + 강점/과제
    strengths, challenges, advice = _build_strengths_challenges(
        ilji, ilgan, ohaeng, yong_pair, cheon, all_zhi, label_a, label_b
    )
    narrative = build_narrative_story(
        ilji, ilgan, cheon, ohaeng, yong_pair, all_zhi, sipsin_gh, sew_gh, label_a, label_b
    )
    marriage_suit, marriage_badge = _marriage_suitability(overall_n, conflict_n, bond_n)
    heart_emoji = _heart_emoji(overall_n)

    return {
        "원국_나란히": {
            "A": pillar_snapshot(raw_a, label_a),
            "B": pillar_snapshot(raw_b, label_b),
        },
        "기본_일지": ilji,
        "전체_지지_대조": all_zhi,
        "오행_궁합": ohaeng,
        "일간_궁합": ilgan,
        "십신_궁합": sipsin_gh,
        "천간합": cheon,
        "용신_궁합": yong_pair,
        "종합_점수": {
            "인연_강도":    {"별점": bond_n,     "문자": bond_s,     "게이지": bond_bar},
            "갈등_가능성":  {"별점": conflict_n,  "문자": conflict_s,  "게이지": conflict_bar},
            "경제적_궁합":  {"별점": econ_n,      "문자": econ_s,      "게이지": econ_bar},
            "성격_궁합":    {"별점": pers_n,      "문자": pers_s,      "게이지": pers_bar},
            "전체_궁합":    {"별점": overall_n,   "문자": overall_s,   "게이지": overall_bar},
            "하트_게이지_퍼센트": heart_pct,
            "하트_이모지": heart_emoji,
        },
        "세운_궁합": sew_gh,
        "총평": narrative,
        "강점_3가지": strengths,
        "극복과제_3가지": challenges,
        "핵심조언": advice,
        "결혼적합도": marriage_suit,
        "결혼적합도_뱃지": marriage_badge,
        "참고": "학습·참고용 휴리스틱이며 실제 인연은 선택과 노력에 달려 있습니다.",
    }
