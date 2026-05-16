# -*- coding: utf-8 -*-
"""
월운(月運) — 절기 월(인월~축월) 기준 월간·월지 산출,
원국·세운과의 충파해합형·삼합 중첩·공망 등을 묶어 12절월 표를 만듭니다.

• 표시 「1월」~「12월」은 양력이 아니라 입춘부터 소한까지의 절월 순번입니다.
• 명리 파종·용신 해석은 참고용 휴리스틱입니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import ganji as gj
from . import jieqi_embedded as jq
from . import sewoon as sw
from . import sipsin as sp
from . import sinsal as sn
from .chung_pa_hae import ZHI_BODY
from .yongsin import CONTROL_MAP, RESOURCE_MAP

PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")

# 절월 순번 1 → 인월 … 12 → 축월 (각 해당 절 입후)
MONTH_SLOT_ZHI: Tuple[str, ...] = ("寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")

_MONTH_ELEM_HINT = {"목": "간·목", "화": "심장·혈압", "토": "비위", "금": "폐·피부", "수": "신장·불면"}

_MONTH_ELEM_BODY_LINE = {
    "목": "간·담·근육·관절·눈 피로",
    "화": "심장·소화·혈압·순환",
    "토": "비위·췌장·피부·당대사",
    "금": "폐·대장·기관지·피부",
    "수": "신장·방광·하체·불면",
}

_ELEM_CYCLE: Tuple[str, ...] = ("목", "화", "토", "금", "수")


def _wealth_element(dm_elem: str) -> str:
    i = _ELEM_CYCLE.index(dm_elem)
    return _ELEM_CYCLE[(i + 2) % 5]


def _rating_bar(n: int) -> str:
    n = max(1, min(5, n))
    return "★" * n + "☆" * (5 - n)


def _month_slot_first_stem_index(year_gan: str) -> int:
    """월두표에 따른 인월(첫 절월) 천간 인덱스 0~9."""
    return [2, 4, 6, 8, 0][gj.stem_index(year_gan) % 5]


def _term_parts(cal_year_key: int, term_idx: int) -> Tuple[int, int, int, int, int]:
    """내장 절기표 키 연도 기준: 소한(term_idx==11)은 다음 해 1월."""
    mon, day, hr, mn = jq.TERM_TWELVE_BY_YEAR[cal_year_key][term_idx]
    yr = cal_year_key + 1 if term_idx == 11 else cal_year_key
    return yr, mon, day, hr, mn


def _require_jie_year(cal_year: int) -> None:
    if cal_year not in jq.TERM_TWELVE_BY_YEAR:
        raise ValueError(f"jieqi_embedded 범위 밖 연도입니다(1900~2100): {cal_year}")


def slot_period_label(cal_year: int, slot_1_to_12: int) -> str:
    """절입 구간 문자열 (양력 일자)."""
    _require_jie_year(cal_year)
    if slot_1_to_12 < 1 or slot_1_to_12 > 12:
        raise ValueError("slot는 1~12 절월 순번입니다.")
    ys, ms, ds, _, _ = _term_parts(cal_year, slot_1_to_12 - 1)
    if slot_1_to_12 < 12:
        ye, me, de, _, _ = _term_parts(cal_year, slot_1_to_12)
    else:
        ye, me, de, _, _ = _term_parts(cal_year + 1, 0)
    return f"{ys}-{ms:02d}-{ds:02d} ~ {ye}-{me:02d}-{de:02d}"


def month_pillar_for_slot(solar_year: int, slot_1_to_12: int) -> Dict[str, Any]:
    """
    해당 **세운 연도**(양력 연 번호, 입춘 전까지도 같은 연 번호 키 사용)의 절월 ``slot`` 간지.

    ``slot`` 1 = 입춘 후 인월 … 12 = 소한 후 축월.
    """
    if slot_1_to_12 < 1 or slot_1_to_12 > 12:
        raise ValueError("slot는 1~12입니다.")
    _require_jie_year(solar_year)
    yinfo = sw.yearly_pillar_for_solar_year(solar_year)
    yg = yinfo["gan"]
    mz = MONTH_SLOT_ZHI[slot_1_to_12 - 1]
    sg_idx = (_month_slot_first_stem_index(yg) + slot_1_to_12 - 1) % 10
    sg = gj.STEMS[sg_idx]
    pillar = sg + mz
    jie_name = jq.JIE_TWELVE_NAMES_KR[slot_1_to_12 - 1]
    return {
        "세운연도": solar_year,
        "절월번호": slot_1_to_12,
        "절기명": jie_name,
        "월지": mz,
        "월간": sg,
        "월주간지": pillar,
        "월주한글표기": gj.pillar_label_kr(sg, mz),
        "낭음": gj.nayin_for_pillar(pillar),
        "구간_양력": slot_period_label(solar_year, slot_1_to_12),
        "세운간지": yinfo["pillar"],
        "세운천간": yinfo["gan"],
        "세운지지": yinfo["zhi"],
    }


def _xing_pair(a: str, b: str) -> Optional[str]:
    if a == b and a in gj.XING_ZI_BRANCHES:
        return "자형"
    pair = {a, b}
    if pair <= gj.XING_SAN_INSAM and len(pair) == 2:
        return "인사신 삼형"
    if pair <= gj.XING_SAN_GOJI and len(pair) == 2:
        return "축술미 삼형"
    if pair == gj.XING_SANG_JAMYO:
        return "자묘 상형"
    return None


def _native_branch_relations(mon_zhi: str, pillars: dict) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {"충": [], "파": [], "해": [], "형": [], "육합": []}
    for pk in PILLAR_KEYS:
        nz = pillars[pk]["zhi"]
        pos = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}[pk]
        body = ZHI_BODY.get(nz, "")
        if sw.branch_chong(mon_zhi, nz):
            out["충"].append({"궁": pk, "위치": pos, "글자": f"{mon_zhi}{nz}", "신체": body})
        if sw.branch_po(mon_zhi, nz):
            out["파"].append({"궁": pk, "위치": pos, "글자": f"{mon_zhi}×{nz}", "신체": body})
        if sw.branch_hai(mon_zhi, nz):
            out["해"].append({"궁": pk, "위치": pos, "글자": f"{mon_zhi}×{nz}", "신체": body})
        xt = _xing_pair(mon_zhi, nz)
        if xt:
            out["형"].append({"궁": pk, "위치": pos, "유형": xt, "글자": f"{mon_zhi}{nz}", "신체": body})
        if sw.branch_liu_he(mon_zhi, nz):
            out["육합"].append({"궁": pk, "위치": pos, "글자": f"{mon_zhi}{nz}", "신체": body})
    return out


def _triple_union_zhis(sew_zhi: str, mon_zhi: str, pillars: dict) -> Set[str]:
    return {sew_zhi, mon_zhi, *[pillars[pk]["zhi"] for pk in PILLAR_KEYS]}


def _san_he_analysis(all_zhis: Set[str]) -> Tuple[List[str], bool]:
    notes: List[str] = []
    complete = False
    for tri, label in gj.SAN_HE_GROUPS:
        inter = tri & all_zhis
        if tri <= all_zhis:
            complete = True
            notes.append(f"✅ 삼합완성({label}): 세운·월운·원국에 {''.join(sorted(tri))} 축이 모두 포진.")
        elif len(inter) == 2:
            notes.append(f"반합 성향({label}): {''.join(sorted(inter))}만 모여·결실 전후 움직임.")
    return notes, complete


def _dual_chong_native(sew_zhi: str, mon_zhi: str, pillars: dict) -> Tuple[bool, List[str]]:
    """원국 지지 중 세운·월운과 동시에 충에 걸리는 궁."""
    hits: List[str] = []
    for pk in PILLAR_KEYS:
        nz = pillars[pk]["zhi"]
        if sw.branch_chong(sew_zhi, nz) and sw.branch_chong(mon_zhi, nz):
            lab = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}[pk]
            hits.append(f"{lab}({nz})")
    return bool(hits), hits


def _fuyin_month(sew_zhi: str, mon_zhi: str) -> bool:
    return sew_zhi == mon_zhi


def _kongwang_hit(mon_zhi: str, pillars: dict) -> bool:
    k1, k2 = sn._xunkong_for_pillar(pillars["day"]["pillar"])  # type: ignore[attr-defined]
    kd, kd2 = sn._xunkong_for_pillar(pillars["year"]["pillar"])  # type: ignore[attr-defined]
    return mon_zhi in {k1, k2, kd, kd2}


def _energy_notes(day_master: str, month_gan: str, month_zhi: str) -> Dict[str, Any]:
    dm_el = gj.element_of_stem(day_master)
    officer_el = CONTROL_MAP[dm_el]
    wealth_el = _wealth_element(dm_el)
    resource_el = RESOURCE_MAP[dm_el]

    elems_month = {gj.element_of_stem(month_gan), gj.element_of_branch(month_zhi)}
    lines: List[str] = []

    sheng_zhu = resource_el in elems_month or dm_el in elems_month
    geuk_patch = officer_el in elems_month
    wealth_boost = wealth_el in elems_month
    officer_boost = officer_el in elems_month

    if sheng_zhu:
        lines.append("생조·비겁 방향 오행이 들어와 활동·학습 에너지가 붙기 쉽습니다.")
    if geuk_patch:
        lines.append("관살(극) 방향이 강해져 규범·스트레스·건강 긴장을 의식합니다.")
    if wealth_boost:
        lines.append("재성 오행 기운이 두드러져 재물·사업 타이밍으로 연결합니다.")
    if officer_boost:
        lines.append("관성 오행이 강조되어 직장·계약·승진 변수가 커질 수 있습니다.")

    career = 3 + (1 if officer_boost else 0) + (1 if sheng_zhu else 0) - (2 if geuk_patch else 0)
    career = max(1, min(5, career))
    wealth = 3 + (2 if wealth_boost else 0) - (1 if geuk_patch else 0)
    wealth = max(1, min(5, wealth))
    health = 4 - (2 if geuk_patch else 0) - (1 if officer_boost else 0)
    health = max(1, min(5, health))

    return {
        "생조우위": sheng_zhu,
        "극받음우위": geuk_patch,
        "재성강화": wealth_boost,
        "관성강화": officer_boost,
        "설명": lines,
        "직업별점": career,
        "재물별점": wealth,
        "건강별점": health,
        "직업바": _rating_bar(career),
        "재물바": _rating_bar(wealth),
        "건강바": _rating_bar(health),
    }


def _month_five_tier(
    luck: str,
    energy: Dict[str, Any],
    nat_rel: Dict[str, List[Dict[str, str]]],
) -> Tuple[str, int]:
    """절월 길흉을 5단계(대길~대흉)와 1~5 점수로 정규화."""
    avg_e = (energy["직업별점"] + energy["재물별점"] + energy["건강별점"]) / 3
    c_count = sum(len(nat_rel.get(k, [])) for k in ("충", "파", "해"))
    he_count = len(nat_rel.get("육합", []))

    if luck == "대흉우려":
        return ("대흉", 1)
    if luck == "대길우려":
        return ("대길", 5)
    if luck == "약흉":
        return ("흉", 2) if avg_e <= 2 else ("평", 3)

    if c_count >= 4:
        return ("흉", 2)
    if c_count >= 3 and avg_e < 3:
        return ("흉", 2)
    if c_count >= 2 and avg_e <= 2:
        return ("흉", 2)
    if he_count >= 2 and avg_e >= 4:
        return ("길", 4)
    if avg_e >= 4 and c_count <= 1:
        return ("길", 4)
    if avg_e >= 3 and he_count and c_count <= 2:
        return ("길", 4)
    if avg_e <= 2:
        return ("흉", 2)
    return ("평", 3)


def _jie_transition_note(solar_year: int, slot_1_to_12: int) -> str:
    """해당 절월 시작 절입일 전후 ±3일 특별 주의 문구."""
    _require_jie_year(solar_year)
    if slot_1_to_12 < 1 or slot_1_to_12 > 12:
        return ""
    ti = slot_1_to_12 - 1
    jie_name = jq.JIE_TWELVE_NAMES_KR[ti]
    yr, mon, day, _, _ = _term_parts(solar_year, ti)
    return (
        f"{jie_name} 입기 전후 약 3일({yr}-{mon:02d}-{day:02d} 전후): 절기 변환기로 수면·교통·컨디션 변동에 특별히 유의하세요."
    )


def _gi_elements(yong: Optional[Dict[str, Any]]) -> List[str]:
    if not yong:
        return []
    raw = yong.get("기신_오행")
    if isinstance(raw, str) and raw.strip():
        return [x.strip() for x in raw.replace("·", "/").split("/") if x.strip()]
    gl = yong.get("기신") or []
    return [str(x) for x in gl if x]


def _month_story_dynamic(
    *,
    slot_1_to_12: int,
    mon_zhi: str,
    five_tier: str,
    severe_overlap: bool,
    san_done: bool,
    kong: bool,
    sip_mg: str,
    flags: Dict[str, bool],
    nat_rel: Dict[str, List[Dict[str, str]]],
    yong: Optional[Dict[str, Any]] = None,
) -> str:
    """절월·용신·원국 관계에 따라 월별 문장을 분기한다."""
    slot = max(1, min(12, int(slot_1_to_12)))
    mel = gj.element_of_branch(mon_zhi)
    yong_el = str((yong or {}).get("용신_오행") or "").strip()
    gi_els = _gi_elements(yong)

    if severe_overlap:
        return (
            "이달은 숨 고르기가 필요한 달입니다. 새 일을 시작하기보다 "
            "기존 관계·건강을 점검하고 방어적으로 가져가세요."
        )

    if san_done:
        pool = [
            "기운이 한데 모이는 달입니다. 협력과 성과를 넓히되 과욕만 줄이면 속도를 낼 수 있습니다.",
            f"{mon_zhi}월에 합·삼합 기운이 모여 협업·네트워크에서 성과가 나기 쉽습니다.",
            f"절월 {slot}·{mon_zhi}에 모인 기운을 활용해 공동 프로젝트를 밀어보세요.",
        ]
        return pool[(slot - 1) % len(pool)]

    chung = nat_rel.get("충") or []
    if chung:
        row = chung[0]
        gz = str(row.get("글자", "")).replace("×", "")
        pos = row.get("위치", "")
        sip_hint = f" {sip_mg} 궁" if sip_mg else ""
        pool = [
            f"{gz}충이 발동하는 달입니다.{sip_hint} 관련 변화·이동에 주의하세요.",
            f"월운 {mon_zhi}와 원국 {pos} 축이 충입니다. 결정은 한 박자 늦추고 몸부터 챙기세요.",
            f"충 기운이 드는 {slot}절월입니다. 이동·계약·관계 갈등을 미리 조율하세요.",
        ]
        return pool[(slot - 1) % len(pool)]

    if yong_el and mel == yong_el:
        pool = [
            f"용신 {yong_el} 기운이 들어오는 달입니다. 새로운 시작과 도전에 좋습니다.",
            f"{yong_el} 기운이 살아나는 달입니다. 미뤄둔 일을 한 걸음 진행하기 좋습니다.",
            f"용신 {yong_el}과 절월 {mon_zhi}({slot}월)이 맞물려 실행력이 붙기 쉬운 달입니다.",
        ]
        return pool[(slot - 1) % len(pool)]

    for ge in gi_els:
        if ge == mel:
            pool = [
                f"기신 {mel} 기운이 강해지는 달입니다. 중요한 결정은 다음 달로 미루세요.",
                f"{mel} 기운이 부담으로 올 수 있는 달입니다. 지출·갈등·무리한 확장을 줄이세요.",
                f"기신 {mel}과 맞닿는 {mon_zhi}월입니다. 방어·정리·휴식을 우선하세요.",
            ]
            return pool[(slot - 1) % len(pool)]

    if kong:
        return (
            "공망 기운이 드는 달입니다. 약속·문서는 재확인하고 "
            "허무함을 정리·휴식의 기회로 쓰세요."
        )

    if five_tier in ("대길", "길"):
        pool = [
            "순풍에 가까운 흐름입니다. 준비된 일은 밀고, 약속은 신뢰를 쌓는 방향으로 가세요.",
            f"{mel} 기운이 순조로운 달입니다. 작은 성과를 기록해 두면 후반 추진이 쉬워집니다.",
            f"절월 {slot}·{mon_zhi}는 기회 달입니다. 과욕만 줄이면 속도를 낼 수 있습니다.",
        ]
        return pool[(slot - 1) % len(pool)]

    if five_tier in ("대흉", "흉"):
        pool = [
            "변수가 튀기 쉬운 달입니다. 결정은 한 박자 늦추고 몸의 신호를 우선 반영하세요.",
            f"{mel} 기운이 불안정할 수 있는 달입니다. 방어·점검 중심으로 가져가세요.",
            f"흉 기운이 부각되는 {mon_zhi}월입니다. 확장보다 버퍼·건강을 두껍게 유지하세요.",
        ]
        return pool[(slot - 1) % len(pool)]

    he = nat_rel.get("육합") or []
    if he:
        gz = str(he[0].get("글자", ""))
        return f"육합 {gz} 기운이 살아나는 달입니다. 협력·인연에서 문이 열릴 수 있습니다."

    if flags.get("세운월운_복음"):
        return (
            f"세운·월운이 같은 {mon_zhi}로 겹치는 달입니다. "
            "과열을 줄이고 휴식 루틴을 고정해 두세요."
        )

    if sip_mg in ("식신", "상관"):
        pool = [
            "표현·창작 에너지가 살아나는 달입니다. 말과 글로 관계 윤활을 챙기세요.",
            f"식상 기운이 살아나는 {mon_zhi}월입니다. 배움·콘텐츠·소통에 시간을 쓰면 좋습니다.",
        ]
        return pool[(slot - 1) % len(pool)]

    neutral_pool = [
        "큰 변화 없이 꾸준히 가는 달입니다. 일상 리듬을 유지하는 것이 중요합니다.",
        f"{mel} 기운이 은은한 달입니다. 급한 일만 줄이면 균형을 지키기 좋습니다.",
        f"절월 {slot}·{mon_zhi} 흐름은 안정적입니다. 작은 정리·점검이 다음 달을 돕습니다.",
        f"{mel} 기운으로 루틴을 다지기 좋은 달입니다. 무리한 확장은 보류하세요.",
    ]
    return neutral_pool[(slot - 1) % len(neutral_pool)]


def _month_action_guidelines(five_tier: str, severe: bool, kong: bool) -> Dict[str, Any]:
    bad_tier = five_tier in ("대흉", "흉") or severe
    good = ["규칙 수면", "가벼운 운동", "가계부·저축 점검", "신뢰할 사람과 짧은 동선 미팅"]
    avoid: List[str] = []
    if bad_tier:
        avoid.extend(["대형 계약·연대보증", "단기 투자·레버리지", "이사·개업 등 무리한 시작"])
    if kong:
        avoid.append("말로만 된 약속·추상적 합의")
    if severe:
        avoid.extend(["수술·시술(급하지 않다면 연기 검토)", "야간 장거리 운전"])
    if five_tier in ("대길", "길") and not severe:
        good.extend(["건강검진 예약", "인간관계 정리·감사 표현"])
    else:
        good.insert(0, "건강검진·혈압·혈당 점검")
    if not avoid:
        avoid.append("과음·과로로 컨디션 붕괴")
    return {
        "하면_좋음": good[:8],
        "피할것": avoid[:8],
        "하면_좋음_안내": {"제목": "✅ 이달 하면 좋은 것", "항목": good[:8]},
        "피할것_안내": {"제목": "❌ 이달 피해야 할 것", "항목": avoid[:8]},
    }


def _month_health_pack(mon_zhi: str, solar_year: int, slot: int, body_line: str) -> Dict[str, Any]:
    el = gj.element_of_branch(mon_zhi)
    base = _MONTH_ELEM_BODY_LINE.get(el, _MONTH_ELEM_HINT.get(el, el))
    return {
        "월지_오행": el,
        "신체_우선_참고": base,
        "원국_충파해_신체": body_line,
        "절기전환_특별주의": _jie_transition_note(solar_year, slot),
    }


def _month_wealth_timing(day_master: str, mon_gan: str, energy: Dict[str, Any], severe: bool, sip_mg: str) -> Dict[str, Any]:
    gain_ok = bool(energy.get("재성강화") and sip_mg in ("편재", "정재") and not severe)
    spend_warn = bool(
        sip_mg == "겁재"
        or energy.get("극받음우위")
        or int(energy.get("재물별점", 3)) <= 2
        or severe
    )
    gain_msg = (
        "재성 오행이 받쳐줘 현금·실적 회수(수금) 타이밍으로 보기 좋습니다. 입금 확인·미수 정리를 우선하세요."
        if gain_ok
        else "수금은 평년과 비슷합니다. 확정 전까지 지출 선행은 줄이세요."
    )
    spend_msg = (
        "겁재·극받음·월운 긴장으로 지출·보증·충동구매에 유의하세요."
        if spend_warn
        else "지출 리스크는 상대적으로 낮습니다. 고정비만 관리하면 무난합니다."
    )
    return {"수금_유리": gain_ok, "수금_메모": gain_msg, "지출_주의": spend_warn, "지출_메모": spend_msg}


def _sewoon_year_five(se_pack: Dict[str, Any]) -> Tuple[str, int]:
    """``analyze_sewoon_year`` 결과 → 5단계."""
    s = int(se_pack.get("별점") or 3)
    lw = se_pack.get("운세등급") or "보통"
    if se_pack.get("반음_전지충"):
        s = max(1, s - 2)
    elif se_pack.get("반음_과격"):
        s = max(1, s - 1)

    if lw == "길운":
        if s >= 5:
            return ("대길", 5)
        if s >= 4:
            return ("길", 4)
        return ("평", 3)
    if lw == "흉운":
        if s <= 1:
            return ("대흉", 1)
        if s <= 2:
            return ("흉", 2)
        return ("평", 3)
    if s >= 4:
        return ("길", 4)
    if s <= 2:
        return ("흉", 2)
    return ("평", 3)


def _sewoon_wol_overlap(sw_score: int, mo_score: int) -> Dict[str, Any]:
    sw_bad = sw_score <= 2
    sw_good = sw_score >= 4
    mo_bad = mo_score <= 2
    mo_good = mo_score >= 4
    if sw_bad and mo_bad:
        return {
            "유형": "이중 흉월",
            "배지": "🔴🔴",
            "설명": "세운과 월운이 함께 흐름을 깎아 내리는 구간으로 리스크가 겹칩니다.",
        }
    if sw_bad and mo_good:
        return {
            "유형": "세운 흉을 월운이 완화",
            "배지": "🟡",
            "설명": "연중 압박이 있어도 이달 월운이 완충해 주는 패턴입니다.",
        }
    if sw_good and mo_bad:
        return {
            "유형": "이달만 주의",
            "배지": "🟠",
            "설명": "세운은 순조로우나 이달만 변수가 튀니 방어적으로 운용하세요.",
        }
    if sw_good and mo_good:
        return {
            "유형": "최상의 달",
            "배지": "✅✅",
            "설명": "세운·월운이 함께 받쳐 주어 추진과 회복 모두 유리합니다.",
        }
    return {
        "유형": "중립·혼재",
        "배지": "⚪",
        "설명": "길흉이 섞인 달입니다. 기회는 취하되 리스크 관리를 병행하세요.",
    }


def _annual_wol_flow(months_enriched: List[Dict[str, Any]]) -> Dict[str, Any]:
    def avg_score(slots: Sequence[int]) -> float:
        xs = [m["길흉점수"] for m in months_enriched if int(m["절월번호"]) in set(slots)]
        return sum(xs) / len(xs) if xs else 3.0

    first_half = list(range(1, 7))
    second_half = list(range(7, 13))
    a1 = avg_score(first_half)
    a2 = avg_score(second_half)

    def half_line(label: str, a: float) -> str:
        if a >= 4.2:
            return f"{label}은 전반적으로 순풍에 가까운 흐름입니다."
        if a >= 3.4:
            return f"{label}은 무난·완만한 편입니다. 기회와 방어를 반씩 섞어 가면 좋습니다."
        if a >= 2.5:
            return f"{label}은 변수가 있는 편입니다. 건강·재무 버퍼를 두껍게 유지하세요."
        return f"{label}은 기복이 큽니다. 확장보다 내실·점검 중심으로 가져가세요."

    sorted_best = sorted(months_enriched, key=lambda m: (-int(m["길흉점수"]), int(m["절월번호"])))
    sorted_worst = sorted(months_enriched, key=lambda m: (int(m["길흉점수"]), int(m["절월번호"])))

    def brief(m: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "절월번호": m["절월번호"],
            "월주간지": m["월주간지"],
            "길흉등급_5단계": m["길흉등급_5단계"],
            "핵심스토리": m.get("월별_핵심스토리") or "",
        }

    return {
        "상반기_총평": half_line("상반기(1~6절월)", a1),
        "하반기_총평": half_line("하반기(7~12절월)", a2),
        "최고의달_TOP3": [brief(m) for m in sorted_best[:3]],
        "최악의달_TOP3": [brief(m) for m in sorted_worst[:3]],
    }


def analyze_wolwoon_month(
    day_master: str,
    pillars: dict,
    solar_year: int,
    slot_1_to_12: int,
    *,
    sewoon_zhi_override: Optional[str] = None,
    yong: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    단일 절월(slot 1~12) 월운 분석.

    ``sewoon_zhi_override``: 세운 지지를 바꿔 재평가할 때 사용.
    """
    base = month_pillar_for_slot(solar_year, slot_1_to_12)
    sew_zhi = sewoon_zhi_override if sewoon_zhi_override is not None else base["세운지지"]
    mon_zhi = base["월지"]
    mon_gan = base["월간"]

    nat_rel = _native_branch_relations(mon_zhi, pillars)
    all_z = _triple_union_zhis(sew_zhi, mon_zhi, pillars)
    san_notes, san_done = _san_he_analysis(all_z)

    dual_chong, dual_chong_where = _dual_chong_native(sew_zhi, mon_zhi, pillars)
    fuyin_sw_mw = _fuyin_month(sew_zhi, mon_zhi)
    kong = _kongwang_hit(mon_zhi, pillars)

    overlap_notes: List[str] = []
    overlap_notes.extend(san_notes)

    any_sew_chong = any(sw.branch_chong(sew_zhi, pillars[pk]["zhi"]) for pk in PILLAR_KEYS)
    severe_overlap = dual_chong or (fuyin_sw_mw and any_sew_chong)

    if dual_chong:
        overlap_notes.append(f"🔴 세운·월운 동시충 → {','.join(dual_chong_where)} 이중충 극대화.")
    if fuyin_sw_mw:
        overlap_notes.append(f"🔴 세운지·월운지 동일({sew_zhi}) 복음·중첩으로 과열.")
    if kong:
        overlap_notes.append("⚠️ 공망(일·년 순공 기준): 허무·속 빈 결실 구간.")

    sip_mg = sp.classify_sipsin(day_master, mon_gan)

    energy = _energy_notes(day_master, mon_gan, mon_zhi)

    luck = "보통"
    if severe_overlap:
        luck = "대흉우려"
    elif san_done:
        luck = "대길우려"
    elif kong:
        luck = "약흉"

    grade_word = {"대길우려": "길", "대흉우려": "흉", "약흉": "약흉", "보통": "보통"}[luck]

    flags = {
        "삼합완성": san_done,
        "세운월운_동시충": dual_chong,
        "세운월운_복음": fuyin_sw_mw,
        "공망달": kong,
    }

    body_hints = sorted(
        {r["신체"] for rows in nat_rel.values() for r in rows if r.get("신체")},
        key=lambda x: x,
    )
    body_line = "·".join(body_hints[:4]) if body_hints else "특정 부위 과제 없음"

    summary_parts: List[str] = []
    if nat_rel["육합"]:
        summary_parts.append(f"{nat_rel['육합'][0]['글자']} 육합")
    if san_notes and not san_done:
        summary_parts.append(san_notes[0].replace("반합 성향", "").strip())
    if sip_mg:
        summary_parts.append(f"월간십신 {sip_mg}")

    icons: List[str] = []
    if dual_chong or (fuyin_sw_mw and any_sew_chong):
        icons.append("🔴")
    if san_done:
        icons.append("✅")
    if kong:
        icons.append("⚠️")

    five_name, five_score = _month_five_tier(luck, energy, nat_rel)
    story = _month_story_dynamic(
        slot_1_to_12=slot_1_to_12,
        mon_zhi=mon_zhi,
        five_tier=five_name,
        severe_overlap=severe_overlap,
        san_done=san_done,
        kong=kong,
        sip_mg=sip_mg,
        flags=flags,
        nat_rel=nat_rel,
        yong=yong,
    )
    actions = _month_action_guidelines(five_name, severe_overlap, kong)
    health_pack = _month_health_pack(mon_zhi, solar_year, slot_1_to_12, body_line)
    wealth_tim = _month_wealth_timing(day_master, mon_gan, energy, severe_overlap, sip_mg)

    return {
        **base,
        "월간십신": sip_mg,
        "원국_충파해합형": nat_rel,
        "세운지지_실사용": sew_zhi,
        "중첩분석": overlap_notes,
        "중첩플래그": flags,
        "월별에너지": energy,
        "길흉등급": grade_word,
        "길흉판정": luck,
        "길흉등급_5단계": five_name,
        "길흉점수": five_score,
        "월별_핵심스토리": story,
        "월별_행동지침": actions,
        "건강_월별": health_pack,
        "재물_타이밍": wealth_tim,
        "건강부위메모": body_line,
        "한줄요약": " · ".join(summary_parts) if summary_parts else "특이 패턴 없음",
        "특이아이콘": icons,
    }


def format_month_box_row(month_row: Dict[str, Any], *, width: int = 37) -> List[str]:
    """표 한 절월 블록(상하 테두리 제외)."""
    icons = "".join(month_row.get("특이아이콘") or [])
    top_left = f"{month_row['절월번호']}월({month_row['월주간지']})"
    jie = month_row["절기명"]
    mz = month_row["월지"]
    line_a = f"{top_left} {jie}후 · {mz}월"
    if icons:
        line_a = f"{icons} {line_a}"
    overlap = month_row.get("중첩분석") or []
    if overlap:
        line_b = " | ".join(overlap[:2])
    else:
        line_b = month_row["한줄요약"]
    en = month_row["월별에너지"]
    line_c = f"💼{en['직업바']} 💰{en['재물바']} 🏥{body_hint_short(month_row)}"
    pad = width - 2

    def clip(s: str) -> str:
        return s if len(s) <= pad else s[: pad - 1] + "…"

    return [
        f"│ {clip(line_a):<{pad}} │",
        f"│ {clip(line_b):<{pad}} │",
        f"│ {clip(line_c):<{pad}} │",
    ]


def body_hint_short(month_row: Dict[str, Any]) -> str:
    el = gj.element_of_branch(month_row["월지"])
    base_h = _MONTH_ELEM_HINT.get(el, el)
    bh = month_row.get("건강부위메모") or ""
    if bh and bh != "특정 부위 과제 없음":
        frag = bh.split("·")[0].strip()
        if frag:
            return f"{base_h}+{frag}"
    return base_h


def build_year_ascii_table(month_rows: List[Dict[str, Any]], solar_year: int, *, width: int = 37) -> str:
    rule_top = "┌" + "─" * width + "┐"
    rule_mid = "├" + "─" * width + "┤"
    rule_bot = "└" + "─" * width + "┘"
    lines = [
        f"{solar_year}년 월운표:",
        rule_top,
    ]
    for i, row in enumerate(month_rows):
        lines.extend(format_month_box_row(row, width=width))
        if i < len(month_rows) - 1:
            lines.append(rule_mid)
    lines.append(rule_bot)
    return "\n".join(lines)


def wolwoon_year_pack(
    day_master: str,
    pillars: dict,
    solar_year: int,
    *,
    gender: str = "남",
    counts: Optional[Dict[str, int]] = None,
    yong: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    months = [
        analyze_wolwoon_month(day_master, pillars, solar_year, s, yong=yong)
        for s in range(1, 13)
    ]
    se_pack = sw.analyze_sewoon_year(day_master, pillars, gender, solar_year, counts=counts)
    sw_name, sw_score = _sewoon_year_five(se_pack)

    for m in months:
        mo_score = int(m["길흉점수"])
        ov = _sewoon_wol_overlap(sw_score, mo_score)
        m["세운_월운_중첩"] = ov
        m["세운_길흉_5단계"] = sw_name
        m["세운_길흉점수"] = sw_score
        badge = (ov.get("배지") or "").strip()
        head = f"{badge} {ov['유형']}: {ov['설명']}".strip()
        m["중첩분석"] = [head] + list(m.get("중첩분석") or [])

    table_text = build_year_ascii_table(months, solar_year)
    alerts = {
        "🔴경고": [m["절월번호"] for m in months if m["길흉판정"] == "대흉우려"],
        "✅기회": [m["절월번호"] for m in months if m["중첩플래그"]["삼합완성"]],
        "⚠️공망": [m["절월번호"] for m in months if m["중첩플래그"]["공망달"]],
    }
    flow = _annual_wol_flow(months)
    return {
        "세운연도": solar_year,
        "절월_안내": "1월=입춘 후 인월 … 12월=소한 후 축월 (양력 1~12월과 다름).",
        "월별": months,
        "출력_표텍스트": table_text,
        "특별주의": alerts,
        "연간_월운_요약": flow,
        "세운연간_참고": {
            "간지": se_pack.get("간지"),
            "운세등급": se_pack.get("운세등급"),
            "길흉_5단계": sw_name,
            "길흉점수": sw_score,
        },
    }
