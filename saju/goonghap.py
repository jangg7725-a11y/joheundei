# -*- coding: utf-8 -*-
"""
두 명의 원국을 바탕으로 한 입문용 궁합 휴리스틱.

- 일지(日支) 충·육합·파·해
- 오행 분포 상 보완·과다 충돌
- 일간(日干) 오행 생·극·비화
- 일간 천간합(甲己·乙庚·丙辛·丁壬·戊癸)
- 용신 오행과 상대 일간 오행

정식 명리 학파·파종별 해석과 다를 수 있으며 참고용입니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from . import ganji as gj
from . import ohaeng as oh
from . import yongsin as ys

PILLAR_KEYS = ("year", "month", "day", "hour")
_ELEM_ORDER = ("목", "화", "토", "금", "수")

_CHONG_SET = {tuple(sorted(p)) for p in gj.CHONG_PAIRS}
_PO_SET = {tuple(sorted(p)) for p in gj.LIU_PO}
_HAI_SET = {tuple(sorted(p)) for p in gj.LIU_HAI}
_HE_SET = {tuple(sorted(p)) for p in gj.LIU_HE}

CHEON_GAN_HAP_LABEL: Dict[frozenset, str] = {
    frozenset(("甲", "己")): "甲己합(토화)",
    frozenset(("乙", "庚")): "乙庚합(금화)",
    frozenset(("丙", "辛")): "丙辛합(수화)",
    frozenset(("丁", "壬")): "丁壬합(목화)",
    frozenset(("戊", "癸")): "戊癸합(화화)",
}


def _pair_key(zhi_a: str, zhi_b: str) -> Tuple[str, str]:
    return tuple(sorted((zhi_a, zhi_b)))


def analyze_ilji_relations(zhi_a: str, zhi_b: str) -> Dict[str, Any]:
    """두 일지 지지 관계."""
    key = _pair_key(zhi_a, zhi_b)
    tags: List[str] = []
    if key in _CHONG_SET:
        tags.append("충")
    if key in _PO_SET:
        tags.append("파")
    if key in _HAI_SET:
        tags.append("해")
    if key in _HE_SET:
        tags.append("육합")

    if "육합" in tags:
        couple_type = "천생연분형"
        note = "일지 육합은 끌림·인연으로 읽기 쉬운 조합입니다."
    elif "충" in tags:
        couple_type = "갈등형"
        note = "일지 충은 가치관·생활 리듬에서 부딪침이 커질 수 있는 패턴입니다."
    elif "파" in tags or "해" in tags:
        couple_type = "서서히 멀어지는 형"
        note = "파·해는 불신·피로가 누적되기 쉬워 소통이 특히 중요합니다."
    else:
        couple_type = "중립"
        note = "일지만으로는 뚜렷한 충·합·파·해 패턴이 없습니다."

    return {
        "지지_A": zhi_a,
        "지지_B": zhi_b,
        "관계_표기": tags,
        "커플_유형": couple_type,
        "해설": note,
    }


def analyze_ohaeng_overlap(
    counts_a: Dict[str, int],
    counts_b: Dict[str, int],
) -> Dict[str, Any]:
    """오행 분포 비교·보완·과다 충돌 힌트."""
    dom_a = oh.dominant_weak_elements(counts_a)
    dom_b = oh.dominant_weak_elements(counts_b)
    strong_a: Set[str] = set(dom_a.get("strong") or [])
    weak_a: Set[str] = set(dom_a.get("weak") or [])
    strong_b: Set[str] = set(dom_b.get("strong") or [])
    weak_b: Set[str] = set(dom_b.get("weak") or [])

    fill_ab: List[str] = []
    fill_ba: List[str] = []
    for e in _ELEM_ORDER:
        if e in weak_a and e in strong_b:
            fill_ab.append(e)
        if e in weak_b and e in strong_a:
            fill_ba.append(e)

    total_a = sum(counts_a.get(e, 0) for e in _ELEM_ORDER) or 1
    total_b = sum(counts_b.get(e, 0) for e in _ELEM_ORDER) or 1
    avg_a = total_a / 5
    avg_b = total_b / 5

    clash_elems: List[str] = []
    for e in _ELEM_ORDER:
        if e in strong_a and e in strong_b:
            if counts_a.get(e, 0) >= avg_a + 0.01 and counts_b.get(e, 0) >= avg_b + 0.01:
                clash_elems.append(e)

    lines: List[str] = []
    if fill_ab:
        lines.append(f"A가 부족한 {','.join(fill_ab)}를 B의 강한 기운이 채워 줄 여지가 있습니다.")
    if fill_ba:
        lines.append(f"B가 부족한 {','.join(fill_ba)}를 A의 강한 기운이 채워 줄 여지가 있습니다.")
    if clash_elems:
        lines.append(
            f"둘 다 {','.join(clash_elems)} 기운이 과다하면 고집·충돌이 생기기 쉬우니 역할 분담이 필요합니다."
        )
    if not lines:
        lines.append("오행 과다·결핍 패턴이 비슷해 평행하게 가거나, 뚜렷한 보완 신호는 약합니다.")

    return {
        "A_강함": list(strong_a),
        "A_약함": list(weak_a),
        "B_강함": list(strong_b),
        "B_약함": list(weak_b),
        "상대가_내_결핍_보완": fill_ab,
        "내가_상대_결핍_보완": fill_ba,
        "동일_오행_과다_충돌_후보": clash_elems,
        "요약_문장": lines,
    }


def analyze_ilgan_relation(dm_a: str, dm_b: str) -> Dict[str, Any]:
    """두 일간 오행의 생·극·비화."""
    ea = gj.element_of_stem(dm_a)
    eb = gj.element_of_stem(dm_b)
    if ea == eb:
        return {
            "유형": "비화",
            "오행_A": ea,
            "오행_B": eb,
            "해설": "같은 오행으로 동등·경쟁과 동료애가 함께 나타나기 쉽습니다.",
        }
    if ys.GENERATE_MAP[ea] == eb:
        return {
            "유형": "생(A→B)",
            "오행_A": ea,
            "오행_B": eb,
            "해설": "A의 기운이 B를 생(生)하여 돕고 성장시키는 관계로 읽을 수 있습니다.",
        }
    if ys.GENERATE_MAP[eb] == ea:
        return {
            "유형": "생(B→A)",
            "오행_A": ea,
            "오행_B": eb,
            "해설": "B의 기운이 A를 생하여 돕는 관계로 읽을 수 있습니다.",
        }
    if ys.CONTROL_MAP[ea] == eb:
        return {
            "유형": "극(A→B)",
            "오행_A": ea,
            "오행_B": eb,
            "해설": "A가 B를 극(剋)하여 압박·통제 욕구가 드러나기 쉬우니 존중이 필요합니다.",
        }
    if ys.CONTROL_MAP[eb] == ea:
        return {
            "유형": "극(B→A)",
            "오행_A": ea,
            "오행_B": eb,
            "해설": "B가 A를 극하여 한쪽이 부담을 느낄 수 있어 균형이 중요합니다.",
        }
    return {"유형": "기타", "오행_A": ea, "오행_B": eb, "해설": "오행 관계를 단순 생극으로 분류하기 어렵습니다."}


def analyze_cheon_gan_hap(dm_a: str, dm_b: str) -> Dict[str, Any]:
    """일간 천간합 여부."""
    key = frozenset((dm_a, dm_b))
    if key not in ys.CHEON_GAN_HAP_ELEM:
        return {
            "성립": False,
            "화기_오행": None,
            "표기": None,
            "해설": "일간 천간합 패턴은 아닙니다.",
        }
    label = CHEON_GAN_HAP_LABEL.get(key, "천간합")
    elem = ys.CHEON_GAN_HAP_ELEM[key]
    return {
        "성립": True,
        "화기_오행": elem,
        "표기": label,
        "해설": f"{label}이 성립하면 인연·끌림이 강하게 부각되는 경우가 많습니다.",
    }


def _yongsin_match_line(my_yong: Dict[str, Any], partner_dm: str) -> Dict[str, Any]:
    pe = gj.element_of_stem(partner_dm)
    y_elem = my_yong.get("용신_오행") or ""
    hui = set(my_yong.get("희신") or [])
    gi = set(my_yong.get("기신") or [])
    if y_elem and pe == y_elem:
        grade = "최상"
        msg = "상대 일간 오행이 나의 용신과 같아 균형에 도움이 되기 쉬운 조합입니다."
    elif pe in hui:
        grade = "양호"
        msg = "상대 일간이 희신 방향과 맞아 긍정적 보완이 기대됩니다."
    elif pe in gi:
        grade = "주의"
        msg = "상대 일간이 기신 쪽에 가깝다 보니 생활 방식에서 마찰이 생기기 쉽습니다."
    else:
        grade = "보통"
        msg = "용신·기신과 직접 겹치지는 않으며 다른 원국 요소로 조율됩니다."
    return {"상대_일간_오행": pe, "등급": grade, "해설": msg}


def analyze_yongsin_pair(yong_a: Dict[str, Any], yong_b: Dict[str, Any], dm_a: str, dm_b: str) -> Dict[str, Any]:
    return {
        "A가_느끼는_상대": _yongsin_match_line(yong_a, dm_b),
        "B가_느끼는_상대": _yongsin_match_line(yong_b, dm_a),
    }


def _star_bar(n: float) -> Tuple[int, str]:
    v = max(1, min(5, int(round(n))))
    return v, "★" * v + "☆" * (5 - v)


def _score_stars(
    ilji: Dict[str, Any],
    ilgan: Dict[str, Any],
    cheon: Dict[str, Any],
    ohaeng: Dict[str, Any],
    yong_pair: Dict[str, Any],
) -> Tuple[int, int, int, int, int]:
    """인연, 갈등, 경제, 성격, 종합 별 개수(1~5)."""
    tags = set(ilji.get("관계_표기") or [])
    bond = 3
    if "육합" in tags:
        bond += 1
    if "충" in tags:
        bond -= 2
    if "파" in tags:
        bond -= 1
    if "해" in tags:
        bond -= 1
    if cheon.get("성립"):
        bond += 1
    y_a = yong_pair["A가_느끼는_상대"]["등급"]
    y_b = yong_pair["B가_느끼는_상대"]["등급"]
    if y_a == "최상" or y_b == "최상":
        bond += 1
    if y_a == "주의" or y_b == "주의":
        bond -= 1

    il_type = str(ilgan.get("유형") or "")
    if "생(" in il_type:
        bond += 1
    if "극(" in il_type:
        bond -= 1
    if il_type == "비화":
        bond += 1

    conflict = 2
    if "충" in tags:
        conflict += 2
    if "파" in tags:
        conflict += 1
    if "해" in tags:
        conflict += 1
    if "극(" in il_type:
        conflict += 1

    econ = 3
    if "충" in tags:
        econ -= 1
    if cheon.get("성립"):
        econ += 1
    if "육합" in tags:
        econ += 1
    if ohaeng.get("동일_오행_과다_충돌_후보"):
        econ -= 1
    if ohaeng.get("상대가_내_결핍_보완") or ohaeng.get("내가_상대_결핍_보완"):
        econ += 1

    pers = 3
    if il_type == "비화":
        pers += 1
    if "생(" in il_type:
        pers += 1
    if "극(" in il_type:
        pers -= 1
    if ohaeng.get("동일_오행_과다_충돌_후보"):
        pers -= 1

    bond = max(1, min(5, bond))
    conflict = max(1, min(5, conflict))
    econ = max(1, min(5, econ))
    pers = max(1, min(5, pers))

    overall_raw = (bond + econ + pers + (6 - conflict)) / 4.0
    overall = max(1, min(5, int(round(overall_raw))))
    return bond, conflict, econ, pers, overall


def build_summary_lines(
    ilji: Dict[str, Any],
    ilgan: Dict[str, Any],
    cheon: Dict[str, Any],
    ohaeng: Dict[str, Any],
    yong_pair: Dict[str, Any],
) -> str:
    parts: List[str] = []
    ct = ilji.get("커플_유형")
    rel = ilji.get("관계_표기") or []
    if "육합" in rel:
        parts.append("두 분은 일지 육합으로 첫 만남부터 강한 끌림이 있을 수 있는 인연입니다.")
    elif "충" in rel:
        parts.append("일지 충이 있어 가치관 차이를 조율하는 것이 과제로 남을 수 있습니다.")
    elif rel:
        parts.append(f"일지 관계는 {','.join(rel)}로 서서히 거리를 두기 쉬운 패턴일 수 있어 소통이 중요합니다.")
    else:
        parts.append("일지 관계는 중립에 가깝고 다른 주와 대운으로 보완됩니다.")

    if cheon.get("성립"):
        parts.append(f"일간 {cheon.get('표기')}이 있어 천간 차원의 인연 신호가 함께 붙습니다.")

    il_t = ilgan.get("유형")
    if il_t and il_t != "기타":
        parts.append(f"일간은 {il_t} 관계로 성격 궁합을 가늠할 수 있습니다.")

    clash = ohaeng.get("동일_오행_과다_충돌_후보") or []
    if clash:
        parts.append(f"같은 오행({','.join(clash)})이 과다하면 재물·생활 방식에서 충돌 여지가 있습니다.")

    if yong_pair["A가_느끼는_상대"]["등급"] == "최상" or yong_pair["B가_느끼는_상대"]["등급"] == "최상":
        parts.append("한쪽 또는 양쪽 모두 상대 일간이 자신의 용신과 맞아 균형 면에서 긍정적입니다.")

    return " ".join(parts).strip()


def pillar_snapshot(raw: Dict[str, Any], label: str) -> Dict[str, Any]:
    """UI용 원국 요약(JSON 직렬화 가능)."""
    pillars = raw["pillars"]
    return {
        "표시_이름": label,
        "eight_char_string": raw.get("eight_char_string") or "",
        "양력": raw.get("solar", {}).get("label") or "",
        "음력": raw.get("lunar", {}).get("label") or "",
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
) -> Dict[str, Any]:
    """두 명 원국·오행·용신 블록을 받아 궁합 패키지 생성."""
    pillars_a = raw_a["pillars"]
    pillars_b = raw_b["pillars"]
    dm_a = raw_a["day_master"]
    dm_b = raw_b["day_master"]
    z_a = pillars_a["day"]["zhi"]
    z_b = pillars_b["day"]["zhi"]

    ilji = analyze_ilji_relations(z_a, z_b)
    ohaeng = analyze_ohaeng_overlap(counts_a, counts_b)
    ilgan = analyze_ilgan_relation(dm_a, dm_b)
    cheon = analyze_cheon_gan_hap(dm_a, dm_b)
    yong_pair = analyze_yongsin_pair(yong_a, yong_b, dm_a, dm_b)

    b_star, c_star, e_star, p_star, o_star = _score_stars(ilji, ilgan, cheon, ohaeng, yong_pair)

    bond_n, bond_s = _star_bar(float(b_star))
    conflict_n, conflict_s = _star_bar(float(c_star))
    econ_n, econ_s = _star_bar(float(e_star))
    pers_n, pers_s = _star_bar(float(p_star))
    overall_n, overall_s = _star_bar(float(o_star))

    heart_pct = min(100, max(5, int(round(overall_n / 5.0 * 100))))

    summary = build_summary_lines(ilji, ilgan, cheon, ohaeng, yong_pair)

    return {
        "기본_일지": ilji,
        "오행_궁합": ohaeng,
        "일간_궁합": ilgan,
        "천간합": cheon,
        "용신_궁합": yong_pair,
        "종합_점수": {
            "인연_강도": {"별점": bond_n, "문자": bond_s},
            "갈등_가능성": {"별점": conflict_n, "문자": conflict_s},
            "경제적_궁합": {"별점": econ_n, "문자": econ_s},
            "성격_궁합": {"별점": pers_n, "문자": pers_s},
            "전체_궁합": {"별점": overall_n, "문자": overall_s},
            "하트_게이지_퍼센트": heart_pct,
        },
        "총평": summary,
        "원국_나란히": {
            "A": pillar_snapshot(raw_a, label_a),
            "B": pillar_snapshot(raw_b, label_b),
        },
        "참고": "학습·참고용 휴리스틱이며 실제 인연은 선택과 노력에 달려 있습니다.",
    }
