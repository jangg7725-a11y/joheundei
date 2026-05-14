# -*- coding: utf-8 -*-
"""
용신·희신·기신·구신·한신 도출 (입문용 규칙 기반).

월지 득령·생조·십신 비율로 신강/신약을 가늠하고,
신강에는 설기(식상)·소설(재)·극제(관) 순,
신약에는 인성·비겁을 우선 고려합니다.
종격·화격 등 특수 패턴은 단순 휴리스틱으로 표시합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from . import ganji as gj
from . import sipsin as sp

MONTH_COMMAND = {
    "寅": "목",
    "卯": "목",
    "辰": "토",
    "巳": "화",
    "午": "화",
    "未": "토",
    "申": "금",
    "酉": "금",
    "戌": "토",
    "亥": "수",
    "子": "수",
    "丑": "토",
}

CONTROL_MAP = {"목": "금", "화": "수", "토": "목", "금": "화", "수": "토"}
GENERATE_MAP = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
RESOURCE_MAP = {"목": "수", "화": "목", "토": "화", "금": "토", "수": "금"}

BIBING_INSTRINSIC: Set[str] = {"비견", "겁재", "편인", "정인"}
SHISHANG_CAIGUAN: Set[str] = {"식신", "상관", "편재", "정재", "편관", "정관"}

CHEON_GAN_HAP_ELEM: Dict[frozenset, str] = {
    frozenset(("甲", "己")): "토",
    frozenset(("乙", "庚")): "금",
    frozenset(("丙", "辛")): "수",
    frozenset(("丁", "壬")): "목",
    frozenset(("戊", "癸")): "화",
}

ELEMENT_META = {
    "목": {"색상": "청·녹계열", "방위": "동(震·巽)", "직업": "교육·출판·임업·섬유·디자인"},
    "화": {"색상": "적·주황", "방위": "남(離)", "직업": "에너지·조명·요식·미디어·IT"},
    "토": {"색상": "황·베이지", "방위": "중앙·남서·동북", "직업": "부동산·건설·농축산·중개"},
    "금": {"색상": "백·은회색·금속", "방위": "서(兌·乾)", "직업": "금속·법무·군경·의료기기"},
    "수": {"색상": "흑·남색", "방위": "북(坎)", "직업": "유통·무역·해양·음료·데이터"},
}

YONG_JONG_PLACEHOLDER: Dict[str, Any] = {
    "성립": False,
    "추종_오행": "—",
    "설명": "종격 패턴은 두드러지지 않습니다.",
}
YONG_HWA_PLACEHOLDER: Dict[str, Any] = {
    "성립": False,
    "합_간": "—",
    "화기_오행": "—",
    "설명": "원국 천간 화격 패턴은 두드러지지 않습니다.",
}


def _uniq(xs: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _all_target_gans(pillars: dict) -> List[str]:
    gans: List[str] = []
    for k in sp.PILLAR_KEYS:
        gans.append(pillars[k]["gan"])
        zhi = pillars[k]["zhi"]
        gans.extend(gj.jijanggan_ordered(zhi))
    return gans


def _deoling_score(dm_elem: str, month_zhi: str) -> Tuple[int, str]:
    cmd = MONTH_COMMAND.get(month_zhi, "토")
    if cmd == dm_elem:
        return 38, f"월지가 일간({dm_elem})과 같은 기운으로 득령에 가깝습니다."
    if GENERATE_MAP[cmd] == dm_elem:
        return 26, f"월지({cmd})가 일간({dm_elem})을 생하는 방향이라 뿌리가 살아나기 쉽습니다."
    if RESOURCE_MAP[cmd] == dm_elem:
        return 14, f"월지가 일간의 인성 방향과 맞닿아 보조 득지가 있습니다."
    return 0, "월지와 일간의 계절 적합도는 평이하거나 다소 엇나가는 편입니다."


def _sipsin_ratio(day_master: str, pillars: dict) -> Tuple[float, float, str]:
    bib = 0
    scg = 0
    for gan in _all_target_gans(pillars):
        if gan == day_master:
            continue
        name = sp.classify_sipsin(day_master, gan)
        if name in BIBING_INSTRINSIC:
            bib += 1
        elif name in SHISHANG_CAIGUAN:
            scg += 1
    total = bib + scg
    if total == 0:
        return 0.5, 0.5, "비겁·인성과 식재관 비교 표본이 부족합니다."
    return bib / total, scg / total, f"비겁·인성 계열 {bib} vs 식상·재·관 계열 {scg}"


def _support_element_ratio(counts: Dict[str, int], dm_elem: str) -> Tuple[float, str]:
    total = sum(counts.values()) or 1
    res = RESOURCE_MAP[dm_elem]
    sup = counts.get(dm_elem, 0) + counts.get(res, 0)
    ratio = sup / total
    return ratio, f"일간·인성({dm_elem}+{res}) 비중 약 {ratio * 100:.1f}%"


def _strength_verdict(
    deoling_pts: int,
    bib_ratio: float,
    support_r: float,
) -> Tuple[str, float]:
    """신강/신약/중화 종합 점수."""
    score = (
        deoling_pts
        + min(32, bib_ratio * 32)
        + min(30, support_r * 30)
    )
    if score >= 58:
        return "신강", score
    if score <= 38:
        return "신약", score
    return "중화", score


def _dominant_element_share(counts: Dict[str, int]) -> Tuple[str, float]:
    total = sum(counts.values()) or 1
    best_e, best_v = max(counts.items(), key=lambda kv: kv[1])
    return best_e, best_v / total


def _jong_gyeok(counts: Dict[str, int], dm_elem: str) -> Optional[Dict[str, Any]]:
    dom, share = _dominant_element_share(counts)
    total = sum(counts.values()) or 1
    dm_share = counts.get(dm_elem, 0) / total
    if share >= 0.44 and dm_share <= 0.16 and dom != dm_elem:
        return {
            "성립": True,
            "추종_오행": dom,
            "설명": "한 오행 비중이 높고 일간 편재가 약해 종격(從格) 성향으로 그 강한 오행을 따르는 해석이 가능합니다.",
        }
    return None


def _hwa_gyeok(day_master: str, pillars: dict) -> Optional[Dict[str, Any]]:
    dm = day_master
    for k in sp.PILLAR_KEYS:
        if k == "day":
            continue
        g = pillars[k]["gan"]
        fs = frozenset((dm, g))
        if fs in CHEON_GAN_HAP_ELEM:
            elem = CHEON_GAN_HAP_ELEM[fs]
            return {
                "성립": True,
                "합_간": f"{dm}{g}",
                "화기_오행": elem,
                "설명": "원국 천간합이 성립해 화기(化气) 방향을 용신 참고에 더합니다.",
            }
    return None


def _gisin_weakest_elements(counts: Dict[str, int], exclude: Set[str]) -> List[str]:
    """구신: 상대적으로 작용이 약한 오행."""
    items = sorted(counts.items(), key=lambda kv: kv[1])
    out = [e for e, _ in items if e not in exclude][:2]
    return out


def analyze_yongsin(
    pillars: dict,
    day_master: str,
    counts: Dict[str, int],
) -> Dict[str, Any]:
    dm_elem = gj.element_of_stem(day_master)
    month_zhi = pillars["month"]["zhi"]

    deoling_pts, deoling_note = _deoling_score(dm_elem, month_zhi)
    bib_r, scg_r, sipsin_note = _sipsin_ratio(day_master, pillars)
    sup_r, sup_note = _support_element_ratio(counts, dm_elem)

    verdict, score = _strength_verdict(deoling_pts, bib_r, sup_r)

    output_e = GENERATE_MAP[dm_elem]
    wealth_e = GENERATE_MAP[output_e]
    officer_e = CONTROL_MAP[dm_elem]
    resource_e = RESOURCE_MAP[dm_elem]

    jong = _jong_gyeok(counts, dm_elem)
    hwa = _hwa_gyeok(day_master, pillars)

    yongsin_elem: str
    yongsin_reason_parts: List[str] = []
    huisin: List[str] = []
    gisin: List[str] = []
    hansin: List[str] = []
    gusin: List[str] = []

    if jong and jong["성립"]:
        yongsin_elem = jong["추종_오행"]
        yongsin_reason_parts.append(jong["설명"])
        huisin = _uniq([GENERATE_MAP[yongsin_elem], RESOURCE_MAP[yongsin_elem]])
        gisin = _uniq([CONTROL_MAP[yongsin_elem], dm_elem])
        hansin = [wealth_e]
        gusin = _gisin_weakest_elements(counts, {yongsin_elem})
    elif hwa and hwa["성립"]:
        yongsin_elem = hwa["화기_오행"]
        yongsin_reason_parts.append(hwa["설명"])
        yongsin_reason_parts.append(f"기본 강약은 {verdict}로 식상·재·관 중심에서 화기 {yongsin_elem}을 우선합니다.")
        if verdict == "신강":
            huisin = _uniq([wealth_e, officer_e])
            gisin = _uniq([resource_e, dm_elem])
            hansin = [officer_e]
        else:
            huisin = _uniq([dm_elem, output_e])
            gisin = _uniq([officer_e])
            hansin = [wealth_e]
        gusin = _gisin_weakest_elements(counts, {yongsin_elem, dm_elem})
    elif verdict == "신강":
        yongsin_elem = output_e
        yongsin_reason_parts.append(
            "신강으로 보아 설기(食神·傷官)로 기운을 살피는 것을 우선합니다."
        )
        huisin = _uniq([wealth_e, officer_e])
        gisin = _uniq([resource_e, dm_elem])
        hansin = [officer_e]
        gusin = _gisin_weakest_elements(counts, {output_e, wealth_e})
    elif verdict == "신약":
        yongsin_elem = resource_e
        yongsin_reason_parts.append(
            "신약으로 보아 생조하는 인성(正印·偏印)을 우선 용신으로 봅니다."
        )
        huisin = _uniq([dm_elem, output_e])
        gisin = _uniq([officer_e, wealth_e])
        hansin = [wealth_e]
        gusin = _gisin_weakest_elements(counts, {resource_e, dm_elem})
    else:
        yongsin_elem = resource_e
        yongsin_reason_parts.append(
            "중화에 가까워 인성·관성 균형 가운데 인성 쪽을 기본 용신 후보로 둡니다."
        )
        huisin = _uniq([output_e, dm_elem])
        gisun_alt = [officer_e, wealth_e]
        gisin = _uniq(gisun_alt)
        hansin = [officer_e]
        gusin = _gisin_weakest_elements(counts, set())

    yongsin_reason_parts.extend([deoling_note, sup_note, sipsin_note])

    meta = ELEMENT_META.get(yongsin_elem, {})

    yong_line = f"용신: {yongsin_elem} ({yongsin_reason_parts[0]})"
    hui_line = f"희신: {', '.join(huisin)}"
    gi_line = f"기신: {', '.join(gisin)} (과다하거나 세력이 맞붙으면 조심)"

    return {
        "일간_오행": dm_elem,
        "월지": month_zhi,
        "월령_주기": MONTH_COMMAND.get(month_zhi),
        "득령_판단": deoling_note,
        "생조_비중_설명": sup_note,
        "비겁인성_비율": round(bib_r * 100, 1),
        "식재관_비율": round(scg_r * 100, 1),
        "십신_비교_설명": sipsin_note,
        "강약_점수": round(score, 1),
        "일간_강약": verdict,
        "종격_휴리스틱": jong if jong else YONG_JONG_PLACEHOLDER,
        "화격_휴리스틱": hwa if hwa else YONG_HWA_PLACEHOLDER,
        "용신_오행": yongsin_elem,
        "용신_색상_방위_직업": meta,
        "희신": huisin,
        "기신": gisin,
        "구신": gusin,
        "한신": hansin,
        "출력_문장": {
            "용신": yong_line,
            "희신": hui_line,
            "기신": gi_line,
        },
        "yongsin_hint": [yongsin_elem],
        "huisin_hint": huisin,
        "gisin_hint": gisin,
        "notes": _uniq(yongsin_reason_parts + [deoling_note]),
        "disclaimer": "파종·대운·월령 입춘 시각에 따라 용신은 달라질 수 있습니다. 본 결과는 학습용 단순 규칙입니다.",
    }


def _analyze_counts_only(
    counts: Dict[str, int],
    day_master: str,
    month_zhi: str,
) -> Dict[str, Any]:
    """pillars 없을 때: 월지·오행 분포만으로 근사."""
    dm_elem = gj.element_of_stem(day_master)
    deoling_pts, deoling_note = _deoling_score(dm_elem, month_zhi)
    sup_r, sup_note = _support_element_ratio(counts, dm_elem)
    bib_proxy = min(0.92, max(0.08, sup_r))
    verdict, score = _strength_verdict(deoling_pts, bib_proxy, sup_r)
    output_e = GENERATE_MAP[dm_elem]
    wealth_e = GENERATE_MAP[output_e]
    officer_e = CONTROL_MAP[dm_elem]
    resource_e = RESOURCE_MAP[dm_elem]

    jong = _jong_gyeok(counts, dm_elem)

    yongsin_reason_parts: List[str] = []
    huisin: List[str] = []
    gisin: List[str] = []
    hansin: List[str] = []
    gusin: List[str] = []

    if jong and jong["성립"]:
        yongsin_elem = jong["추종_오행"]
        yongsin_reason_parts.append(jong["설명"])
        huisin = _uniq([GENERATE_MAP[yongsin_elem], RESOURCE_MAP[yongsin_elem]])
        gisin = _uniq([CONTROL_MAP[yongsin_elem], dm_elem])
        hansin = [wealth_e]
        gusin = _gisin_weakest_elements(counts, {yongsin_elem})
    elif verdict == "신강":
        yongsin_elem = output_e
        yongsin_reason_parts.append("신강으로 보아 설기(食神·傷官)를 우선합니다.")
        huisin = _uniq([wealth_e, officer_e])
        gisin = _uniq([resource_e, dm_elem])
        hansin = [officer_e]
        gusin = _gisin_weakest_elements(counts, {output_e, wealth_e})
    elif verdict == "신약":
        yongsin_elem = resource_e
        yongsin_reason_parts.append("신약으로 보아 인성 생조를 우선합니다.")
        huisin = _uniq([dm_elem, output_e])
        gisin = _uniq([officer_e, wealth_e])
        hansin = [wealth_e]
        gusin = _gisin_weakest_elements(counts, {resource_e, dm_elem})
    else:
        yongsin_elem = resource_e
        yongsin_reason_parts.append("중화에 가깝게 인성을 기본 용신 후보로 둡니다.")
        huisin = _uniq([output_e, dm_elem])
        gisin = _uniq([officer_e, wealth_e])
        hansin = [officer_e]
        gusin = _gisin_weakest_elements(counts, set())

    sipsin_note = "(원국 지장간 미포함 근사)"
    yongsin_reason_parts.extend([deoling_note, sup_note, sipsin_note])

    meta = ELEMENT_META.get(yongsin_elem, {})
    yong_line = f"용신: {yongsin_elem} ({yongsin_reason_parts[0]})"
    hui_line = f"희신: {', '.join(huisin)}"
    gi_line = f"기신: {', '.join(gisin)} (과다하거나 세력이 맞붙으면 조심)"

    return {
        "일간_오행": dm_elem,
        "월지": month_zhi,
        "월령_주기": MONTH_COMMAND.get(month_zhi),
        "득령_판단": deoling_note,
        "생조_비중_설명": sup_note,
        "비겁인성_비율": round(bib_proxy * 100, 1),
        "식재관_비율": round((1 - bib_proxy) * 100, 1),
        "십신_비교_설명": sipsin_note,
        "강약_점수": round(score, 1),
        "일간_강약": verdict,
        "종격_휴리스틱": jong if jong else YONG_JONG_PLACEHOLDER,
        "화격_휴리스틱": YONG_HWA_PLACEHOLDER,
        "용신_오행": yongsin_elem,
        "용신_색상_방위_직업": meta,
        "희신": huisin,
        "기신": gisin,
        "구신": gusin,
        "한신": hansin,
        "출력_문장": {"용신": yong_line, "희신": hui_line, "기신": gi_line},
        "yongsin_hint": [yongsin_elem],
        "huisin_hint": huisin,
        "gisin_hint": gisin,
        "notes": _uniq(yongsin_reason_parts),
        "disclaimer": "파종·대운·월령 입춘 시각에 따라 용신은 달라질 수 있습니다. 본 결과는 학습용 단순 규칙입니다.",
    }


def suggest_useful_gods(
    counts: Dict[str, int],
    day_master: str,
    month_zhi: str,
    *,
    pillars: Optional[dict] = None,
) -> Dict[str, Any]:
    if pillars is None:
        return _analyze_counts_only(counts, day_master, month_zhi)
    return analyze_yongsin(pillars, day_master, counts)
