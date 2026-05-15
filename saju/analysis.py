# -*- coding: utf-8 -*-
"""종합 분석 — 계산 결과 묶음 + 생활 영역별 패턴 해석."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from itertools import combinations
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import chung_pa_hae as cph
from . import daewoon as dw
from . import ganji as gj
from . import ilwoon as il
from . import jieqi_embedded as jq
from . import jijanggan as jj
from . import ohaeng as oh
from . import saju_calc as sc
from . import sewoon as sw
from . import sibiunsung as sb
from . import sinsal as sn
from . import sipsin as sp
from . import timeline as tl
from . import wolwoon as ww
from . import yongsin as ys
from .yongsin import CHEON_GAN_HAP_ELEM, ELEMENT_META, MONTH_COMMAND

PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")

_ELEMS_ORDER = ("목", "화", "토", "금", "수")

_ELEMENT_ORGAN = {
    "목": "간·담·목·눈 피로",
    "화": "심장·소화·혈압",
    "토": "비위·췌장·당대사",
    "금": "폐·대장·피부·호흡",
    "수": "신장·방광·하체·불면",
}

_SK = "⭐ 핵심 한줄 요약"
_EV = "📌 근거"
_WR = "⚠️ 주의사항"
_AD = "✅ 조언"


def _cat(summary: str, evidence: List[str], caution: List[str], advice: List[str]) -> Dict[str, Any]:
    return {_SK: summary, _EV: evidence, _WR: caution, _AD: advice}


def _wealth_element(day_master: str) -> str:
    i = _ELEMS_ORDER.index(gj.element_of_stem(day_master))
    return _ELEMS_ORDER[(i + 2) % 5]


def _officer_element(day_master: str) -> str:
    i = _ELEMS_ORDER.index(gj.element_of_stem(day_master))
    return _ELEMS_ORDER[(i + 3) % 5]


def _sipsin_counts(day_master: str, pillars: dict) -> Counter[str]:
    c: Counter[str] = Counter()
    for pk in PILLAR_KEYS:
        gans = [pillars[pk]["gan"]] + gj.jijanggan_ordered(pillars[pk]["zhi"])
        for gan in gans:
            if gan == day_master:
                continue
            c[sp.classify_sipsin(day_master, gan)] += 1
    return c


def _pillar_sipsin_set(day_master: str, pillars: dict, pk: str) -> Set[str]:
    gans = [pillars[pk]["gan"]] + gj.jijanggan_ordered(pillars[pk]["zhi"])
    return {sp.classify_sipsin(day_master, g) for g in gans if g != day_master}


def _parse_partner_pillar(s: Optional[str]) -> Optional[Tuple[str, str]]:
    if not s:
        return None
    t = s.strip()
    if len(t) != 2:
        return None
    gan, zhi = t[0], t[1]
    if gan not in gj.STEMS or zhi not in gj.BRANCHES:
        return None
    return gan, zhi


def _zhi_relation_tags(z1: str, z2: str) -> List[str]:
    pair = tuple(sorted((z1, z2)))
    tags: List[str] = []
    if pair in {tuple(sorted(p)) for p in gj.CHONG_PAIRS}:
        tags.append("충")
    if pair in {tuple(sorted(p)) for p in gj.LIU_PO}:
        tags.append("파")
    if pair in {tuple(sorted(p)) for p in gj.LIU_HAI}:
        tags.append("해")
    if pair in {tuple(sorted(p)) for p in gj.LIU_HE}:
        tags.append("육합")
    return tags


def _pillar_zhi_under_native_branch_stress(pk: str, pillars: dict) -> bool:
    """해당 주 지지가 원국 안 다른 지지와 충·파·해를 이루는지."""
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    ch_set = {tuple(sorted(p)) for p in gj.CHONG_PAIRS}
    po_set = {tuple(sorted(p)) for p in gj.LIU_PO}
    hai_set = {tuple(sorted(p)) for p in gj.LIU_HAI}
    for k1, k2 in combinations(PILLAR_KEYS, 2):
        if pk not in (k1, k2):
            continue
        t = tuple(sorted((zhis[k1], zhis[k2])))
        if t in ch_set or t in po_set or t in hai_set:
            return True
    return False


def _zhis_from_sinsal_rows(sinsal: Dict[str, Any], star_name: str) -> Set[str]:
    found: Set[str] = set()
    rows = sinsal.get("신살_목록") or []
    if not isinstance(rows, list):
        return found
    for r in rows:
        if r.get("신살") != star_name:
            continue
        for z in gj.BRANCHES:
            if z in r.get("글자", ""):
                found.add(z)
    return found


def _cheoneul_wealth_same_pillar(sinsal: Dict[str, Any], day_master: str, pillars: dict) -> List[str]:
    """천을 지지가 깔린 주에서 천간이 재성인 경우."""
    hits: List[str] = []
    ce = _zhis_from_sinsal_rows(sinsal, "천을귀인")
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    for pk in PILLAR_KEYS:
        if zhis[pk] not in ce:
            continue
        gan = pillars[pk]["gan"]
        if gan == day_master:
            continue
        if sp.classify_sipsin(day_master, gan) in ("편재", "정재"):
            hits.append(f"{sp.PILLAR_LABELS_KR[pk]}({pillars[pk]['pillar']})")
    return hits


def _yangin_marker_zhi(sinsal: Dict[str, Any]) -> Optional[str]:
    rows = sinsal.get("신살_목록") or []
    if not isinstance(rows, list):
        return None
    for r in rows:
        if r.get("신살") != "양인살":
            continue
        g = r.get("글자", "")
        for z in gj.BRANCHES:
            if z in g:
                return z
    return None


def _has_sinsal_lines(sinsal: Dict[str, Any], name: str) -> bool:
    xs = sinsal.get(name)
    return bool(xs) if isinstance(xs, list) else False


def _pillars_with_rexcai(day_master: str, pillars: dict) -> List[str]:
    out: List[str] = []
    for pk in PILLAR_KEYS:
        ss = _pillar_sipsin_set(day_master, pillars, pk)
        if ss & {"편재", "정재"}:
            out.append(pk)
    return out


def _pillars_with_officer(day_master: str, pillars: dict) -> List[str]:
    out: List[str] = []
    for pk in PILLAR_KEYS:
        ss = _pillar_sipsin_set(day_master, pillars, pk)
        if ss & {"정관", "편관"}:
            out.append(pk)
    return out


def _sewoon_years_officer_chong(
    day_master: str, pillars: dict, sewoon_items: Sequence[Dict[str, Any]]
) -> List[str]:
    officer_pks = set(_pillars_with_officer(day_master, pillars))
    if not officer_pks:
        return []
    lines: List[str] = []
    for item in sewoon_items:
        year = item.get("year")
        pillar = item.get("pillar") or ""
        if len(pillar) < 2:
            continue
        inj = cph.analyze_sewoon_injection(pillars, pillar, sewoon_year=year)
        for r in inj:
            if r.get("관계") != "세운충":
                continue
            w = r.get("위치", "")
            for pk in officer_pks:
                lab = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}[pk]
                if lab in w:
                    lines.append(f"{year}년 세운 {pillar}: {r['글자']} ({lab} 관성 자리 동요)")
                    break
    return lines[:12]


def _sewoon_years_geobjae_hit(
    day_master: str, sewoon_items: Sequence[Dict[str, Any]]
) -> List[str]:
    lines: List[str] = []
    for item in sewoon_items:
        gan = item.get("gan")
        y = item.get("year")
        if not gan or not y:
            continue
        if sp.classify_sipsin(day_master, gan) == "겁재":
            lines.append(f"{y}년 세운 천간 {gan}: 겁재가 들어와 동업·지출·경쟁 변수가 커질 수 있습니다.")
    return lines[:10]


def _sewoon_wealth_heavenly_union(
    day_master: str, pillars: dict, sewoon_items: Sequence[Dict[str, Any]]
) -> List[str]:
    lines: List[str] = []
    for item in sewoon_items:
        sg = item.get("gan")
        y = item.get("year")
        if not sg or not y:
            continue
        for pk in PILLAR_KEYS:
            pg = pillars[pk]["gan"]
            if pg == day_master:
                continue
            if sp.classify_sipsin(day_master, pg) not in ("편재", "정재"):
                continue
            if frozenset((sg, pg)) not in CHEON_GAN_HAP_ELEM:
                continue
            elem = CHEON_GAN_HAP_ELEM[frozenset((sg, pg))]
            lines.append(
                f"{y}년 세운 천간 {sg}이 {sp.PILLAR_LABELS_KR[pk]} 재성 {pg}와 천간합 → "
                f"합화 성향 {elem}, 재물·거래 인연 신호로 볼 수 있습니다."
            )
            break
    return lines[:10]


def _sewoon_hits_rexcai_branch(
    day_master: str, pillars: dict, sewoon_items: Sequence[Dict[str, Any]]
) -> List[str]:
    rex_pks = set(_pillars_with_rexcai(day_master, pillars))
    if not rex_pks:
        return []
    lines: List[str] = []
    for item in sewoon_items:
        pillar = item.get("pillar") or ""
        y = item.get("year")
        if len(pillar) < 2 or not y:
            continue
        inj = cph.analyze_sewoon_injection(pillars, pillar, sewoon_year=y)
        for r in inj:
            if r.get("관계") not in ("세운충", "세운파", "세운해"):
                continue
            w = r.get("위치", "")
            for pk in rex_pks:
                lab = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}[pk]
                if lab in w:
                    lines.append(f"{y}년 {r['관계']}가 재성 자리({lab})와 맞물립니다.")
                    break
    return lines[:12]


def _sewoon_day_chong_years(pillars: dict, sewoon_items: Sequence[Dict[str, Any]]) -> List[int]:
    dz = pillars["day"]["zhi"]
    ys: List[int] = []
    for item in sewoon_items:
        pillar = item.get("pillar") or ""
        y = item.get("year")
        if len(pillar) < 2 or not y:
            continue
        sz = pillar[1]
        if tuple(sorted((dz, sz))) in {tuple(sorted(p)) for p in gj.CHONG_PAIRS}:
            ys.append(int(y))
    return ys


def _kongwang_zhis_from_sinsal(sinsal_rows: Sequence[Dict[str, str]]) -> Set[str]:
    found: Set[str] = set()
    for r in sinsal_rows:
        if r.get("신살") != "공망(空亡)":
            continue
        g = r.get("글자", "")
        for z in gj.BRANCHES:
            if z in g:
                found.add(z)
    return found


def _xing_lines_for_mishap(native_shape: List[Dict[str, str]]) -> List[str]:
    lines: List[str] = []
    for r in native_shape:
        k = r.get("관계", "")
        if "형" in k or "삼형" in k:
            lines.append(f"[{k}] {r.get('글자')} @ {r.get('위치')} — {r.get('해석')}")
    return lines


def _daewoon_tone(yong: Dict[str, Any], cycle: Dict[str, Any]) -> Tuple[int, str]:
    gz = cycle.get("ganzhi") or ""
    if len(gz) < 2:
        return 0, "(간지 없음)"
    y_elem = yong.get("용신_오행") or ""
    hui = set(yong.get("희신") or [])
    gi = set(yong.get("기신") or [])
    ge = gj.element_of_stem(gz[0])
    ze = gj.element_of_branch(gz[1])
    score = 0
    for e in (ge, ze):
        if e == y_elem or e in hui:
            score += 1
        if e in gi:
            score -= 1
    if score >= 2:
        tag = "순조·보완 재물이 붙기 쉬운 편"
    elif score >= 1:
        tag = "평타 이상, 과제는 있으나 희신 방향으로 조정 여지"
    elif score <= -2:
        tag = "기신 자극이 커 무리한 확장·고집을 줄일 시기"
    else:
        tag = "중간, 큰 방향만 용신으로 맞추면 균형 가능"
    ages = f"{cycle.get('start_age')}~{cycle.get('end_age')}세"
    return score, f"{gz}({ages}): {tag}"


def _flow_sewoon_digest(
    day_master: str, pillars: dict, sewoon_items: Sequence[Dict[str, Any]]
) -> List[str]:
    lines: List[str] = []
    for item in sewoon_items:
        y = item.get("year")
        pillar = item.get("pillar") or ""
        if not y or len(pillar) < 2:
            continue
        inj = cph.analyze_sewoon_injection(pillars, pillar, sewoon_year=y)
        ch = sum(1 for r in inj if r.get("관계") == "세운충")
        if ch >= 2:
            lines.append(f"{y}년: 세운이 원국과 충이 {ch}건 겹쳐 변동·건강·관계 이슈가 동시에 올라올 수 있습니다.")
        elif ch == 1 and any("일지" in r.get("위치", "") for r in inj if r.get("관계") == "세운충"):
            lines.append(f"{y}년: 일지 충으로 거처·결혼·내실 테마가 요동칠 수 있습니다.")
    return lines[:10]


def _build_life_categories(
    *,
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    sinsal: Dict[str, Any],
    sewoon_nearby: Sequence[Dict[str, Any]],
    daewoon_cycles: Sequence[Dict[str, Any]],
    partner_day_pillar: Optional[str],
) -> Dict[str, Any]:
    female = sp.is_female_gender(gender)
    sip_c = _sipsin_counts(day_master, pillars)
    wealth_el = _wealth_element(day_master)
    officer_el = _officer_element(day_master)
    rel_full = cph.analyze_relations_full(pillars)
    ch_po_hai_rows = rel_full["원국_충"] + rel_full["원국_파"] + rel_full["원국_해"]

    day_branch_notes = [r["해석"] for r in ch_po_hai_rows if "일지" in r.get("위치", "")]
    peach = _has_sinsal_lines(sinsal, "도화살")
    wonjin = _has_sinsal_lines(sinsal, "원진살")

    officer_n = sip_c["정관"] + sip_c["편관"]
    officer_txt = (
        f"정관·편관 노출 합계 약 {officer_n}회(천간+지장간)"
        if officer_n
        else "관성 천간·지장간 노출이 매우 적음"
    )

    partner = _parse_partner_pillar(partner_day_pillar)
    partner_lines: List[str] = []
    if partner_day_pillar and partner is None:
        partner_lines.append("상대 일주는 두 글자(예: 庚子) 한글 간지로 넣어야 합니다.")
    elif partner:
        pz = partner[1]
        dz = pillars["day"]["zhi"]
        tags = _zhi_relation_tags(dz, pz)
        partner_lines.append(f"본인 일지 {dz} vs 상대 일지 {pz}: 관계 태그 {', '.join(tags) if tags else '충·파·해·육합 해당 없음'}.")

    love_ev = []
    if peach:
        love_ev.append("도화살: 인기·이성 인연 신호가 원국에 있습니다.")
    if day_branch_notes:
        love_ev.append("일지 충·파·해: 배우자·내실 축에 긴장 패턴이 있습니다.")
    if female:
        love_ev.append(f"여명 관성(남편성 참고): {officer_txt}")
    else:
        love_ev.append(f"남명 재성(배우자성 참고): 편재·정재 노출 {sip_c['편재'] + sip_c['정재']}회")
    if wonjin:
        love_ev.append("원진살: 부부·동료 각이 세게 부딪히기 쉬운 별입니다.")
    love_ev.extend(partner_lines)

    love_warn = []
    if peach and day_branch_notes:
        love_warn.append("도화와 일지 긴장이 겹치면 관계가 화려하지만 번복도 크니 속도 조절이 필요합니다.")
    if wonjin:
        love_warn.append("원진이면 대화 방식·기대치 조정 없이는 같은 갈등이 반복되기 쉽습니다.")

    love_adv = [
        "충·파가 있을수록 ‘맞춤’보다 ‘존중 거리’와 규칙 합의가 장기적으로 유리합니다.",
        "도화가 있으면 표현력은 강점으로 삼되, 관계 선택은 신중히 가져가면 좋습니다.",
    ]

    career_ev = [
        f"용신 오행 {yong.get('용신_오행')} 참고 직업군: {yong.get('용신_색상_방위_직업', {}).get('직업', '')}",
        officer_txt,
        f"식신·상관 노출 {sip_c['식신'] + sip_c['상관']}회 — 기술·표현·기획 에너지 지표입니다.",
    ]
    if _has_sinsal_lines(sinsal, "역마살"):
        career_ev.append("역마살: 이동·해외·직무 변경 변수가 있습니다.")

    career_warn = []
    if officer_n >= 4:
        career_warn.append("관성이 많으면 책임·규정 스트레스가 크니 역할 범위를 명확히 하세요.")
    if sip_c["상관"] >= sip_c["식신"] + 2:
        career_warn.append("상관이 두드러지면 상사·규칙과 마찰이 생기기 쉬워 보고 체계를 갖추는 것이 안전합니다.")

    career_adv = [
        f"용신 방향({yong.get('용신_오행')}) 산업·업무 환경을 우선 노출시키면 사회운이 덜 고됩니다.",
        "식상이 살아 있으면 결과물·포트폴리오 중심 커리어가 유리합니다.",
    ]

    rex_n = sip_c["편재"] + sip_c["정재"]
    reb_n = sip_c["겁재"]
    rex_pks = _pillars_with_rexcai(day_master, pillars)
    rex_hit_conflict = any(_pillar_zhi_under_native_branch_stress(pk, pillars) for pk in rex_pks)

    wealth_ev = [
        f"재성(편·정) 노출 합계 {rex_n}회, 재성 오행은 {wealth_el}입니다.",
        f"겁재 노출 {reb_n}회 — 동업·지출·경쟁으로 재물이 새기 쉬운지 봅니다.",
    ]
    if rex_hit_conflict:
        wealth_ev.append("재성이 놓인 지지가 원국 충·파·해와 맞물려 재무 구조가 흔들리기 쉽습니다.")
    if yong.get("용신_오행") == wealth_el:
        wealth_ev.append("용신이 재성 오행과 같아 재물 운을 적극적으로 끌어올릴 여지가 있습니다.")

    wealth_warn = []
    if reb_n >= rex_n and rex_n > 0:
        wealth_warn.append("겁재가 재성보다 두드러지면 남의 돈·공동지출로 손재 패턴이 나올 수 있습니다.")
    if rex_hit_conflict:
        wealth_warn.append("투자·보증·급격한 확장은 충·파가 걸린 재 자리에서 특히 보수적으로.")

    wealth_adv = [
        "재성이 살아 있을 때는 현금흐름·회계 습관을 먼저 갖추면 복이 실속으로 전환되기 쉽습니다.",
        f"용신 {yong.get('용신_오행')} 방향 일과 재테크를 겸하면 안정성이 올라갑니다.",
    ]

    dom_weak = oh.dominant_weak_elements(counts)
    strong_e = dom_weak.get("strong") or []
    weak_e = dom_weak.get("weak") or []

    health_ev = []
    for e in strong_e:
        health_ev.append(f"{e} 과다 기운: {_ELEMENT_ORGAN.get(e, '')} 쪽 피로·만성 질환 여지를 함께 봅니다.")
    for e in weak_e:
        health_ev.append(f"{e} 결핍 기운: {_ELEMENT_ORGAN.get(e, '')} 보완·정밀 검진을 참고합니다.")

    for r in rel_full["원국_충"]:
        if "일지" in r.get("위치", "") or "월지" in r.get("위치", ""):
            zs = [z for z in gj.BRANCHES if z in r.get("글자", "")]
            for z in zs:
                health_ev.append(f"충으로 요동치는 지지 {z}: {cph.ZHI_BODY.get(z, '')}")

    if _has_sinsal_lines(sinsal, "백호살"):
        health_ev.append("백호살: 금속·피·수술·급사 변수를 의식합니다.")
    if _has_sinsal_lines(sinsal, "양인살"):
        health_ev.append("양인살: 칼날·외상·결단으로 몸이 같이 반응하기 쉽습니다.")

    pianyin_n = sip_c["편인"]
    health_warn = []
    if pianyin_n >= 4:
        health_warn.append("편인 과다는 스트레스·불면·종양 등 뭉친 덩어리 질환을 점검할 편이 안전합니다.")

    health_adv = [
        "충이 있는 부위(지지)는 정기 검진·유연성 운동·과로 관리를 우선하세요.",
        "오행이 치우치면 해당 장부 보양식·수면 리듬부터 조정하면 체감이 빠릅니다.",
    ]

    legal_ev = []
    if _has_sinsal_lines(sinsal, "백호살"):
        legal_ev.append("백호살")
    if _has_sinsal_lines(sinsal, "양인살"):
        legal_ev.append("양인살")
    if _has_sinsal_lines(sinsal, "괴강살"):
        legal_ev.append("괴강살(일주)")
    legal_ev.extend(_xing_lines_for_mishap(rel_full["원국_형"]))
    officer_chong_years = _sewoon_years_officer_chong(day_master, pillars, sewoon_nearby)
    legal_ev.extend(officer_chong_years[:6])

    legal_warn = [
        "형·충이 겹치는 해에는 규정·계약·운전 안전을 보수적으로 가져가세요.",
    ]

    legal_adv = [
        "관성 자리가 흔들리는 해에는 실력보다 절차·문서를 먼저 챙기면 관재 소지가 줄어듭니다.",
    ]

    wind_ev = []
    if sip_c["편재"] >= 2 and not rex_hit_conflict:
        wind_ev.append("편재가 두드러지고 재 지지 충파해가 약하면 한방 재물·기회 포착 신호가 있습니다.")
    che = _cheoneul_wealth_same_pillar(sinsal, day_master, pillars)
    if che:
        wind_ev.append("천을귀인 + 재성 동주: " + ", ".join(che))
    wind_ev.extend(_sewoon_wealth_heavenly_union(day_master, pillars, sewoon_nearby))

    wind_warn = ["급격한 베팅·보증은 세운 충과 겹치면 오히려 증발하기 쉽습니다."]
    wind_adv = ["기회 해에는 현금 확보 비율을 정해 두고 단계적으로 실행하면 횡재가 실속으로 남습니다."]

    loss_ev = _sewoon_years_geobjae_hit(day_master, sewoon_nearby)
    loss_ev.extend(_sewoon_hits_rexcai_branch(day_master, pillars, sewoon_nearby))
    yangin_br = _yangin_marker_zhi(sinsal)
    if yangin_br and _has_sinsal_lines(sinsal, "양인살"):
        for item in sewoon_nearby:
            p = item.get("pillar") or ""
            if len(p) >= 2 and p[1] == yangin_br and item.get("year"):
                loss_ev.append(f"{item['year']}년 세운 지지 {yangin_br}: 양인과 만나 지출·외상 변수를 의식합니다.")

    loss_warn = ["겁재·충이 겹치면 로또급 기대보다 지출 통제가 우선입니다."]
    loss_adv = ["공동지출·연대보증을 줄이고, 재성 자리가 요동치는 해에는 현금 비중을 높입니다."]

    mour_ev = []
    if _has_sinsal_lines(sinsal, "상문살"):
        mour_ev.append("상문살: 조문·상가 이벤트에 민감합니다.")
    if _has_sinsal_lines(sinsal, "조객살"):
        mour_ev.append("조객살: 애도·이별 기운이 들어오기 쉽습니다.")

    sin_rows = sinsal.get("신살_목록") or []
    kong_set = _kongwang_zhis_from_sinsal(sin_rows if isinstance(sin_rows, list) else [])
    for pk in PILLAR_KEYS:
        if pillars[pk]["zhi"] in kong_set:
            ss = _pillar_sipsin_set(day_master, pillars, pk)
            yk = []
            for sname in ss:
                yk.extend(sp.yukchin_roles(sname, female=female))
            if yk:
                mour_ev.append(f"공망이 {sp.PILLAR_LABELS_KR[pk]}에 걸리며 육친 기운 {','.join(sorted(set(yk)))}이 허해 보입니다.")

    mour_warn = ["상문·조객이 있으면 가족 건강 체크를 미루지 않는 것이 좋습니다."]
    mour_adv = ["비보가 예상될 때는 마음·일정·재정 여유를 미리 확보하세요."]

    sep_ev = []
    day_chong_years = _sewoon_day_chong_years(pillars, sewoon_nearby)
    if day_chong_years:
        sep_ev.append(f"일지 충이 예상되는 해: {', '.join(str(y) for y in day_chong_years[:8])}")
    if wonjin:
        sep_ev.append("원진살: 반복 갈등으로 거리두기·이별 논의가 나오기 쉽습니다.")
    if pillars["day"]["zhi"] in kong_set:
        sep_ev.append("일지가 공망: 배우자 인연의 허실·시차를 함께 봅니다.")

    sep_warn = ["일지 충 해에는 큰 이사·결별 결정을 즉흥적으로 내리지 않도록 숙고가 필요합니다."]
    sep_adv = ["관계는 ‘규칙·재정 합의’를 문서로 남기면 공망·충의 피해가 줄어듭니다."]

    dw_lines = [_daewoon_tone(yong, c)[1] for c in daewoon_cycles if c.get("ganzhi")]
    flow_ev = dw_lines[:8]
    flow_ev.extend(_flow_sewoon_digest(day_master, pillars, sewoon_nearby))

    flow_warn = ["대운·세운은 참고용 규칙 기반이며 실제는 월운·일진·환경이 함께 작동합니다."]
    flow_adv = ["10년 대운 방향을 용신 오행에 맞추고, 세운은 일지·재성 충 여부만 골라 관리해도 큰 그림이 잡힙니다."]

    def _sum(cat_ev: List[str], fallback: str) -> str:
        return fallback if not cat_ev else " | ".join(cat_ev[:4])

    out = {
        "1_연애_궁합": _cat(
            _sum(love_ev, "연애 패턴은 원국 일지와 도화·관성 균형으로 판단합니다."),
            love_ev[:12] or ["특이 신호가 적음"],
            love_warn,
            love_adv,
        ),
        "2_직업_사회운": _cat(
            _sum(career_ev, "용신·관성·식상 균형으로 사회 적응 방식을 가늠합니다."),
            career_ev[:12],
            career_warn,
            career_adv,
        ),
        "3_재물운": _cat(
            _sum(wealth_ev, "재성·겁재 비율과 충파해 여부로 재물 붙는 방식이 갈립니다."),
            wealth_ev[:12],
            wealth_warn,
            wealth_adv,
        ),
        "4_건강": _cat(
            _sum(health_ev, "오행 균형과 충 지지로 체질 취약축을 짚습니다."),
            health_ev[:14],
            health_warn,
            health_adv,
        ),
        "5_사고_관재": _cat(
            _sum(legal_ev, "백호·양인·형살과 세운 관성 충을 함께 봅니다."),
            legal_ev[:14],
            legal_warn,
            legal_adv,
        ),
        "6_횡재운": _cat(
            _sum(wind_ev, "편재·귀인·세운 천간합이 맞물릴 때 기회 신호로 볼 수 있습니다."),
            wind_ev[:12],
            wind_warn,
            wind_adv,
        ),
        "7_손재운": _cat(
            _sum(loss_ev, "겁재 세운·재성 자리 충파해를 중심으로 지출 경계를 봅니다."),
            loss_ev[:14],
            loss_warn,
            loss_adv,
        ),
        "8_상복_우환": _cat(
            _sum(mour_ev, "상문·조객·공망 육친으로 조문·비보를 의식합니다."),
            mour_ev[:12],
            mour_warn,
            mour_adv,
        ),
        "9_이별_별리": _cat(
            _sum(sep_ev, "일지 충·원진·공망으로 거리·재정 분리 이슈를 봅니다."),
            sep_ev[:10],
            sep_warn,
            sep_adv,
        ),
        "10_전체_운세_흐름": _cat(
            _sum(flow_ev, "대운 간지 성향과 세운 다발 충으로 변동 해를 짚습니다."),
            flow_ev[:14],
            flow_warn,
            flow_adv,
        ),
        "_참고": {
            "재성_오행": wealth_el,
            "관성_오행": officer_el,
            "편재_겁재_카운트": {"편재": sip_c["편재"], "정재": sip_c["정재"], "겁재": sip_c["겁재"]},
        },
    }
    return out


_ELEM_POETIC = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}


def _sorted_elems_by_count(counts: Dict[str, int]) -> List[str]:
    return [e for e, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)]


def _guiren_star_names(sinsal: Dict[str, Any]) -> List[str]:
    rows = sinsal.get("신살_목록") or []
    if not isinstance(rows, list):
        return []
    names: List[str] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        n = r.get("신살") or ""
        if "귀인" in n and n not in names:
            names.append(n)
    return names


def _story_core_line(
    day_master: str,
    pillars: dict,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    sip_c: Counter[str],
) -> str:
    dom = oh.dominant_weak_elements(counts)
    top = _sorted_elems_by_count(counts)[:2]
    poetic = [_ELEM_POETIC.get(e, e) for e in top]
    heap = "·".join(poetic) if poetic else "오행"
    dm_el = gj.element_of_stem(day_master)
    verdict = yong.get("일간_강약") or "중화"
    dz = pillars["day"]["zhi"]
    month_cmd = MONTH_COMMAND.get(pillars["month"]["zhi"], "토")
    spouse_stress = any(sw.branch_chong(dz, pillars[pk]["zhi"]) for pk in ("year", "month"))
    officer_n = sip_c["정관"] + sip_c["편관"]
    rex_n = sip_c["편재"] + sip_c["정재"]
    geb_n = sip_c["겁재"]

    will_txt = "의지와 버티는 힘"
    if verdict == "신강":
        will_txt = "강한 의지와 자기주장·추진력"
    elif verdict == "신약":
        will_txt = "섬세함과 내실형 인내"

    spouse_txt = "배우자 인연은 비교적 순조롭게 정리되기 쉬운 편입니다"
    if spouse_stress and officer_n >= 4:
        spouse_txt = "배우자·계약 인연은 매력과 긴장이 동시에 들어와 다소 복잡하게 전개되기 쉽습니다"
    elif spouse_stress or pillars["day"]["zhi"] in _kong_zhis_union(pillars):
        spouse_txt = "배우자·내실 축에 변동·공백을 의식하고 거리·합의 과제가 생기기 쉽습니다"
    elif officer_n >= 5:
        spouse_txt = "배우자·규범 축이 무겁게 깔려 책임과 기대가 크게 얹히는 형입니다"

    wealth_txt = "재물은 꾸준한 노력과 역할 설계가 기본 축입니다"
    if rex_n >= 5 and geb_n <= rex_n:
        wealth_txt = "재물은 기회 포착과 거래 감각이 살아나 요행·사업형 수입도 기대할 수 있습니다"
    elif geb_n >= rex_n + 2 and rex_n > 0:
        wealth_txt = "재물은 벌어들임보다 지출·분배 변수가 커 관리형·노력형에 가깝습니다"
    elif rex_n <= 2:
        wealth_txt = "재물은 명목 수입보다 기술·연봉·안정 현금흐름형으로 굳어지기 쉽습니다"

    tail = f"월령 기운은 {month_cmd}쪽 뿌리에서 시작합니다."
    return (
        f"{heap} 기운이 두드러진 사주로, {will_txt}이 포개집니다. "
        f"{spouse_txt}. {wealth_txt}. 일간은 {dm_el}을 타고난 축입니다. {tail}"
    ).strip()


def _story_personality(
    gender: str,
    sip_c: Counter[str],
    yong: Dict[str, Any],
    sinsal: Dict[str, Any],
    rel_full: Dict[str, Any],
) -> Dict[str, Any]:
    female = sp.is_female_gender(gender)
    bib = sip_c["비견"] + sip_c["겁재"]
    ins = sip_c["편인"] + sip_c["정인"]
    ss = sip_c["식신"] + sip_c["상관"]
    rex = sip_c["편재"] + sip_c["정재"]
    guan = sip_c["정관"] + sip_c["편관"]

    strengths: List[str] = []
    if bib >= 3:
        strengths.append("독립적 판단과 선이 지키는 투지가 있어 위기에서도 스스로 버티는 힘이 있습니다.")
    if ss >= 4:
        strengths.append("표현·기술·기획으로 무언가를 빚어내는 재능과 속도감이 있습니다.")
    if rex >= 4:
        strengths.append("현실 감각과 거래·숫자 감각으로 생활 전반을 구조화하는 편입니다.")
    if guan >= 3:
        strengths.append("책임·규범·약속을 중시해 조직과 역할 안에서 신뢰를 쌓기 쉽습니다.")
    if ins >= 4:
        strengths.append("배움·연구·복안(복기) 습관으로 전문성을 쌓아 올리는 인내가 있습니다.")
    if _has_sinsal_lines(sinsal, "문창귀인") or _has_sinsal_lines(sinsal, "학당귀인"):
        strengths.append("글·학문·자격의 기운이 받쳐 줄 때 설명력과 논리 전개가 빛납니다.")
    if len(strengths) < 5:
        strengths.append("용신 방향으로 일과 환경을 맞출 때 강점이 가장 크게 드러나는 타입입니다.")
    while len(strengths) < 5:
        strengths.append("대인관계에서 약속 시간·메모 습관만 지켜도 신뢰가 빠르게 쌓입니다.")
    strengths = strengths[:5]

    weaknesses: List[str] = []
    if sip_c["상관"] >= sip_c["식신"] + 3:
        weaknesses.append("말·표현이 상대에게 도발로 비칠 수 있어 상사·가족과 마찰이 잦아질 수 있습니다.")
    if guan >= 5:
        weaknesses.append("스스로 책임을 과하게 지며 번아웃·근육 긴장·불면으로 이어지기 쉽습니다.")
    if ins >= 5:
        weaknesses.append("생각이 많아지고 우려가 길어져 실행을 미루거나 우울 기복이 생기기 쉽습니다.")
    if bib >= 6:
        weaknesses.append("고집과 자존이 앞서 타협을 손해로 느끼게 되어 관계 비용이 커질 수 있습니다.")
    if rex <= 2 and guan >= 4:
        weaknesses.append("현금·재테크 감각을 키우지 않으면 수입 대비 불안이 누적되기 쉽습니다.")
    ch_day = [r for r in rel_full.get("원국_충", []) if "일지" in r.get("위치", "")]
    if ch_day:
        weaknesses.append("내실·배우자 축이 자주 흔들리는 패턴이라 정서적 안정 설계가 필요합니다.")
    if len(weaknesses) < 5:
        weaknesses.append("기신 오행이 과할 때 같은 실수를 반복할 수 있어 주기적 점검이 필요합니다.")
    while len(weaknesses) < 5:
        weaknesses.append("피로가 쌓이면 말수가 줄거나 반대로 과잉 반응이 나올 수 있어 휴식 루틴이 중요합니다.")
    weaknesses = weaknesses[:5]

    if ss >= guan and ss >= rex:
        social = "말과 결과물로 사람을 끌어당기는 스타일이며, 칭찬보다는 피드백 욕구가 솔직하게 드러납니다."
    elif rex >= ss:
        social = "실리·교환가치를 중시하는 편이라 신뢰는 약속 이행과 금전 명료함에서 생깁니다."
    elif guan >= ss:
        social = "역할·예의를 중시하는 편이라 선후배·직급 관계에서 거리감을 나누는 방식이 편합니다."
    else:
        social = "가까운 소수와 깊게 가는 편이며, 넓은 네트워크보다 오래된 인연을 챙깁니다."

    if guan >= 4 or sip_c["편관"] >= 3:
        stress = "압박이 오면 더 바짝 매달리다 몸과 말이 거칠어질 수 있어 수면·근육 이완이 우선입니다."
    elif ins >= 5:
        stress = "스트레스 시 혼자 삭이거나 검색·추측이 길어지며, 대화로 풀면 회복 속도가 빨라집니다."
    elif sip_c["겁재"] >= 4:
        stress = "경쟁·비교 의식이 발동해 지출이나 과장된 약속으로 번아웃으로 이어질 수 있습니다."
    else:
        stress = "평소 무던해 보이다 한계선에서 감정이 터지는 편이라 ‘미리 쉬는 날’을 넣는 것이 안전합니다."

    if rex >= guan and bib >= 3:
        decide = "숫자·체감 손익을 보며 빠르게 결정하고, 망설임은 짧게 가져가는 편입니다."
    elif guan > rex:
        decide = "규정·상사·주변 시선을 참고해 안전한 선택을 고르는 신중형입니다."
    elif ins >= ss:
        decide = "정보를 충분히 모은 뒤 결론을 내리며, 급한 결정은 불안을 남깁니다."
    else:
        decide = "직관과 경험 법칙을 섞어 결정하며, 큰 결정은 한 박자 쉬었다가 확정합니다."

    return {
        "장점_5": strengths,
        "단점_5": weaknesses,
        "대인관계_스타일": social,
        "스트레스_반응": stress,
        "의사결정_방식": decide,
        "_참고_성별해석축": "여명" if female else "남명",
    }


def _story_life_arc(
    pillars: dict,
    yong: Dict[str, Any],
    sip_c: Counter[str],
    daewoon_cycles: Sequence[Dict[str, Any]],
) -> Dict[str, str]:
    year_z = pillars["year"]["zhi"]
    month_z = pillars["month"]["zhi"]
    hour_z = pillars["hour"]["zhi"]

    def zstress(z: str) -> str:
        hits = sum(
            1
            for pk in PILLAR_KEYS
            if pillars[pk]["zhi"] != z
            and tuple(sorted((z, pillars[pk]["zhi"])))
            in {tuple(sorted(p)) for p in gj.CHONG_PAIRS}
        )
        return "다소 출발 환경에 변수가 있었을 수 있습니다." if hits else "비교적 안정적인 출발 축입니다."

    youth_home = (
        f"년지({year_z})가 부모·초기 환경을 대표합니다. {zstress(year_z)} "
        f"월령 오행은 {yong.get('월령_주기', '')} 방향과 맞물립니다."
    )
    teen = (
        f"월지({month_z})는 학업·사회화 초기를 상징합니다. "
        f"식상·관성 노출이 있어 표준 경로 안에서도 방향 전환 욕구가 생길 수 있습니다."
        if sip_c["식신"] + sip_c["상관"] >= 3 or sip_c["정관"] + sip_c["편관"] >= 3
        else f"월지({month_z})는 학업·친구 관계에서 내향형 성장이 두드러질 수 있습니다."
    )
    young_adult = (
        f"일주는 배우자·자아 확립 축입니다. 일지 {pillars['day']['zhi']}를 중심으로 연애·결혼·첫 직장 테마가 펼쳐집니다."
    )
    mid = (
        "재·관 균형이 맞물리는 시기로 전성기(직급·매출)와 책임 과부하가 동시에 올 수 있습니다."
        if sip_c["편재"] + sip_c["정재"] >= 4 and sip_c["정관"] + sip_c["편관"] >= 3
        else "전성기보다 방향 재설정·내실 다지기 과제가 교차하는 시기로 보입니다."
    )
    mature = (
        "자산·가족 구조를 정리하며 권위와 역할을 나누는 시기입니다."
        if sip_c["정재"] >= 2
        else "경험을 바탕으로 일과 삶의 우선순위를 줄이는 조정기입니다."
    )
    elder = (
        f"시지({hour_z})는 말년·자녀·후손 환경입니다. "
        f"{'활동 반경은 줄어도 자아 표현은 살아 있는 편입니다.' if sip_c['식신'] + sip_c['상관'] >= 2 else '조용한 안식과 의료·여행 계획이 중요해집니다.'}"
    )

    dw0 = ""
    if daewoon_cycles:
        _, dw0 = _daewoon_tone(yong, daewoon_cycles[0])
    arc_note = f"첫 대운 참고: {dw0}" if dw0 else ""

    return {
        "유년기_15미만": youth_home,
        "청소년기_15_25": teen + (" " + arc_note if arc_note else ""),
        "청년기_25_35": young_adult,
        "중년기_35_50": mid,
        "장년기_50_65": mature,
        "노년기_65이상": elder,
    }


def _story_career_details(day_master: str, pillars: dict, yong: Dict[str, Any], sip_c: Counter[str]) -> Dict[str, Any]:
    meta = yong.get("용신_색상_방위_직업") or {}
    base_jobs = (meta.get("직업") or "").replace("·", ",").split(",")
    base_jobs = [t.strip() for t in base_jobs if t.strip()]
    extras: List[Tuple[str, str]] = []
    if sip_c["식신"] + sip_c["상관"] >= 4:
        extras.append(("크리에이터·기술교육", "식상이 두드러져 결과물·설명력으로 돈을 버는 구조에 가깝습니다."))
    if sip_c["편재"] + sip_c["정재"] >= 4:
        extras.append(("영업·재무·유통", "재성이 받쳐 거래·현금 사이클을 직접 만지는 일에 강점이 생깁니다."))
    if sip_c["정관"] + sip_c["편관"] >= 4:
        extras.append(("관리·공공·컴플라이언스", "관성이 무거워 규정·감사·조직 운영 역할에 적합합니다."))
    if sip_c["편인"] + sip_c["정인"] >= 5:
        extras.append(("연구·컨설팅·재교육", "인성이 깊어 자료·개념 정리형 일에 몰입도가 높습니다."))

    top5: List[Dict[str, str]] = []
    for j in base_jobs[:3]:
        top5.append({"직군": j, "이유": f"용신 {yong.get('용신_오행')} 방향 산업 축과 연결됩니다."})
    for job, why in extras:
        if len(top5) >= 5:
            break
        if job not in {x["직군"] for x in top5}:
            top5.append({"직군": job, "이유": why})
    idx = 0
    while len(top5) < 5:
        fallback = ["프로젝트 매니저", "운영·품질", "데이터 정리", "현장 중재", "교육 보조"]
        job = fallback[idx % len(fallback)]
        idx += 1
        if job not in {x["직군"] for x in top5}:
            top5.append({"직군": job, "이유": "십신 균형을 맞추며 성장 보조 역할로 두면 안정적입니다."})

    avoid: List[str] = []
    for el in yong.get("기신") or []:
        mj = (ELEMENT_META.get(el) or {}).get("직업")
        if mj:
            avoid.append(f"{el} 과열 산업({mj})은 피로·좌절 비용이 클 수 있습니다.")

    verdict = yong.get("일간_강약") or ""
    rex_n = sip_c["편재"] + sip_c["정재"]
    ss_n = sip_c["식신"] + sip_c["상관"]
    geb_n = sip_c["겁재"]

    biz_ok = verdict == "신강" and rex_n >= 3 and geb_n < rex_n
    freelance_ok = ss_n >= rex_n and ss_n >= 4
    employee_ok = sip_c["정관"] + sip_c["편관"] >= 3 or verdict != "신강"

    modes: List[str] = []
    if employee_ok:
        modes.append("직장인: 조직 내 역할을 명확히 할 때 장기 복이 안정적으로 붙는 편입니다.")
    if freelance_ok:
        modes.append("프리랜서·프로젝트: 포트폴리오·단가 협상력을 갖추면 식상 기운이 수입으로 전환됩니다.")
    if biz_ok:
        modes.append("사업가: 거래 구조와 지분 설계만 명확하면 재성이 롤업 성향으로 작동할 여지가 있습니다.")
    if not modes:
        modes.append("직장 내 전문가·실무형으로 커리어를 쌓은 뒤 소규모 사업 전환을 검토하는 흐름이 무리가 적습니다.")

    return {
        "최적_직군_TOP5": top5[:5],
        "피해야_할_직군": avoid[:6],
        "사업_적합": "추진형 재성 구조가 받쳐 줄 때 적합 신호가 큽니다." if biz_ok else "안정적 현금흐름 확보 후 단계적 창업이 안전합니다.",
        "근무형태_판정": modes,
    }


def _story_wealth_lifetime(
    day_master: str,
    pillars: dict,
    yong: Dict[str, Any],
    sip_c: Counter[str],
    sinsal: Dict[str, Any],
    daewoon_cycles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    rex_n = sip_c["편재"] + sip_c["정재"]
    geb_n = sip_c["겁재"]
    ce_hit = bool(_cheoneul_wealth_same_pillar(sinsal, day_master, pillars))

    if rex_n >= 4 and geb_n <= rex_n - 1 and sip_c["편재"] >= 2:
        earn = "요행·거래·기회 포착형에 가깝고, 한 번 잘 붙으면 레버리지를 타기 쉽습니다."
    elif sip_c["식신"] + sip_c["상관"] >= rex_n and rex_n >= 3:
        earn = "기술·브랜드·콘텐츠 등 투자형·성장형 수입(지식 자산)으로 불어나는 패턴입니다."
    else:
        earn = "노력·연봉·반복 매출형이 중심이며, 꾸준한 저축 습관이 복을 고정시킵니다."

    leak: List[str] = []
    if geb_n > rex_n:
        leak.append("겁재가 재성보다 세면 동업·경쟁·충동 소비로 재물이 새기 쉽습니다.")
    rex_pks = _pillars_with_rexcai(day_master, pillars)
    if any(_pillar_zhi_under_native_branch_stress(pk, pillars) for pk in rex_pks):
        leak.append("재성 자리 지지가 충파해와 맞물리면 사업·주식 손실 폭이 커질 수 있습니다.")
    if sip_c["편관"] >= 3:
        leak.append("관살 스트레스가 건강·법적 비용으로 이어져 간접 손재가 나올 수 있습니다.")
    if not leak:
        leak.append("특이한 누출 패턴은 적으나 방심한 보증·연대는 피하는 편이 좋습니다.")

    flow_bits = [_daewoon_tone(yong, c)[1] for c in daewoon_cycles[:4] if c.get("ganzhi")]
    flow = (
        "초기 대운은 " + ("순조 방향이 많습니다." if flow_bits and "순조" in flow_bits[0] else "방향을 다잡는 과제가 있습니다.")
        + " 이후 대운은 용신 오행과 맞을수록 재물 그래프가 완만하게 우상향합니다."
    )
    if flow_bits:
        flow += " 참고: " + flow_bits[0]

    rich = "중상 위안: 균형과 습관만 유지하면 평생 현금흐름은 안정적으로 유지하기 쉽습니다."
    if rex_n >= 5 and not geb_n > rex_n + 1 and ce_hit:
        rich = "상향 가능: 귀인·재성 결합 신호가 있어 한두 번의 큰 승부에서 자산 레벨이 올라갈 여지가 있습니다."
    elif geb_n >= rex_n + 3:
        rich = "보수형: 벌기보다 지키기·분산 투자가 우선인 명식입니다."

    return {
        "버는_방식": earn,
        "새는_패턴": leak[:5],
        "평생_재물_흐름": flow,
        "부자_가능성_판정": rich,
    }


def _story_health_lifetime(
    counts: Dict[str, int],
    sip_c: Counter[str],
    sinsal: Dict[str, Any],
    rel_full: Dict[str, Any],
) -> Dict[str, Any]:
    dom = oh.dominant_weak_elements(counts)
    weak_bodies = [_ELEMENT_ORGAN.get(e, e) for e in (dom.get("weak") or [])][:3]
    strong_bodies = [_ELEMENT_ORGAN.get(e, e) for e in (dom.get("strong") or [])[:2]]

    age_notes = {
        "유소년": "성장기에는 과다 오행 장부의 피로·알레르기를 의식합니다.",
        "청년": "식상·관성 긴장이 교차하면 불면·위장·근골격 피로가 빨리 올 수 있습니다.",
        "중년": "충이 있는 지지 장부는 만성 질환 전조가 되므로 정기 검진 간격을 짧게 잡습니다.",
        "시니어": "결핍 오행 장부 보양과 낙상 예방, 순환 관리가 장수 분기점입니다.",
    }

    longevity = "생명력은 비교적 평균 이상으로 유지하려면 수면·혈압 관리만 해도 체감이 큽니다."
    if sip_c["편관"] + sip_c["편인"] >= 8:
        longevity = "스트레스·급성 염증 리스크가 있어 장수 여부는 생활 습관 차이에 크게 좌우됩니다."
    if _has_sinsal_lines(sinsal, "백호살") or _has_sinsal_lines(sinsal, "양인살"):
        longevity += " 백호·양인은 급성 사고·수술 변수를 의식합니다."

    advice = [
        "충·형이 걸린 지지 장부는 유연성 운동과 해당 장기 검진을 우선하세요.",
        "오행이 치우치면 반대 성질 음식·환경(생족)을 번갈아 주면 회복 속도가 빨라집니다.",
    ]
    if strong_bodies:
        advice.append(f"선천적으로 과한 축({','.join(strong_bodies)})은 과로 시 먼저 신호가 옵니다.")

    return {
        "선천_취약_축": weak_bodies or ["종합 검진으로 개인별 우선순위 확인 권장"],
        "나이대별_주의": age_notes,
        "장수_가능성": longevity,
        "건강_유지_조언": advice,
    }


def _story_special_points(
    day_master: str,
    pillars: dict,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    sip_c: Counter[str],
    sinsal: Dict[str, Any],
    daewoon_cycles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    jong = yong.get("종격_휴리스틱") or {}
    hwa = yong.get("화격_휴리스틱") or {}
    special_lines: List[str] = []
    if isinstance(jong, dict) and jong.get("성립"):
        special_lines.append(f"종격 성향: {jong.get('설명', '')}")
    if isinstance(hwa, dict) and hwa.get("성립"):
        special_lines.append(f"화기 용신 후보: {hwa.get('설명', '')}")

    guirens = _guiren_star_names(sinsal)
    guiren_txt = f"귀인 신살 {len(guirens)}종 노출 — {', '.join(guirens[:8])}" if guirens else "두드러진 귀인 신호는 적지만 용신 방향 인연을 스스로 만들면 보완됩니다."

    comeback = "신약·재성 축이 용신 대운에서 살아나 역전 드라마가 가능한 편입니다."
    if yong.get("일간_강약") == "신강":
        comeback = "신강 명은 한 번 꺾인 뒤 재정비하고 들어올 때 더 크게 도약하는 패턴입니다."
    if daewoon_cycles:
        sc, _ = _daewoon_tone(yong, daewoon_cycles[0])
        if sc >= 2:
            comeback += " 첫 대운이 용신과 맞닿아 초반부터 귀인·기회 신호가 강합니다."
        elif sc <= -1:
            comeback += " 초반 대운은 시행착오를 통해 내공을 쌓는 전개일 수 있습니다."

    spirit = "현실 검증과 데이터를 신뢰하는 편입니다."
    if sip_c["편인"] + sip_c["정인"] >= 6:
        spirit = "종교·명상·철학·심리 등 무형 세계에 끌리기 쉬운 명식입니다."
    if pillars["day"]["zhi"] in _kong_zhis_union(pillars):
        spirit += " 공망이 있어 허무감·영적 탐구를 함께 타고날 수 있습니다."

    extras: List[str] = []
    if _has_sinsal_lines(sinsal, "역마살"):
        extras.append("역마: 이동·해외·종교 순례 인연.")
    if _has_sinsal_lines(sinsal, "도화살"):
        extras.append("도화: 사람에게 끌림과 예술적 감수성.")

    return {
        "특수격_휴리스틱": special_lines or ["단순 규칙상 특이 격 국한 신호는 크지 않습니다."],
        "귀인_복": guiren_txt,
        "고난_역전_가능성": comeback,
        "종교_정신세계_성향": spirit,
        "기타_표식": extras,
    }


def _build_native_story_pack(
    *,
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    sinsal: Dict[str, Any],
    daewoon_cycles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    sip_c = _sipsin_counts(day_master, pillars)
    rel_full = cph.analyze_relations_full(pillars)

    return {
        "사주_한줄_핵심": _story_core_line(day_master, pillars, counts, yong, sip_c),
        "성격_분석": _story_personality(gender, sip_c, yong, sinsal, rel_full),
        "인생_전체_흐름": _story_life_arc(pillars, yong, sip_c, daewoon_cycles),
        "직업_적성": _story_career_details(day_master, pillars, yong, sip_c),
        "재물_패턴": _story_wealth_lifetime(day_master, pillars, yong, sip_c, sinsal, daewoon_cycles),
        "건강_평생": _story_health_lifetime(counts, sip_c, sinsal, rel_full),
        "특별_포인트": _story_special_points(day_master, pillars, counts, yong, sip_c, sinsal, daewoon_cycles),
        "안내": "본 블록은 오행·십신·신살·충합 규칙을 바탕 한 스토리텔링 참고용이며, 실제 상담은 파종·환경과 함께 봅니다.",
    }


# --- 세운·월운 정밀 분석 (규칙 기반 참고용) ---------------------------------

_BANG_GROUPS: Tuple[Tuple[str, frozenset, str], ...] = (
    ("동방(목)", frozenset({"寅", "卯", "辰"}), "목"),
    ("남방(화)", frozenset({"巳", "午", "未"}), "화"),
    ("서방(금)", frozenset({"申", "酉", "戌"}), "금"),
    ("북방(수)", frozenset({"亥", "子", "丑"}), "수"),
)

_JJG_KEYS = ("정기", "중기", "여기")


def _intensity_label(score: int) -> str:
    if score >= 5:
        return "🔴강"
    if score >= 3:
        return "🟠중"
    return "🟡약"


def _pillar_in_native_chong(pk: str, pillars: dict) -> bool:
    nz = pillars[pk]["zhi"]
    for other in PILLAR_KEYS:
        if other == pk:
            continue
        if sw.branch_chong(nz, pillars[other]["zhi"]):
            return True
    return False


def _kong_zhis_union(pillars: dict) -> Set[str]:
    k1, k2 = sn._xunkong_for_pillar(pillars["day"]["pillar"])  # type: ignore[attr-defined]
    ky1, ky2 = sn._xunkong_for_pillar(pillars["year"]["pillar"])  # type: ignore[attr-defined]
    return {k1, k2, ky1, ky2}


def _parse_solar_period_label(label: str) -> Optional[Tuple[date, date]]:
    t = (label or "").strip()
    if "~" not in t:
        return None
    a, b = t.split("~", 1)
    a, b = a.strip(), b.strip()

    def _one(s: str) -> Optional[date]:
        try:
            y, m, d = (int(x) for x in s.split("-"))
            return date(y, m, d)
        except (ValueError, TypeError):
            return None

    da, db = _one(a), _one(b)
    if not da or not db:
        return None
    return da, db


def _unstable_dates_near_jie(cal_year: int) -> Set[date]:
    """절입일 전후 3일(±3) 구간에 포함되는 모든 양력 일자."""
    out: Set[date] = set()
    for cy in (cal_year - 1, cal_year, cal_year + 1):
        row = jq.TERM_TWELVE_BY_YEAR.get(cy)
        if not row:
            continue
        for term_idx, tup in enumerate(row):
            mon, day, _hr, _mn = tup
            yr = cy + 1 if term_idx == 11 else cy
            try:
                jd = date(yr, mon, day)
            except ValueError:
                continue
            for k in range(-3, 4):
                out.add(jd + timedelta(days=k))
    return out


def _precision_chong_rows(
    day_master: str,
    pillars: dict,
    sewoon_zhi: str,
    month_zhi: Optional[str],
) -> Dict[str, Any]:
    """
    충 강도: 원국 충 축 +3, 세운 신규 충 +2, 월운 추가 충 +1.
    합산 6 이상이면 삼중 충으로 최위험 표기.
    """
    rows: List[Dict[str, Any]] = []
    max_score = 0
    triple_hit = False

    for pk in PILLAR_KEYS:
        nz = pillars[pk]["zhi"]
        if not sw.branch_chong(sewoon_zhi, nz):
            continue
        score = 0
        evidence_bits: List[str] = []
        if _pillar_in_native_chong(pk, pillars):
            score += 3
            evidence_bits.append(
                f"{cph.ZHI_LABEL[pk]} {nz}(은)는 원국 안에서 이미 다른 주와 지충 관계라 축이 흔들린 상태입니다."
            )
        score += 2
        evidence_bits.append(f"세운 지지 {sewoon_zhi}(이)가 {cph.ZHI_LABEL[pk]} {nz}와 새로 지충을 겁니다.")
        mz_note = ""
        if month_zhi and sw.branch_chong(month_zhi, nz):
            score += 1
            mz_note = f" 당월 월운 지지 {month_zhi}도 같은 {cph.ZHI_LABEL[pk]}와 충을 겹쳐 레이어가 한 겹 더 붙습니다."
            evidence_bits.append(mz_note.strip())

        if score >= 6:
            triple_hit = True
        max_score = max(max_score, score)

        ev = " ".join(evidence_bits)
        lbl = "🔴강" if score >= 6 else _intensity_label(score)
        if score >= 6:
            evt = (
                f"{cph.ZHI_YUKCHIN_SHORT[pk]} 축에서 이사·이직·계약 해지·부부 갈등·수술·교통 등 "
                f"현실 사건이 한꺼번에 밀려올 수 있는 해(월)입니다."
            )
        elif score >= 4:
            evt = f"{cph.ZHI_YUKCHIN_SHORT[pk]} 관련 변동·건강 긴장이 뚜렷해지기 쉽습니다."
        else:
            evt = f"{cph.ZHI_YUKCHIN_SHORT[pk]} 테마의 일정 조정·합의가 필요할 수 있습니다."

        rows.append(
            {
                "항목": "지충 강도",
                "궁": pk,
                "점수": score,
                "강도표시": lbl,
                "근거": ev + (" → 삼중 충에 해당합니다." if score >= 6 else ""),
                "예상사건": evt,
            }
        )

    summary = "세운과 원국 지지 간 지충 패턴이 없습니다."
    if rows:
        summary = (
            f"지충 발동 {len(rows)}건 · 최고 점수 {max_score}"
            + (" · 삼중 충(6점) 포함" if triple_hit else "")
        )

    return {"요약": summary, "최고점수": max_score, "삼중충": triple_hit, "항목": rows}


def _precision_tougan(day_master: str, pillars: dict, sewoon_gan: str) -> Dict[str, Any]:
    """지장간 간이 세운 천간으로 투출되면 육친·십신 사건 강도 상승."""
    rows: List[Dict[str, Any]] = []
    for pk in PILLAR_KEYS:
        zhi = pillars[pk]["zhi"]
        det = gj.JIJANGGAN_DETAIL.get(zhi, {})
        for slot in _JJG_KEYS:
            hg = det.get(slot)
            if not hg or hg != sewoon_gan:
                continue
            sip = sp.classify_sipsin(day_master, sewoon_gan)
            body = cph.ZHI_BODY.get(zhi, "")
            ev = (
                f"원국 {cph.ZHI_LABEL[pk]} {zhi}의 지장간({slot}) 글자 {hg}(이)가 "
                f"세운 천간 {sewoon_gan}(으)로 투간되어 숨어 있던 기운이 표면으로 드러납니다."
            )
            strong = sip in ("정관", "편관", "정재", "편재", "식신", "상관") or pk == "day"
            lbl = "🔴강" if strong else "🟠중"
            evt = (
                f"{cph.ZHI_YUKCHIN_SHORT[pk]}·{sip} 테마가 활성화되어 "
                f"({body or '신체·환경'}) 쪽으로 구체적 사건·계약·관계 이슈가 붙기 쉽습니다."
            )
            rows.append(
                {
                    "항목": "투간",
                    "궁": pk,
                    "강도표시": lbl,
                    "근거": ev,
                    "예상사건": evt,
                }
            )
    summary = "투간 패턴이 검출되지 않았습니다."
    if rows:
        summary = f"투간 {len(rows)}건 — 지장간 기운이 세운 천간으로 표출됩니다."
    return {"요약": summary, "항목": rows}


def _precision_kongwang_sewoon(day_master: str, pillars: dict, sewoon_gan: str, sewoon_zhi: str) -> Dict[str, Any]:
    """원국 공망 지지가 세운 간지로 들어올 때 해소/강화 성향을 규칙으로 나눕니다."""
    kong = _kong_zhis_union(pillars)
    rows: List[Dict[str, Any]] = []

    if sewoon_zhi in kong:
        sip_sz = sp.classify_sipsin(day_master, gj.jijanggan_ordered(sewoon_zhi)[0])
        # 세운 지지가 공망 글자 자체를 채움 → 현실화 시도 vs 허실 반복을 양면 제시
        ev = (
            f"세운 지지 {sewoon_zhi}(은)는 일간·연간 기준 공망 축에 포함되는 글자와 동일합니다. "
            f"공망 자리가 세운으로 ‘채워지며’ 약속·계약·연애가 현실 검증 구간으로 들어갑니다."
        )
        resolve_like = sip_sz in ("정재", "편재", "정관", "편관")
        lbl = "🟠중"
        evt_resolve = "현금·직장·계약 실체가 드러나며 빈약했던 부분이 보완되거나, 거짓 기대가 깨질 수 있습니다."
        evt_void = "허실·연기·무산 반복으로 같은 공망 주제가 되풀이될 수 있으니 서면·현금 방어가 필요합니다."
        evt = evt_resolve if resolve_like else evt_void
        rows.append(
            {
                "항목": "공망·세운 지지",
                "강도표시": lbl,
                "근거": ev,
                "예상사건": evt + (" (재관 성향으로 보면 해소 쪽 비중을 둡니다.)" if resolve_like else " (공망 강화 쪽도 병행 검토.)"),
            }
        )

    # 공망 축과 세운 지지가 충으로 마주치면 공망 요동
    for kz in kong:
        if sw.branch_chong(sewoon_zhi, kz):
            rows.append(
                {
                    "항목": "공망 요동(충)",
                    "강도표시": "🟠중",
                    "근거": f"세운 지지 {sewoon_zhi}(이) 원국 공망 지지 {kz}와 지충하여 공망 주제가 요동칩니다.",
                    "예상사건": "예정 없던 해외·이직·이별·지출 공백 등 공망 특유의 ‘비어 있음’이 사건으로 표면화될 수 있습니다.",
                }
            )

    summary = "공망과 세운의 특이 결합이 검출되지 않았습니다."
    if rows:
        summary = f"공망 관련 세운 신호 {len(rows)}건입니다."
    return {"요약": summary, "항목": rows}


def _precision_hapgeo(day_master: str, pillars: dict, sewoon_gan: str) -> Dict[str, Any]:
    """세운 천간이 원국 천간과 합하여 해당 십신 역할이 묶이는(합거 성향) 패턴."""
    rows: List[Dict[str, Any]] = []

    for pk in PILLAR_KEYS:
        pg = pillars[pk]["gan"]
        if pg == sewoon_gan:
            continue
        fs = frozenset({pg, sewoon_gan})
        if fs not in cph.CHEON_GAN_HAP_RESULT:
            continue
        elem = cph.CHEON_GAN_HAP_RESULT[fs]
        sip = sp.classify_sipsin(day_master, pg)
        ev = (
            f"{cph.GAN_LABEL[pk]}의 원국 천간 {pg}(과)와 세운 천간 {sewoon_gan}(이) 천간합으로 묶여 "
            f"합화 성향의 오행은 {elem}입니다."
        )
        lbl = "🔴강" if sip in ("정관", "편관", "정재", "편재") else "🟠중"
        if sip in ("정관", "편관"):
            evt = "관성(직장·남편·규범) 역할이 한동안 묶이거나 외연으로 새어 나가 배우자·상사·승진 문제가 표면화될 수 있습니다."
        elif sip in ("정재", "편재"):
            evt = "재성(현금·사업·매매) 흐름이 합에 묶여 수입 구조가 바뀌거나 계약이 지연·통합될 수 있습니다."
        elif sip in ("식신", "상관"):
            evt = "식상(표현·자녀·기술)이 둔화되거나 프로젝트가 합류·정리되는 형국입니다."
        elif sip == "비견":
            evt = "동료·형제 축이 묶여 협력 또는 경쟁 구도가 재편될 수 있습니다."
        elif sip == "겁재":
            evt = "겁재가 묶여 지출·동업 분배에서 손실 또는 재조정 이슈가 생기기 쉽습니다."
        else:
            evt = f"{sip} 십신 축이 천간합으로 영향을 받아 해당 테마가 정체·전환될 수 있습니다."

        rows.append(
            {
                "항목": "천간합거",
                "궁": pk,
                "강도표시": lbl,
                "근거": ev,
                "예상사건": evt,
            }
        )

    # 일간 직접 합
    fs_dm = frozenset({day_master, sewoon_gan})
    if day_master != sewoon_gan and fs_dm in cph.CHEON_GAN_HAP_RESULT:
        elem = cph.CHEON_GAN_HAP_RESULT[fs_dm]
        rows.append(
            {
                "항목": "천간합거(일간)",
                "강도표시": "🔴강",
                "근거": f"일간 {day_master}(과) 세운 천간 {sewoon_gan}(이) 직접 천간합 — 합화 오행 {elem}.",
                "예상사건": "본인 의사·건강·대외 이미지가 끌려 들어가 결혼·제휴·법적 합의 등 ‘나’를 묶는 사건이 강조됩니다.",
            }
        )

    summary = "천간합거로 볼 만한 결합이 없습니다."
    if rows:
        summary = f"천간합거 성향 {len(rows)}건입니다."
    return {"요약": summary, "항목": rows}


def _precision_banghap(pillars: dict, sewoon_zhi: str, month_zhi: Optional[str] = None) -> Dict[str, Any]:
    nat = {pillars[k]["zhi"] for k in PILLAR_KEYS}
    union = set(nat) | {sewoon_zhi}
    if month_zhi:
        union.add(month_zhi)
    rows: List[Dict[str, Any]] = []

    for label, tri, elem in _BANG_GROUPS:
        if not tri <= union:
            continue
        extra_zhis = {sewoon_zhi}
        if month_zhi:
            extra_zhis.add(month_zhi)
        gained = sorted((tri & extra_zhis) - nat)
        ev = (
            f"원국 지지 {''.join(sorted(nat))}에 세운 지지 {sewoon_zhi}"
            + (f"·월운 지지 {month_zhi}" if month_zhi else "")
            + f"가 더해져 {label} 방위 세 지지({''.join(sorted(tri))})가 모두 모였습니다."
        )
        if gained:
            ev += f" (원국에 없던 글자: {''.join(gained)})"
        lbl = "🔴강"
        evt = f"{elem}행 에너지가 단기간에 과포화되어 해당 오행 관련 직업·건강·투자 테마가 급격히 부풀거나 과열합니다."
        rows.append({"항목": "방합", "강도표시": lbl, "근거": ev, "예상사건": evt})

    summary = "방합(사방 삼지 완성) 패턴이 없습니다."
    if rows:
        summary = f"방합 완성 {len(rows)}건 — 해당 방위 오행 과열 신호입니다."
    return {"요약": summary, "항목": rows}


def _precision_jieqi_window(cal_year: int, period_label: str) -> Dict[str, Any]:
    unstable = _unstable_dates_near_jie(cal_year)
    pr = _parse_solar_period_label(period_label)
    if not pr:
        return {
            "불안정_여부": False,
            "강도표시": "",
            "근거": "절월 양력 구간 파싱 실패.",
            "예상사건": "",
        }
    lo, hi = pr
    hits = sorted({d for d in unstable if lo <= d <= hi})
    if not hits:
        return {
            "불안정_여부": False,
            "강도표시": "🟡약",
            "근거": f"{period_label}: 절입 전후 ±3일과 겹치지 않습니다.",
            "예상사건": "절기 경계 밖으로 월운 적용이 비교적 안정적으로 보입니다.",
        }
    lbl = "🟠중"
    ev = (
        f"{period_label} 안에 절기 변환일 인근(±3일)인 "
        f"{', '.join(h.isoformat() for h in hits[:6])}"
        + (" 외 다수" if len(hits) > 6 else "")
        + "이 포함됩니다."
    )
    evt = "월환경이 바뀌는 경계 구간이라 운세 적용·컨디션·일정이 들쭉날쭉할 수 있으니 중요 계약·수술은 전후로 여유를 두는 편이 안전합니다."
    return {"불안정_여부": True, "강도표시": lbl, "근거": ev, "예상사건": evt, "해당일자": [h.isoformat() for h in hits]}


def _precision_pack_sewoon_only(day_master: str, pillars: dict, sewoon_gan: str, sewoon_zhi: str) -> Dict[str, Any]:
    return {
        "충_강도": _precision_chong_rows(day_master, pillars, sewoon_zhi, None),
        "투간": _precision_tougan(day_master, pillars, sewoon_gan),
        "공망_세운": _precision_kongwang_sewoon(day_master, pillars, sewoon_gan, sewoon_zhi),
        "천간합거": _precision_hapgeo(day_master, pillars, sewoon_gan),
        "방합": _precision_banghap(pillars, sewoon_zhi, None),
    }


def _enrich_sewoon_deep_pack(pack: Dict[str, Any], day_master: str, pillars: dict) -> None:
    for row in pack.get("연도별") or []:
        sg = row.get("천간")
        sz = row.get("지지")
        if not sg or not sz:
            continue
        row["정밀분석"] = _precision_pack_sewoon_only(day_master, pillars, sg, sz)


def _enrich_wolwoon_pack(pack: Dict[str, Any], day_master: str, pillars: dict) -> None:
    solar_y = pack.get("세운연도")
    if not solar_y or solar_y not in jq.TERM_TWELVE_BY_YEAR:
        return
    yinfo = sw.yearly_pillar_for_solar_year(int(solar_y))
    sew_zhi = yinfo["zhi"]

    for m in pack.get("월별") or []:
        mz = m.get("월지")
        slot = m.get("절월번호")
        period = m.get("구간_양력") or ""
        if not mz or not slot:
            continue
        jw = _precision_jieqi_window(int(solar_y), period)
        prec: Dict[str, Any] = {
            "충_강도": _precision_chong_rows(day_master, pillars, sew_zhi, mz),
            "방합": _precision_banghap(pillars, sew_zhi, mz),
            "절기_전후_불안정": jw,
        }
        if jw.get("불안정_여부"):
            overlap = m.setdefault("중첩분석", [])
            if isinstance(overlap, list):
                overlap.append(
                    f"🟠 절입 전후 불안정: {jw.get('근거', '')[:120]}"
                    + ("…" if len(str(jw.get("근거", ""))) > 120 else "")
                )
        m["정밀분석"] = prec


def build_report(
    *,
    calendar: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    gender: str,
    lunar_leap: bool = False,
    ya_jasi: bool = False,
    sewoon_center_year: int | None = None,
    wolwoon_center_year: int | None = None,
    partner_day_pillar: str | None = None,
) -> Dict[str, Any]:
    birth = sc.BirthInput(
        calendar=calendar,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lunar_leap=lunar_leap,
        gender=gender,
        ya_jasi=ya_jasi,
    )
    raw = sc.compute_saju(birth)
    ec = raw["_eight_char"]
    pillars = raw["pillars"]
    dm = raw["day_master"]

    counts = oh.count_elements(pillars, include_hidden=True)
    counts_surface = oh.count_elements_surface(pillars)
    counts_hidden = oh.count_elements_hidden_only(pillars)
    gender_male = gender.strip().lower() in ("male", "m", "남", "남자")

    center = sewoon_center_year or datetime.now().year
    # 월운표 기준 연도: 미지정 시 양력 현재 연도(세운 기준연도와 독립)
    wol_center = wolwoon_center_year if wolwoon_center_year is not None else datetime.now().year

    hidden_block = jj.all_hidden_for_pillars(pillars)
    sip_full = sp.full_eight_char_sipsin(dm, pillars, gender)
    hidden_sipsin = {k: sip_full["지지"][k]["hidden"] for k in ("year", "month", "day", "hour")}

    daewoon_block = dw.compute_daewoon(ec, gender_male)
    sew_now = sw.yearly_pillar_for_solar_year(center)
    sewoon_nearby = sw.sewoon_range(center, before=10, after=10)
    chung_report = cph.analyze_branch_relations(
        pillars,
        sewoon_pillar=sew_now["pillar"],
        sewoon_year=center,
        daewoon_cycles=daewoon_block["cycles"],
    )

    yong_block = ys.suggest_useful_gods(
        counts,
        dm,
        pillars["month"]["zhi"],
        pillars=pillars,
        sewoon_nearby=sewoon_nearby,
        sewoon_center_year=center,
    )
    sinsal_block = sn.analyze_sinsal(dm, pillars, gender=gender)

    categories = _build_life_categories(
        day_master=dm,
        pillars=pillars,
        gender=gender,
        counts=counts,
        yong=yong_block,
        sinsal=sinsal_block,
        sewoon_nearby=sewoon_nearby,
        daewoon_cycles=daewoon_block["cycles"],
        partner_day_pillar=partner_day_pillar,
    )

    sew_deep = sw.sewoon_forecast_pack(
        dm, pillars, gender, center_year=center, span=10, counts=counts
    )
    _enrich_sewoon_deep_pack(sew_deep, dm, pillars)

    wol_pack = ww.wolwoon_year_pack(dm, pillars, wol_center, gender=gender, counts=counts)
    _enrich_wolwoon_pack(wol_pack, dm, pillars)

    il_pack = il.ilwoon_snapshot_pack(dm, pillars)
    timeline_pack = tl.build_timeline_pack(
        dm,
        pillars,
        gender,
        counts,
        birth_year=year,
        daewoon_cycles=daewoon_block["cycles"],
        yong_block=yong_block,
        current_year=center,
    )

    sewoon_list: List[Dict[str, Any]] = list(sew_deep.get("연도별") or [])
    wolwoon_list: List[Dict[str, Any]] = list(wol_pack.get("월별") or [])
    jeongmil: Dict[str, Any] = {
        "sewoon": [{"연도": row.get("연도"), "정밀분석": row.get("정밀분석")} for row in sewoon_list],
        "wolwoon": [
            {"절월번호": m.get("절월번호"), "정밀분석": m.get("정밀분석")} for m in wolwoon_list
        ],
    }

    report: Dict[str, Any] = {
        "meta": {
            "gender_for_daewoon": "남성" if gender_male else "여성",
            "sewoon_center_applied": center,
            "wolwoon_center_applied": wol_center,
        },
        "solar": raw["solar"],
        "lunar": raw["lunar"],
        "lunar_leap_month": raw["is_leap_month"],
        "jieqi_embedded_year": raw.get("jieqi_embedded_year"),
        "day_anchor_note": raw.get("day_anchor_note"),
        "pillars": pillars,
        "eight_char_string": raw["eight_char_string"],
        "day_master": raw["day_master"],
        "day_master_kr": raw["day_master_kr"],
        "day_master_element": raw["day_master_element"],
        "ohaeng": {
            "counts": counts,
            "counts_surface": counts_surface,
            "counts_hidden": counts_hidden,
            "summary_lines": oh.element_summary(counts),
            "dominant_weak": oh.dominant_weak_elements(counts),
        },
        "sipsin_full": sip_full,
        "sipsin_stems": sip_full["천간"],
        "jijanggan": hidden_block,
        "sipsin_hidden": hidden_sipsin,
        "sibiunsung": sb.pillar_twelve_stages(dm, pillars),
        "chung_pa_hae": chung_report,
        "sinsal": sinsal_block,
        "daewoon": daewoon_block,
        "sewoon_nearby": sewoon_nearby,
        "세운_심층": sew_deep,
        "월운표": wol_pack,
        "일운": il_pack,
        "통합_타임라인": timeline_pack,
        # 영문 키 (프론트·외부 연동용; 통합 API 유지)
        "sewoon": sewoon_list,
        "wolwoon": wolwoon_list,
        "ilwoon": il_pack,
        "timeline": timeline_pack,
        "jeongmil": jeongmil,
        "yongsin": yong_block,
        "분석_카테고리": categories,
        "원국_스토리텔링": _build_native_story_pack(
            day_master=dm,
            pillars=pillars,
            gender=gender,
            counts=counts,
            yong=yong_block,
            sinsal=sinsal_block,
            daewoon_cycles=daewoon_block["cycles"],
        ),
        "narrative": _compose_narrative(raw, counts, gender_male,
                                        yong=yong_block,
                                        chung_report=chung_report),
    }
    return report


def _compose_narrative(
    raw: Dict[str, Any],
    counts: Dict[str, int],
    gender_male: bool,
    *,
    yong: Optional[Dict[str, Any]] = None,
    chung_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    p = raw["pillars"]
    gender_kr = "남성" if gender_male else "여성"
    lines: List[str] = [
        f"원국 사주는 연월일시가 각각 {p['year']['pillar']}, {p['month']['pillar']}, "
        f"{p['day']['pillar']}, {p['hour']['pillar']}입니다.",
        f"일간은 {raw['day_master']}({raw['day_master_kr']})로 오행은 {raw['day_master_element']}입니다.",
        f"오행 개수(지장간 포함)는 목·화·토·금·수 순으로 "
        f"{counts['목']}, {counts['화']}, {counts['토']}, {counts['금']}, {counts['수']}입니다.",
        f"대운은 입력하신 성별({gender_kr})과 생시를 바탕으로 전통 순역 규칙을 적용하여 계산했습니다.",
    ]

    # 용신·강약 요약
    if yong:
        gangak = yong.get("일간_강약") or "중화"
        yong_el = yong.get("용신_오행") or ""
        hee_el = yong.get("희신_오행") or ""
        gi_el = yong.get("기신_오행") or ""
        lines.append(
            f"일간은 {gangak}으로, 용신은 {yong_el}"
            + (f" · 희신 {hee_el}" if hee_el else "")
            + (f" · 기신 {gi_el}" if gi_el else "")
            + "입니다."
        )
        out_sen = yong.get("출력_문장") or {}
        for k in ("용신", "희신", "기신"):
            val = (out_sen.get(k) or "").strip()
            if val and val != "—":
                lines.append(val)

    # 원국 충파해 핵심 요약
    if chung_report:
        detail = chung_report.get("관계_상세_전체") or []
        native = [r for r in detail
                  if isinstance(r, dict) and str(r.get("분류", "")).startswith("원국")]
        if not native:
            native = detail
        for row in native[:4]:
            rel = row.get("관계", "")
            gz = row.get("글자", "")
            pos = row.get("위치", "")
            desc = str(row.get("해석", "") or "").strip()
            if rel and gz and desc:
                lines.append(f"▸ 원국 {rel}({gz}, {pos}): {desc[:70]}")

    return {
        "bullets": "\n".join(lines),
        "hint": "세부 해석은 명리학 파종과 상담자 관점에 따라 달라질 수 있습니다.",
    }
