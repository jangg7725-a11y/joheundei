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


def _score_band_text(verdict: str, score: float) -> str:
    if verdict == "신약":
        if score <= 28:
            return "매우 신약 (28점 이하) — 혼자 버티기보다 도움·휴식이 꼭 필요한 편"
        return "신약 (38점 이하) — 힘이 부족해 부담이 쌓이기 쉬운 편"
    if verdict == "신강":
        if score >= 72:
            return "매우 신강 (72점 이상) — 기운이 넘쳐 조절·배출이 중요한 편"
        return "신강 (58점 이상) — 스스로 밀고 나가기 쉬운 편"
    if score <= 44:
        return "중화·약한 쪽 (39~44점) — 상황에 따라 신약처럼 보일 때가 많음"
    if score >= 52:
        return "중화·강한 쪽 (52~57점) — 상황에 따라 신강처럼 보일 때가 많음"
    return "중화 (39~57점) — 신강·신약 사이, 때에 따라 기운이 오르내림"


def _phenomena_for_verdict(verdict: str, score: float, dm_elem: str) -> Dict[str, Any]:
    """판단별 생활 속 현상·주의·대처."""
    resource = RESOURCE_MAP[dm_elem]
    output = GENERATE_MAP[dm_elem]
    wealth = GENERATE_MAP[output]
    officer = CONTROL_MAP[dm_elem]

    if verdict == "신약":
        traits = [
            "혼자 모든 일을 떠맡으면 금방 지치고, 몸·마음이 먼저 신호(피로·불면·소화)를 보냅니다.",
            "큰 결정·이직·투자·대출을 한꺼번에 하면 부담이 커지기 쉽습니다.",
            "주변의 도움·멘토·가족 지원, 또는 학습·자격(인성) 쪽에서 힘이 붙습니다.",
            f"기운을 보태 주는 방향은 「{resource}」(인성)·「{dm_elem}」(비겁) 오행에 가깝습니다.",
            f"한꺼번에 몰아오는 「{officer}」(관살)·「{wealth}」(재성) 기운이 강한 해·월에는 특히 조심하세요.",
        ]
        tips = [
            "무리한 확장보다 체력·수면·루틴을 먼저 챙기세요.",
            "혼자 끙끙대지 말고, 믿을 수 있는 사람에게 역할을 나누세요.",
            f"색·소품·방향에서 {resource}·{dm_elem} 기운(용신·희신)을 가볍게 보강하는 것도 참고가 됩니다.",
        ]
        sewoon_hint = (
            f"세운에 {resource}·{dm_elem} 기운이 오면 힘이 붙고, "
            f"{officer}·{wealth}가 과하면 일·돈·책임이 무거워질 수 있습니다."
        )
    elif verdict == "신강":
        traits = [
            "의지·추진력이 강해, 한 번 방향을 잡으면 밀고 나가기 쉽습니다.",
            "남의 말보다 내 판단을 믿는 편이라, 고집·독주·과로로 이어질 수 있습니다.",
            "에너지가 넘치면 말·행동이 앞서거나, 관계에서 부딪침이 생기기 쉽습니다.",
            f"기운을 빼 주는(설기) 방향은 「{output}」(식상), 일을 벌이는 쪽은 「{wealth}」(재성)입니다.",
            f"「{resource}」·「{dm_elem}」이 또 강해지면 더 고집·피로·부담이 쌓일 수 있습니다.",
        ]
        tips = [
            "일을 더 벌리기보다, 표현·운동·창작 등으로 기운을 한 번 흘려보내세요.",
            "혼자 결정만 하지 말고, 한 번 더 검토할 상대를 두세요.",
            f"용신 {output}·재성 {wealth} 방향의 일·직업·취미에 에너지를 쓰면 균형이 맞기 쉽습니다.",
        ]
        sewoon_hint = (
            f"세운에 {output}·{wealth}가 오면 일이 풀리고, "
            f"{resource}·{dm_elem}이 과하면 답답함·부담·고집이 커질 수 있습니다."
        )
    else:
        traits = [
            "신강·신약 어느 한쪽으로 치우치지 않아, 환경·대운·세운에 따라 기운이 오르내립니다.",
            "좋을 때는 균형 잡힌 판단이 가능하고, 불리할 때는 갑자기 지치거나 답답해질 수 있습니다.",
            "한 해·한 달의 오행만으로 운이 좌우되는 느낌이 큽니다.",
            f"기본 용신 후보는 인성 「{resource}」 쪽을 두고, 세운·대운을 함께 봅니다.",
        ]
        tips = [
            "세운표에서 ‘유리·주의’ 표시가 바뀌는 해를 기준으로 계획을 조절하세요.",
            "극단적인 일(올인 투자·무리한 이직)은 피하고, 중간 속도를 유지하세요.",
        ]
        sewoon_hint = "아래 세운별 해설에서 매년 유리·주의를 확인하세요."

    return {
        "현상_특징": traits,
        "생활_조언": tips,
        "세운_읽는_법": sewoon_hint,
    }


def _build_strength_detail(
    verdict: str,
    score: float,
    dm_elem: str,
    *,
    bib_pct: float,
    scg_pct: float,
    deoling_note: str,
    sup_note: str,
    sipsin_note: str,
) -> Dict[str, Any]:
    phen = _phenomena_for_verdict(verdict, score, dm_elem)
    band = _score_band_text(verdict, score)
    score_expl = (
        f"강약 점수 {score}점 = 월령 득력(최대 38) + 비겁·인성 비중(최대 32) + "
        f"일간·인성 오행 비중(최대 30)을 합친 값입니다. "
        f"58점 이상은 신강, 38점 이하는 신약, 그 사이는 중화로 봅니다. "
        f"현재는 「{band}」입니다."
    )
    verdict_summary = {
        "신약": (
            f"일간({dm_elem}) 힘이 약한 편(신약)입니다. "
            "혼자 버티기보다 보호·학습·협력이 들어올 때 살아나기 쉽고, "
            "관살·재성이 몰리는 시기에는 피로·책임·돈 문제가 무거워질 수 있습니다."
        ),
        "신강": (
            f"일간({dm_elem}) 힘이 강한 편(신강)입니다. "
            "스스로 밀고 나가기 쉽지만, 기운이 넘치면 고집·과로·관계 마찰이 생기기 쉽습니다. "
            "식상·재성으로 기운을 쓰고 배출하는 것이 균형에 맞습니다."
        ),
        "중화": (
            f"일간({dm_elem})이 신강·신약 사이(중화)에 가깝습니다. "
            "원국만으로는 한쪽으로 치우치지 않아, 세운·대운에 따라 체감이 달라질 수 있습니다."
        ),
    }.get(verdict, "")

    return {
        "판단_요약": verdict_summary,
        "점수_구간": band,
        "점수_해설": score_expl,
        "현상_특징": phen["현상_특징"],
        "생활_조언": phen["생활_조언"],
        "세운_읽는_법": phen["세운_읽는_법"],
        "산출_근거": {
            "득령": deoling_note,
            "생조": sup_note,
            "십신": sipsin_note,
            "비겁인성_퍼센트": bib_pct,
            "식재관_퍼센트": scg_pct,
        },
    }


def _rate_elem_for_strength(
    verdict: str,
    elem: str,
    dm_elem: str,
    yong_elem: str,
    huisin: List[str],
    gisin: List[str],
) -> str:
    """세운 오행이 원국 강약에 유리한지 단순 등급."""
    resource = RESOURCE_MAP[dm_elem]
    output = GENERATE_MAP[dm_elem]
    wealth = GENERATE_MAP[output]
    officer = CONTROL_MAP[dm_elem]
    hui_set = set(huisin or [])
    gi_set = set(gisin or [])

    if elem == yong_elem or elem in hui_set:
        return "유리"
    if elem in gi_set:
        return "주의"

    if verdict == "신약":
        if elem in (resource, dm_elem):
            return "유리"
        if elem in (officer, wealth):
            return "주의"
        if elem == output:
            return "보통"
        return "보통"
    if verdict == "신강":
        if elem in (output, wealth):
            return "유리"
        if elem in (resource, dm_elem):
            return "주의"
        if elem == officer:
            return "보통"
        return "보통"
    # 중화
    if elem in (resource, dm_elem, output):
        return "보통"
    if elem in (officer, wealth):
        return "주의"
    return "보통"


def _merge_elem_rates(a: str, b: str) -> str:
    if "주의" in (a, b):
        return "주의"
    if a == "유리" and b == "유리":
        return "유리"
    if a == "유리" or b == "유리":
        return "보통"
    return "보통"


def _sewoon_year_strength_line(
    verdict: str,
    year: int,
    pillar: str,
    gan_elem: str,
    zhi_elem: str,
    rate: str,
    *,
    is_center: bool,
) -> Tuple[str, str]:
    """(한줄, 상세) 반환."""
    yr = f"{year}년"
    tag = "【올해】" if is_center else yr
    pillar_s = pillar or f"{gan_elem}/{zhi_elem}"

    if rate == "유리":
        one = f"{tag} {pillar_s} — 힘이 붙기 쉬운 해"
        if verdict == "신약":
            detail = (
                f"{yr} 세운 {pillar_s}은(는) 비겁·인성·용신 쪽 기운이 살아나 "
                f"체력·멘토·학습·협력에서 도움을 받기 쉽습니다. "
                f"무리한 확장보다 기반을 다지기 좋은 시기로 보세요."
            )
        elif verdict == "신강":
            detail = (
                f"{yr} 세운 {pillar_s}은(는) 식상·재성 쪽으로 기운이 흘러 "
                f"일·표현·수입·성과를 내기 좋은 해입니다. "
                f"다만 과로·말실수만 조절하세요."
            )
        else:
            detail = (
                f"{yr} 세운 {pillar_s}은(는) 균형에 맞는 기운이 와 "
                f"판단·협력·일 진행이 비교적 순조롭습니다."
            )
    elif rate == "주의":
        one = f"{tag} {pillar_s} — 부담·소모가 큰 해"
        if verdict == "신약":
            detail = (
                f"{yr} 세운 {pillar_s}은(는) 관살·재성·기신 쪽이 강해 "
                f"책임·돈·경쟁·압박이 한꺼번에 몰릴 수 있습니다. "
                f"건강·수면·무리한 계약을 특히 조심하세요."
            )
        elif verdict == "신강":
            detail = (
                f"{yr} 세운 {pillar_s}은(는) 인성·비겁이 또해져 "
                f"고집·답답함·부담·과로가 쌓이기 쉽습니다. "
                f"일을 더 벌리기보다 정리·배출·휴식이 필요합니다."
            )
        else:
            detail = (
                f"{yr} 세운 {pillar_s}은(는) 기신 쪽이 두드러져 "
                f"갑자기 지치거나 마찰이 생기기 쉬운 해입니다. 속도를 줄이세요."
            )
    else:
        one = f"{tag} {pillar_s} — 보통, 환경 따라 달라짐"
        detail = (
            f"{yr} 세운 {pillar_s}은(는) 강약만으로 극단적이지 않습니다. "
            f"합충·신살·대운과 함께 보시고, 무리한 올인은 피하세요."
        )
    return one, detail


def build_sewoon_strength_series(
    yong_report: Dict[str, Any],
    day_master: str,
    sewoon_nearby: Sequence[Dict[str, Any]],
    *,
    center_year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """세운 ±범위 각 연도의 신강·신약 관점 해설."""
    verdict = yong_report.get("일간_강약") or "중화"
    score = float(yong_report.get("강약_점수") or 0)
    dm_elem = yong_report.get("일간_오행") or gj.element_of_stem(day_master)
    yong_elem = yong_report.get("용신_오행") or ""
    huisin = list(yong_report.get("희신") or [])
    gisin = list(yong_report.get("기신") or [])

    out: List[Dict[str, Any]] = []
    for item in sewoon_nearby:
        year = int(item.get("year") or item.get("연도") or 0)
        gan = item.get("gan") or ""
        zhi = item.get("zhi") or ""
        pillar = item.get("pillar") or f"{gan}{zhi}"
        if not gan or not zhi:
            continue
        ge = gj.element_of_stem(gan)
        ze = gj.element_of_branch(zhi)
        rg = _rate_elem_for_strength(verdict, ge, dm_elem, yong_elem, huisin, gisin)
        rz = _rate_elem_for_strength(verdict, ze, dm_elem, yong_elem, huisin, gisin)
        rate = _merge_elem_rates(rg, rz)
        is_center = center_year is not None and year == center_year
        one, detail = _sewoon_year_strength_line(
            verdict, year, pillar, ge, ze, rate, is_center=is_center
        )
        out.append(
            {
                "연도": year,
                "간지": pillar,
                "천간_오행": ge,
                "지지_오행": ze,
                "천간_등급": rg,
                "지지_등급": rz,
                "종합_등급": rate,
                "한줄": one,
                "상세": detail,
                "기준년": is_center,
            }
        )
    return out


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

    strength_detail = _build_strength_detail(
        verdict,
        round(score, 1),
        dm_elem,
        bib_pct=round(bib_r * 100, 1),
        scg_pct=round(scg_r * 100, 1),
        deoling_note=deoling_note,
        sup_note=sup_note,
        sipsin_note=sipsin_note,
    )

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
        "강약_상세": strength_detail,
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
        "세운_강약_해설": [],
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

    strength_detail = _build_strength_detail(
        verdict,
        round(score, 1),
        dm_elem,
        bib_pct=round(bib_proxy * 100, 1),
        scg_pct=round((1 - bib_proxy) * 100, 1),
        deoling_note=deoling_note,
        sup_note=sup_note,
        sipsin_note=sipsin_note,
    )

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
        "강약_상세": strength_detail,
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
        "세운_강약_해설": [],
    }


def suggest_useful_gods(
    counts: Dict[str, int],
    day_master: str,
    month_zhi: str,
    *,
    pillars: Optional[dict] = None,
    sewoon_nearby: Optional[Sequence[Dict[str, Any]]] = None,
    sewoon_center_year: Optional[int] = None,
) -> Dict[str, Any]:
    if pillars is None:
        rep = _analyze_counts_only(counts, day_master, month_zhi)
    else:
        rep = analyze_yongsin(pillars, day_master, counts)
    if sewoon_nearby:
        rep["세운_강약_해설"] = build_sewoon_strength_series(
            rep, day_master, sewoon_nearby, center_year=sewoon_center_year
        )
    return rep
