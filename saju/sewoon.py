# -*- coding: utf-8 -*-
"""
세운(流年) 심층 분석 — 연도별 간지와 원국의 천간·지지 작용,
육친 궁 해석, 사건 휴리스틱, 길흉·별점까지 묶어 제공합니다.

• 기준 연도 ±span(기본 10) → 총 2*span+1년 (기본 21년)
• 명리 파종마다 세부 해석이 달라질 수 있으며, 본 모듈은 규칙 기반 참고용입니다.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from lunar_python import Solar

from . import chung_pa_hae as cph
from . import ganji as gj
from . import sipsin as sp
from . import sinsal as sn
from .chung_pa_hae import CHEON_GAN_HAP_RESULT, ZHI_BODY, ZHI_YUKCHIN_SHORT
from .yongsin import CONTROL_MAP, RESOURCE_MAP

_ELEM_CYCLE: Tuple[str, ...] = ("목", "화", "토", "금", "수")

# 참고용: 오행 과다·결핍 시 흔히 엮는 신체·질환 힌트(명리 파종·의학과 무관)
_ELEM_ORGAN_HINTS: Dict[str, str] = {
    "목": "간·담·근육·관절·눈 피로",
    "화": "심장·소화·혈압·순환·불면",
    "토": "비위·췌장·당대사·피부",
    "금": "폐·대장·기관지·피부·치아",
    "수": "신장·방광·생식·하체·불면",
}

_ELEM_DISEASE_EXAMPLES: Dict[str, str] = {
    "목": "간수치·근막통·안구건조",
    "화": "고혈압·부정맥·위염",
    "토": "당뇨경향·위장장애·피부염",
    "금": "호흡기·알레르기·치주",
    "수": "신장결석·방광염·부종",
}

_ELEM_SCREENING: Dict[str, str] = {
    "목": "간기능·안저·근골격 초음파",
    "화": "심전도·혈압·위내시경",
    "토": "혈당·지방간·피부과 검진",
    "금": "흉부X선·폐기능·치과",
    "수": "요·신장 초음파·소변검사",
}

_DIRECTION_COMFORT: Dict[str, str] = {"목": "동쪽", "화": "남쪽", "토": "중앙·낮은 산", "금": "서쪽", "수": "북쪽"}
_ELEM_COLOR_COMFORT: Dict[str, str] = {
    "목": "청록·목색 액세서리",
    "화": "옅은 화색 포인트",
    "토": "베이지·황토 톤",
    "금": "백색·금속 액세서리",
    "수": "남색·검정 포인트",
}


def _wealth_element(dm_elem: str) -> str:
    """일간 오행이 극하는 오행(재성 방향)."""
    i = _ELEM_CYCLE.index(dm_elem)
    return _ELEM_CYCLE[(i + 2) % 5]


PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")
ZHI_LABEL = cph.ZHI_LABEL
GAN_LABEL = cph.GAN_LABEL

STEM_CHONG_SET: Set[frozenset] = frozenset(
    {
        frozenset({"甲", "庚"}),
        frozenset({"乙", "辛"}),
        frozenset({"丙", "壬"}),
        frozenset({"丁", "癸"}),
    }
)


def yearly_pillar_for_solar_year(year: int) -> Dict[str, str]:
    solar = Solar.fromYmd(year, 6, 1)
    lunar = solar.getLunar()
    gz = lunar.getYearInGanZhiExact()
    gan, zhi = gz[0], gz[1]
    pillar = gz
    return {
        "year": year,
        "gan": gan,
        "zhi": zhi,
        "pillar": pillar,
        "label_kr": gj.pillar_label_kr(gan, zhi),
        "nayin": gj.nayin_for_pillar(pillar),
    }


def sewoon_range(center_year: int, before: int = 5, after: int = 10) -> List[Dict[str, str]]:
    return [yearly_pillar_for_solar_year(y) for y in range(center_year - before, center_year + after + 1)]


def _pair_sorted(z1: str, z2: str) -> Tuple[str, str]:
    return tuple(sorted((z1, z2)))  # type: ignore[return-value]


def _chong_set() -> Set[Tuple[str, str]]:
    return {_pair_sorted(a, b) for a, b in gj.CHONG_PAIRS}


def _po_set() -> Set[Tuple[str, str]]:
    return {_pair_sorted(a, b) for a, b in gj.LIU_PO}


def _hai_set() -> Set[Tuple[str, str]]:
    return {_pair_sorted(a, b) for a, b in gj.LIU_HAI}


def _liu_he_set() -> Set[Tuple[str, str]]:
    return {_pair_sorted(a, b) for a, b in gj.LIU_HE}


def branch_chong(z1: str, z2: str) -> bool:
    return _pair_sorted(z1, z2) in _chong_set()


def branch_po(z1: str, z2: str) -> bool:
    return _pair_sorted(z1, z2) in _po_set()


def branch_hai(z1: str, z2: str) -> bool:
    return _pair_sorted(z1, z2) in _hai_set()


def branch_liu_he(z1: str, z2: str) -> bool:
    return _pair_sorted(z1, z2) in _liu_he_set()


def stem_chong(g1: str, g2: str) -> bool:
    return frozenset((g1, g2)) in STEM_CHONG_SET


def _xing_pair_label(a: str, b: str) -> Optional[str]:
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


def _sipsin_counter(day_master: str, pillars: dict) -> Counter[str]:
    c: Counter[str] = Counter()
    for pk in PILLAR_KEYS:
        gans = [pillars[pk]["gan"]] + gj.jijanggan_ordered(pillars[pk]["zhi"])
        for gan in gans:
            if gan == day_master:
                continue
            c[sp.classify_sipsin(day_master, gan)] += 1
    return c


def _peach_marker(year_zhi: str) -> str:
    _, doh, _ = sn._yeolma_dohwa_hwagae(year_zhi)  # type: ignore[attr-defined]
    return doh


def _stars_from_score(score: float) -> Tuple[str, int]:
    """점수·별 개수(1~5)."""
    if score >= 72:
        return ("길운", 5)
    if score >= 58:
        return ("길운", 4)
    if score >= 46:
        return ("보통", 3)
    if score >= 34:
        return ("흉운", 2)
    return ("흉운", 1)


def _rating_bar(n: int) -> str:
    n = max(1, min(5, n))
    return "★" * n + "☆" * (5 - n)


def _elem_delta_note(dm: str, sg: str, sz: str, counts: Optional[Dict[str, int]]) -> str:
    dm_el = gj.element_of_stem(dm)
    ingan_el = gj.element_of_stem(sg)
    izhi_el = gj.element_of_branch(sz)
    lines = [
        f"일간 오행 {dm_el}, 세운 천간·지지 오행은 {ingan_el}·{izhi_el}입니다.",
        f"세운이 일간을 생하는 방향인지·설기·재·관 방향인지로 세운 에너지를 가늠합니다.",
    ]
    if counts:
        weak = oh_weak_strong(counts)
        lines.append(f"원국 분포 참고: 상대 과다 {weak[0]}, 부족 {weak[1]}.")
    return " ".join(lines)


def oh_weak_strong(counts: Dict[str, int]) -> Tuple[str, str]:
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    strong = items[0][0] if items else ""
    weak = items[-1][0] if items else ""
    return strong, weak


def _san_he_notes(native_zhis: Dict[str, str], sz: str) -> List[str]:
    zset = set(native_zhis.values())
    notes: List[str] = []
    for tri, nation in gj.SAN_HE_GROUPS:
        if sz not in tri:
            continue
        inner = zset & tri
        if tri <= zset:
            notes.append(f"{nation} 삼합이 원국에 이미 두텁게 깔려 세운 {sz}(으)로 같은 성향이 재자극됩니다.")
        elif len(inner) == 2:
            notes.append(f"{nation} 삼합 두 지({''.join(sorted(inner))})에 세운 지지 {sz}가 들어와 삼합 결실 방향으로 움직일 수 있습니다.")
        elif len(inner) == 1:
            notes.append(f"{nation} 삼합 반합 성향: 원국 한 지와 세운 {sz}가 끌어당김.")
    return notes


def _stem_union_notes(dm: str, sg: str, pillars: dict) -> Tuple[List[str], bool, bool]:
    """천간합 줄 목록, 재성합·관성합 여부."""
    hap_lines: List[str] = []
    wealth_hap = False
    guan_hap = False
    for pk in PILLAR_KEYS:
        pg = pillars[pk]["gan"]
        if pg == dm:
            continue
        fs = frozenset((sg, pg))
        if fs not in CHEON_GAN_HAP_RESULT:
            continue
        elem = CHEON_GAN_HAP_RESULT[fs]
        sip = sp.classify_sipsin(dm, pg)
        hap_lines.append(
            f"{GAN_LABEL[pk]} {pg}와 세운 천간 {sg}: 천간합 → 화기 성향 {elem} · 원글자 십신 {sip}"
        )
        if sip in ("편재", "정재"):
            wealth_hap = True
        if sip in ("정관", "편관"):
            guan_hap = True
            hap_lines[-1] += " · 관운·직장 인연 신호로 함께 봅니다."
    return hap_lines, wealth_hap, guan_hap


def _stem_clash_notes(sg: str, pillars: dict) -> List[str]:
    lines: List[str] = []
    for pk in PILLAR_KEYS:
        pg = pillars[pk]["gan"]
        if stem_chong(sg, pg):
            lines.append(f"{GAN_LABEL[pk]} {pg}와 세운 천간 {sg}: 천간충·극렬 변동 신호.")
    return lines


def _stem_geuk_pressure(dm: str, sg: str) -> List[str]:
    """세운 천간 십신이 관살 위주일 때 압박 서술."""
    sip = sp.classify_sipsin(dm, sg)
    if sip in ("편관", "정관"):
        return [f"세운 천간 십신이 {sip}(관살)로 규범·상사·건강 스트레스 축을 의식합니다."]
    if sip == "겁재":
        return [f"세운 천간이 겁재로 동업·경쟁·지출 변수가 커질 수 있습니다."]
    return []


def _resource_element(dm_elem: str) -> str:
    i = _ELEM_CYCLE.index(dm_elem)
    return _ELEM_CYCLE[(i + 1) % 5]


def _monthly_focus_risks(
    day_master: str,
    pillars: dict,
    solar_year: int,
    sewoon_zhi: str,
) -> List[Dict[str, Any]]:
    """절월별 세운·월운 중첩 위험 요약 (규칙 기반)."""
    from . import wolwoon as ww

    out: List[Dict[str, Any]] = []
    for slot in range(1, 13):
        m = ww.analyze_wolwoon_month(day_master, pillars, solar_year, slot)
        flags = m.get("중첩플래그") or {}
        grade = m.get("길흉판정") or ""
        rel = m.get("원국_충파해합형") or {}
        cph = sum(len(rel.get(k, [])) for k in ("충", "파", "해"))
        mz = m.get("월지") or ""
        dual = bool(flags.get("세운월운_동시충"))
        fuy = bool(flags.get("세운월운_복음"))
        heavy_chong = sewoon_zhi == mz and dual

        badge = ""
        if (dual and fuy) or (cph >= 3 and dual):
            badge = "🔴 최위험"
        elif dual or grade == "대흉우려" or (fuy and cph >= 1):
            badge = "🟠 위험"
        elif cph >= 2 or grade == "약흉":
            badge = "🟡 주의"
        else:
            continue

        ov = (m.get("중첩분석") or [])[:2]
        detail = " · ".join(ov) if ov else (m.get("한줄요약") or "")
        label = f"{m.get('절월번호')}절월({m.get('월지')}월·{m.get('월주간지', '')})"
        example = f"{label}: {detail}"[:120]
        if heavy_chong:
            example += " → 세운·월운 이중 충·복음에 가까운 패턴으로 긴장 극대."

        out.append(
            {
                "절월번호": m.get("절월번호"),
                "월지": mz,
                "월주간지": m.get("월주간지"),
                "등급": badge,
                "구간_양력": m.get("구간_양력"),
                "요약": example,
                "길흉판정": grade,
            }
        )
    return out


def _rank_body_parts(br_chong: List[Dict[str, str]], sz: str, sg: str, day_zhi: str) -> List[str]:
    parts: List[str] = []
    for row in br_chong:
        b = (row.get("신체") or "").strip()
        if b:
            parts.append(b)
    parts.append(ZHI_BODY.get(day_zhi, ""))
    uniq: List[str] = []
    for p in parts:
        for seg in p.replace("·", ",").split(","):
            t = seg.strip()
            if t and t not in uniq:
                uniq.append(t)
        if len(uniq) >= 5:
            break
    if len(uniq) < 3:
        uniq.append(_ELEM_ORGAN_HINTS.get(gj.element_of_branch(sz), ""))
    return [x for x in uniq if x][:3]


def _health_detail_pack(
    *,
    day_master: str,
    br_chong: List[Dict[str, str]],
    sz: str,
    sg: str,
    day_zhi: str,
    counts: Optional[Dict[str, int]],
    baekho_hit: bool,
    yangin_hit: bool,
    day_chong: bool,
    pianyin_heavy: bool,
) -> Dict[str, Any]:
    dm_el = gj.element_of_stem(day_master)
    sz_el = gj.element_of_branch(sz)
    sg_el = gj.element_of_stem(sg)
    ranked = _rank_body_parts(br_chong, sz, sg, day_zhi)
    order_txt = " · ".join(
        [f"① {ranked[0]}"]
        + ([f"② {ranked[1]}"] if len(ranked) > 1 else [])
        + ([f"③ {ranked[2]}"] if len(ranked) > 2 else [])
    )
    elem_notes: List[str] = []
    if counts:
        strong, weak = oh_weak_strong(counts)
        elem_notes.append(
            f"오행 분포상 과다는 「{strong}」, 부족은 「{weak}」 축입니다. "
            f"과다 연결 참고: {_ELEM_DISEASE_EXAMPLES.get(strong, '만성 피로·스트레스')}; "
            f"부족 연결 참고: {_ELEM_DISEASE_EXAMPLES.get(weak, '저항력·회복력')}."
        )
    elem_notes.append(
        f"세운 표면 오행은 천간 {sg_el}·지지 {sz_el}로 {_ELEM_ORGAN_HINTS.get(sz_el, '신체 리듬')} 쪽 자극이 커질 수 있습니다."
    )
    surg: List[str] = []
    if baekho_hit:
        surg.append("백호살 연계 시 금속·외상·개복·출혈 리스크를 참고용으로 둡니다.")
    if yangin_hit:
        surg.append("양인살 동반 시 급작스런 상해·수술 얘기가 동시에 붙기 쉽습니다.")
    if day_chong:
        surg.append("일지 충은 내실·배우자 건강 검진을 당겨 보는 편이 안전합니다.")
    screens = sorted({t for t in (_ELEM_SCREENING.get(sz_el, ""), _ELEM_SCREENING.get(sg_el, "")) if t})
    return {
        "위험부위_순위": ranked,
        "위험부위_문장": order_txt or "① 종합 검진으로 우선순위 확인 권장",
        "오행_메모": " ".join(elem_notes),
        "수술_사고_가능성": surg if surg else ["특이 신살·일지충 미발동으로 급성 리스크는 상대적으로 낮게 볼 수 있음(참고)"],
        "권장_검진": " · ".join(screens) if screens else "기본 건강검진·혈압·혈당 정기 점검",
    }


def _yukchin_blocks_v2(
    day_master: str,
    pillars: dict,
    zhis: Dict[str, str],
    sg: str,
    sz: str,
    sip_sg: str,
    sip_sz_approx: str,
    events: Dict[str, bool],
) -> Dict[str, Any]:
    """배우자·부모·자녀·직장 사회 축 상세."""
    day_z = zhis["day"]
    year_z = zhis["year"]
    hour_z = zhis["hour"]
    month_z = zhis["month"]

    def rel_bits(pk: str) -> List[str]:
        nz = zhis[pk]
        b: List[str] = []
        if branch_chong(sz, nz):
            b.append("충")
        if branch_po(sz, nz):
            b.append("파")
        if branch_hai(sz, nz):
            b.append("해")
        if branch_liu_he(sz, nz):
            b.append("육합")
        return b or ["해당 없음"]

    ins_star_year = sp.classify_sipsin(day_master, pillars["year"]["gan"])
    officer_month_touch = branch_chong(sz, month_z) or branch_po(sz, month_z)
    spouse_pred = (
        "배우자와 의견 충돌이 잦아지거나 거리두기·별거 주제가 올라올 수 있습니다."
        if events.get("이별_이혼") or branch_chong(sz, day_z)
        else "배우자 관계는 큰 파열 없이 유지되나 대화 피로는 의식하는 편이 좋습니다."
    )
    parent_pred = (
        "모친·부친 건강 또는 윗대 건강 이슈로 병원 동선이 생기기 쉽습니다."
        if events.get("부모우환") or branch_chong(sz, year_z)
        else "부모·환경 축은 무난하지만 생활 습관 점검은 유지하세요."
    )
    child_pred = (
        "자녀 학업·진로·표현 문제로 마음 쓸 일이 늘거나 작은 갈등이 반복될 수 있습니다."
        if branch_chong(sz, hour_z) or sip_sz_approx in ("식신", "상관")
        else "자녀·창작 축은 평년 대비 소폭 변수만 두면 충분합니다."
    )
    career_pred = (
        "이직·조직 이동을 검토하기 쉬운 해이며 상사·규정과 마찰 여지가 있습니다."
        if events.get("실직_이직") or officer_month_touch
        else "직장은 안정 쪽에 가깝되 성과 압박만 과하면 번아웃 소인은 있습니다."
    )

    return {
        "배우자": {
            "일지_상태": "·".join(rel_bits("day")),
            "세운_십신_작용": f"세운 천간 십신 {sip_sg}(은) 일간 대비 배우자·계약 축에 해당하는 작용으로 외연 변화와 연결해 봅니다.",
            "예측": spouse_pred,
        },
        "부모": {
            "년지_상태": "·".join(rel_bits("year")),
            "인성_세운_작용": f"년간 원국 십신 {ins_star_year}와 세운 {sip_sg}가 부모·환경 축을 어떻게 밀지 함께 봅니다.",
            "예측": parent_pred,
        },
        "자녀": {
            "시지_상태": "·".join(rel_bits("hour")),
            "식상_세운_작용": f"세운 지지 본기 십신 근사 {sip_sz_approx}(은) 자녀·표현·기술 축 에너지로 연결합니다.",
            "예측": child_pred,
        },
        "직장_사회": {
            "월지_상태": "·".join(rel_bits("month")),
            "관성_세운_작용": f"세운 천간 십신 {sip_sg}(이) 관성 계열이면 직장·상사 테마가 표면화하기 쉽습니다.",
            "예측": career_pred,
        },
    }


def _story_summary_line(
    solar_year: int,
    pillar_full: str,
    sg: str,
    sz: str,
    zhis: Dict[str, str],
    br_chong: List[Dict[str, str]],
    fan_yin_heavy: bool,
    day_chong: bool,
) -> str:
    sg_el = gj.element_of_stem(sg)
    sz_el = gj.element_of_branch(sz)
    core = (
        f"{solar_year}년 {pillar_full}은 세운에 {sg_el}·{sz_el} 기운이 겹쳐 들어오며, "
        f"원국과의 긴장도는 {'상당히 높은 편' if fan_yin_heavy else '평년 대비 한 단계 위'}입니다."
    )
    extras: List[str] = []
    if day_chong:
        extras.append(
            f"{ZHI_LABEL['day']}{zhis['day']}과 세운 {sz}가 맞부딪혀 부부·내실·건강 이슈가 표면화하기 쉽습니다."
        )
    if br_chong:
        ch = br_chong[0]
        extras.append(
            f"{ch.get('글자', '')} 충으로 {ch.get('육친궁', '')} 축에서 직업·부부 갈등처럼 현실 사건이 동시에 묶여 나올 수 있습니다."
        )
    if sz_el == "화":
        extras.append("화기운이 들어와 심혈관·순환·불면 등 긴장 신호를 의식하는 편이 좋습니다.")
    elif sz_el == "수":
        extras.append("수기운이 들어와 신장·하체·불면 리듬 변동을 함께 봅니다.")
    tail = " ".join(extras)
    return (core + (" " + tail if tail else "")).strip()


def _wealth_narrative_v2(
    sip_sg: str,
    events: Dict[str, bool],
    wealth_hap_flag: bool,
    geobjae_year: bool,
    rex_chong_any: bool,
    sz: str,
    day_master: str,
) -> str:
    cheon_set = sn._cheoneul(day_master)  # type: ignore[attr-defined]
    windfall = bool(sip_sg == "편재" and sz in cheon_set)
    parts: List[str] = []
    if events.get("재물획득") or wealth_hap_flag:
        parts.append("상반기보다 하반기로 갈수록 재성 합·유입 신호가 생길 여지가 있습니다.")
    else:
        parts.append("현금 흐름은 평년 대비 들쭉날쭉할 수 있어 고정 지출 비중을 낮추는 편이 안전합니다.")
    if windfall:
        parts.append("편재 성향에 천을 귀인 지지가 맞물려 단기 보너스·횡재 기회가 스치나 검증 없는 확장은 금물입니다.")
    if geobjae_year or rex_chong_any or events.get("손재_도난"):
        parts.append("겁재 세운 또는 재 자리 충파로 손재·동업 분배 리스크가 있어 투자·보증은 보류 권장입니다.")
    else:
        parts.append("손재 신호가 약하면 소액 분산만 허용하고 레버리지는 피합니다.")
    return " ".join(parts)


def _career_narrative_v2(events: Dict[str, bool], sip_sg: str, samxing_alert: bool, officer_chong_month: bool) -> str:
    parts: List[str] = []
    if events.get("취업_승진"):
        parts.append("관성·합으로 승진·제안 러브콜 가능성이 있으나 충이 있으면 조건 재확인이 필요합니다.")
    if events.get("실직_이직") or officer_chong_month:
        parts.append("2~3분기 전후 이직·조직 개편 변수가 커지며 충동적 사직은 피하는 편이 좋습니다.")
    if not parts:
        parts.append("직장은 큰 이동 없이 업무 강도만 관리하면 균형을 유지하기 쉽습니다.")
    if samxing_alert or events.get("관재구설"):
        parts.append("삼형·관재 신호가 있으면 구설·계약 분쟁에 시간이 새어 나갈 수 있습니다.")
    return " ".join(parts)


def _love_narrative_v2(
    peach_hit: bool,
    day_chong: bool,
    events: Dict[str, bool],
    gender: str,
) -> str:
    female = gender.strip().lower() in ("female", "f", "여", "여성", "여자")
    parts: List[str] = []
    if peach_hit:
        parts.append("도화살 기운이 세운과 맞물려 이성 접촉은 늘지만 일지 충이 가까우면 깊은 관계까지 가기 전 변동이 큽니다.")
    elif events.get("연애_결혼"):
        parts.append("합·관성 신호로 만남이 생길 수 있으나 급결혼보다 상황 확인을 권합니다.")
    else:
        parts.append("만남 신호는 평년과 비슷하며 자기 돌봄에 에너지를 두는 편이 안정적입니다.")
    if day_chong or events.get("이별_이혼"):
        parts.append("기혼이라면 대화 리듬을 맞추지 않으면 거리두기·별거 논의가 표면화하기 쉽습니다.")
    parts.append("(미혼) 인연은 생기더라도 내실 정리 후 진행할 때 길합니다." if not day_chong else "(미혼) 연애보다 관계 정리 쪽 에너지가 강해질 수 있습니다.")
    _ = female  # 향후 성별 특화 문구 확장용
    return " ".join(parts)


def _luck_and_caution_kw(
    dm_el: str,
    sg: str,
    sz: str,
    luck_word: str,
    fan_yin_heavy: bool,
) -> Tuple[List[str], List[str]]:
    se_elems = {gj.element_of_stem(sg), gj.element_of_branch(sz)}
    luck: List[str] = []
    caution: List[str] = []
    # 부족 오행 보완을 행운으로 단순 매핑
    comfort_el = RESOURCE_MAP.get(dm_el, dm_el)
    luck.append(f"{_DIRECTION_COMFORT.get(comfort_el, '친숙한 방향')} 여행·산책")
    luck.append(f"{_ELEM_COLOR_COMFORT.get(comfort_el, '차분한 색')} 착용")
    luck.append(f"{_ELEM_COLOR_COMFORT.get(_wealth_element(dm_el), '재성 방향 소품')} 재물 포인트")
    if "화" in se_elems:
        caution.extend(["남쪽 장거리 이동 과다", "과음·야근으로 화기 과열", "충동 계약"])
    if "수" in se_elems:
        caution.extend(["야간 수분 과다", "저체온·졸음 운전"])
    if fan_yin_heavy:
        caution.append("동시에 여러 축을 건드리는 확장·이사·결별 결정")
    if luck_word == "흉운":
        caution.append("레버리지 투자·연대보증")
    return luck[:6], caution[:6]


def _closing_one_liner(luck_word: str, day_chong: bool, fan_yin_strict: bool, events: Dict[str, bool]) -> str:
    if fan_yin_strict:
        return "네 방향이 동시에 요동치는 해입니다. 새 출발보다 방어·건강·현금 확보를 최우선으로 삼으세요."
    if day_chong:
        return "버티는 해입니다. 확장보다 내실을 다지고 배우자·건강 검진을 최우선으로 하세요."
    if luck_word == "길운" and not events.get("손재_도난"):
        return "기회가 들어오는 해입니다. 과욕만 줄이면 성과와 인연을 함께 가져갈 수 있습니다."
    return "무리한 변화보다 리스크 관리와 컨디션 유지가 전체 운을 좌우하는 해입니다."


def _compute_health_domain_score(
    day_chong: bool,
    baekho_hit: bool,
    yangin_hit: bool,
    pianyin_heavy: bool,
    br_chong: List[Dict[str, str]],
    br_he: List[Dict[str, str]],
) -> float:
    h = 50.0
    h -= 22 if day_chong else 0
    h -= 10 * len([x for x in br_chong if x.get("궁") == "month"])
    h -= 14 if baekho_hit else 0
    h -= 12 if yangin_hit else 0
    h -= 10 if pianyin_heavy else 0
    h += 8 * len([x for x in br_he if x.get("궁") == "day"])
    return h


def analyze_sewoon_year(
    day_master: str,
    pillars: dict,
    gender: str,
    solar_year: int,
    *,
    counts: Optional[Dict[str, int]] = None,
    native_sinsal: Optional[Dict[str, Any]] = None,
    sip_ctr: Optional[Counter[str]] = None,
) -> Dict[str, Any]:
    """
    단일 연도 세운 심층 분석 결과(dict).

    ``native_sinsal``: 원국 ``analyze_sinsal`` 결과를 넘기면 내부에서 신살 재계산을 생략합니다.
    ``sip_ctr``: 원국 전체 십신 카운터(천간+지장간)를 넘기면 재계산 생략.
    """
    sw = yearly_pillar_for_solar_year(solar_year)
    sg, sz = sw["gan"], sw["zhi"]
    pillar_full = sw["pillar"]

    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    gans = {k: pillars[k]["gan"] for k in PILLAR_KEYS}
    nat_pillar = {k: pillars[k]["pillar"] for k in PILLAR_KEYS}

    sip_sg = sp.classify_sipsin(day_master, sg)
    main_hidden = gj.jijanggan_ordered(sz)[0]
    sip_sz_approx = sp.classify_sipsin(day_master, main_hidden)

    inj_rows = cph.analyze_sewoon_injection(pillars, pillar_full, sewoon_year=solar_year)

    # --- 지지별 충·파·해·형·합·복음 ---
    br_chong: List[Dict[str, str]] = []
    br_po: List[Dict[str, str]] = []
    br_hai: List[Dict[str, str]] = []
    br_xing: List[Dict[str, str]] = []
    br_he: List[Dict[str, str]] = []
    fuyin_lines: List[str] = []

    for pk in PILLAR_KEYS:
        nz = zhis[pk]
        lab = ZHI_LABEL[pk]
        yuk_short = ZHI_YUKCHIN_SHORT[pk]
        body = ZHI_BODY.get(nz, "")
        if branch_chong(sz, nz):
            br_chong.append(
                {
                    "궁": pk,
                    "위치": lab,
                    "글자": f"{sz}{nz}",
                    "육친궁": yuk_short,
                    "신체": body,
                    "해석": f"{lab}({nz})와 세운 지지 {sz}가 충하여 {yuk_short}·{body} 축 요동.",
                }
            )
        if branch_po(sz, nz):
            br_po.append(
                {
                    "궁": pk,
                    "위치": lab,
                    "글자": f"{sz}×{nz}",
                    "육친궁": yuk_short,
                    "신체": body,
                    "해석": f"{lab} 파형 무너짐이 생길 수 있습니다.",
                }
            )
        if branch_hai(sz, nz):
            br_hai.append(
                {
                    "궁": pk,
                    "위치": lab,
                    "글자": f"{sz}×{nz}",
                    "육친궁": yuk_short,
                    "신체": body,
                    "해석": f"{lab} 육해로 은근한 시기·건강 피로.",
                }
            )
        xt = _xing_pair_label(sz, nz)
        if xt:
            br_xing.append(
                {
                    "궁": pk,
                    "위치": lab,
                    "글자": f"{sz}{nz}",
                    "유형": xt,
                    "육친궁": yuk_short,
                    "신체": body,
                    "해석": f"{lab} 형살({xt})로 긴장·관재·외상 소인.",
                }
            )
        if branch_liu_he(sz, nz):
            br_he.append(
                {
                    "궁": pk,
                    "위치": lab,
                    "유형": "육합",
                    "글자": f"{sz}{nz}",
                    "육친궁": yuk_short,
                    "해석": f"{lab} 육합 인연으로 끌림이 생깁니다.",
                }
            )

        if sz == nz:
            fuyin_lines.append(f"{lab}({nz})와 세운 지지 {sz} 복음: 같은 글자 반복으로 {yuk_short}·{body} 과제 재등장.")

        if pillar_full == nat_pillar[pk]:
            fuyin_lines.append(f"{lab} 전체 간지 복음({pillar_full}): 해당 주 테마가 크게 되풀이됩니다.")

    san_he_lines = _san_he_notes(zhis, sz)

    conflict_positions = sum(
        1
        for pk in PILLAR_KEYS
        if branch_chong(sz, zhis[pk]) or branch_po(sz, zhis[pk]) or branch_hai(sz, zhis[pk])
    )
    fan_yin_heavy = conflict_positions >= 3
    fan_yin_strict = all(branch_chong(sz, zhis[pk]) for pk in PILLAR_KEYS)

    day_chong = branch_chong(sz, zhis["day"])

    stem_haps, wealth_hap_flag, guan_hap_flag = _stem_union_notes(day_master, sg, pillars)
    stem_clash_lines = _stem_clash_notes(sg, pillars)
    stem_pressure = _stem_geuk_pressure(day_master, sg)

    sins = native_sinsal if native_sinsal is not None else sn.analyze_sinsal(day_master, pillars, gender=gender)
    sin_rows = sins.get("신살_목록") or []

    def _has_star(name: str) -> bool:
        return any(r.get("신살") == name for r in sin_rows if isinstance(r, dict))

    wjz = sn._wonjin_zhi(zhis["year"], gans["year"], gender)  # type: ignore[attr-defined]
    wonjin_hit = bool(wjz and branch_chong(sz, wjz))

    peach_z = _peach_marker(zhis["year"])
    peach_hit = sz == peach_z

    ctr = sip_ctr if sip_ctr is not None else _sipsin_counter(day_master, pillars)
    pianyin_heavy = ctr["편인"] >= 4

    officer_chong_month = branch_chong(sz, zhis["month"]) or branch_po(sz, zhis["month"]) or branch_hai(sz, zhis["month"])
    rex_chong_any = False
    for pk in PILLAR_KEYS:
        pg = pillars[pk]["gan"]
        hs = gj.jijanggan_ordered(zhis[pk])
        has_rex = sp.classify_sipsin(day_master, pg) in ("편재", "정재") or any(
            sp.classify_sipsin(day_master, h) in ("편재", "정재") for h in hs
        )
        if has_rex and (branch_chong(sz, zhis[pk]) or branch_po(sz, zhis[pk])):
            rex_chong_any = True

    geobjae_year = sip_sg == "겁재"

    yangin_br = sn._yangin_branch(day_master)  # type: ignore[attr-defined]
    baekho_hit = False
    for r in sin_rows:
        if not isinstance(r, dict):
            continue
        if r.get("신살") != "백호살":
            continue
        bh_z = r.get("글자", "")
        if bh_z and (bh_z == sz or branch_chong(sz, bh_z)):
            baekho_hit = True
            break

    yangin_hit = bool(yangin_br and sz == yangin_br and _has_star("양인살"))

    year_zhi_chong = branch_chong(sz, zhis["year"])
    resource_hit = ctr["편인"] + ctr["정인"] >= 4 and (
        stem_chong(sg, gans["year"]) or year_zhi_chong or officer_chong_month
    )

    samxing_alert = any("삼형" in x.get("유형", "") or "형" in x.get("유형", "") for x in br_xing)

    events = {
        "연애_결혼": peach_hit and (sip_sg in ("정관", "편관") or guan_hap_flag),
        "이별_이혼": day_chong or wonjin_hit,
        "취업_승진": sip_sg in ("정관", "편관") and any(branch_liu_he(sz, zhis[pk]) for pk in PILLAR_KEYS),
        "실직_이직": officer_chong_month or (sip_sg in ("편관", "상관") and officer_chong_month),
        "재물획득": wealth_hap_flag,
        "손재_도난": geobjae_year or rex_chong_any,
        "건강이상": pianyin_heavy or (sip_sg in ("편관", "정관") and day_chong),
        "수술_사고": baekho_hit or yangin_hit,
        "부모우환": year_zhi_chong or resource_hit,
        "관재구설": samxing_alert or (_has_star("괴강살") and officer_chong_month),
    }

    event_notes = []
    if events["연애_결혼"]:
        event_notes.append("연애·결혼: 도화·관성·합 신호가 겹치면 인연 전환 가능성.")
    if events["이별_이혼"]:
        event_notes.append("이별·이혼: 일지충 또는 원진 발동 시 관계 재조정 과제.")
    if events["취업_승진"]:
        event_notes.append("취업·승진: 세운 관성이 들어오며 지지 육합이 받쳐줄 때 유리.")
    if events["실직_이직"]:
        event_notes.append("실직·이직: 월지 충파해로 직장축 요동 가능.")
    if events["재물획득"]:
        event_notes.append("재물: 세운 천간합으로 재성 방향 화기가 붙기 쉽습니다.")
    if events["손재_도난"]:
        event_notes.append("손재: 겁재 세운 또는 재 자리 충파.")
    if events["건강이상"]:
        event_notes.append("건강: 인성 과다·관살 긴장 시 피로·만성 질환 여지.")
    if events["수술_사고"]:
        event_notes.append("수술·사고: 백호·양인 세운 발동 시 금속·외상 의식.")
    if events["부모우환"]:
        event_notes.append("부모·윗대: 년지 충 또는 인성 급격 충극.")
    if events["관재구설"]:
        event_notes.append("관재·구설: 형살·괴강과 관성 동요.")

    score = 50.0
    score -= 14 * len([x for x in br_chong if x["궁"] == "day"])
    score -= 10 * len([x for x in br_chong if x["궁"] == "month"])
    score -= 6 * len([x for x in br_chong if x["궁"] in ("year", "hour")])
    score -= 5 * (len(br_po) + len(br_hai))
    score -= 7 * len(br_xing)
    score += 8 * len(br_he)
    score += 6 * len(stem_haps)
    score -= 14 if fan_yin_strict else (8 if fan_yin_heavy else 0)
    score -= 6 if events["손재_도난"] else 0
    score += 5 if events["재물획득"] else 0
    score += 4 if events["취업_승진"] else 0
    luck_word, stars_main = _stars_from_score(score)

    love_score = 50 - (18 if day_chong else 0) - (10 if events["이별_이혼"] else 0) + (12 if events["연애_결혼"] else 0)
    wealth_score = 50 + (14 if events["재물획득"] else 0) - (16 if events["손재_도난"] else 0)
    career_score = 50 + (12 if events["취업_승진"] else 0) - (14 if events["실직_이직"] else 0)

    health_raw = _compute_health_domain_score(day_chong, baekho_hit, yangin_hit, pianyin_heavy, br_chong, br_he)
    if counts:
        strong, weak = oh_weak_strong(counts)
        se_elems = {gj.element_of_stem(sg), gj.element_of_branch(sz)}
        if weak in se_elems:
            health_raw += 6
            wealth_score += 4
            career_score += 3
        if strong in se_elems:
            health_raw -= 8
            wealth_score -= 5

    _, love_stars = _stars_from_score(love_score + 20)
    _, wealth_stars = _stars_from_score(wealth_score + 15)
    _, career_stars = _stars_from_score(career_score + 18)
    _, health_stars = _stars_from_score(health_raw + 18)

    health_parts = []
    for row in br_chong:
        health_parts.append(row["신체"])
    health_parts.extend(ZHI_BODY.get(zhis["day"], "").split("·"))
    health_focus = "·".join(sorted({x.strip() for x in health_parts if x.strip()}))[:80]

    # 육친 궁별 요약
    yuk_summ = {}
    for pk, lab in (
        ("year", "부모·환경(년지)"),
        ("month", "직업·부모(월지)"),
        ("day", "배우자·본인(일지)"),
        ("hour", "자녀·말년(시지)"),
    ):
        bits = []
        if branch_chong(sz, zhis[pk]):
            bits.append("충")
        if branch_po(sz, zhis[pk]):
            bits.append("파")
        if branch_hai(sz, zhis[pk]):
            bits.append("해")
        if branch_liu_he(sz, zhis[pk]):
            bits.append("육합")
        if _xing_pair_label(sz, zhis[pk]):
            bits.append("형")
        if sz == zhis[pk]:
            bits.append("복음")
        yuk_summ[pk] = {
            "제목": lab,
            "작용": ", ".join(bits) if bits else "특이 충합 형 해 없음",
            "신체참고": ZHI_BODY.get(zhis[pk], ""),
        }

    outline_lines: List[str] = []
    outline_lines.append(f"{solar_year}년 {pillar_full}년 ({sw['label_kr']} · {sw['nayin']})")
    outline_lines.append(f"├── 십신: {sip_sg}")
    outline_lines.append(f"├── 종합운세: {luck_word} {_rating_bar(stars_main)} ({stars_main}/5)")
    outline_lines.append(f"├── 💰 재물운: {_rating_bar(wealth_stars)}")
    outline_lines.append(f"├── 💑 애정운: {_rating_bar(love_stars)}")
    outline_lines.append(f"├── 💼 직업운: {_rating_bar(career_stars)}")
    outline_lines.append(
        f"├── 🏥 건강운: {_rating_bar(health_stars)} · {health_focus or '특이 호소 부위 없음'}"
    )
    if br_chong:
        for row in br_chong[:4]:
            outline_lines.append(f"├── ⚠️ {row['위치']}와 세운 충 ({row['글자']}) → {row['육친궁']} · {row['신체']}")
    if fuyin_lines:
        outline_lines.append(f"├── ⚠️ 복음: {fuyin_lines[0]}")
    if fan_yin_strict:
        outline_lines.append("├── ⚠️ 반음: 세운 지지가 원국 네 지지 모두와 충.")
    elif fan_yin_heavy:
        outline_lines.append("├── ⚠️ 반음형: 세운 지지가 원국 여러 궁과 동시 긴장(충·파·해 다발).")

    dm_el = gj.element_of_stem(day_master)
    officer_el = CONTROL_MAP[dm_el]
    wealth_el = _wealth_element(dm_el)

    monthly_risk = _monthly_focus_risks(day_master, pillars, solar_year, sz)
    yuk_blocks = _yukchin_blocks_v2(day_master, pillars, zhis, sg, sz, sip_sg, sip_sz_approx, events)
    story_sum = _story_summary_line(solar_year, pillar_full, sg, sz, zhis, br_chong, fan_yin_heavy, day_chong)
    health_detail = _health_detail_pack(
        day_master=day_master,
        br_chong=br_chong,
        sz=sz,
        sg=sg,
        day_zhi=zhis["day"],
        counts=counts,
        baekho_hit=baekho_hit,
        yangin_hit=yangin_hit,
        day_chong=day_chong,
        pianyin_heavy=pianyin_heavy,
    )
    wealth_detail_txt = _wealth_narrative_v2(
        sip_sg, events, wealth_hap_flag, geobjae_year, rex_chong_any, sz, day_master
    )
    career_detail_txt = _career_narrative_v2(events, sip_sg, samxing_alert, officer_chong_month)
    love_detail_txt = _love_narrative_v2(peach_hit, day_chong, events, gender)
    luck_kw, caution_kw = _luck_and_caution_kw(dm_el, sg, sz, luck_word, fan_yin_heavy)
    closing_advice = _closing_one_liner(luck_word, day_chong, fan_yin_strict, events)
    overall_star = max(
        1, min(5, int(round((health_stars + wealth_stars + career_stars + love_stars) / 4)))
    )
    domain_scores = {
        "건강": {"별점": health_stars, "문자": _rating_bar(health_stars), "산출요약": "일지충·월지충·백호·양인·인성과세 반영"},
        "재물": {"별점": wealth_stars, "문자": _rating_bar(wealth_stars), "산출요약": "재성합·손재·겁재·천을×편재 횡재 후보 반영"},
        "직업": {"별점": career_stars, "문자": _rating_bar(career_stars), "산출요약": "관성·월지 충파해·승진 신호 반영"},
        "애정": {"별점": love_stars, "문자": _rating_bar(love_stars), "산출요약": "일지충·도화·연애 플래그 반영"},
        "전체": {
            "별점": overall_star,
            "문자": _rating_bar(overall_star),
            "산출요약": "건강·재물·직업·애정 네 영역 별점 산술평균(반올림)",
        },
    }

    return {
        "연도": solar_year,
        "간지": pillar_full,
        "천간": sg,
        "지지": sz,
        "낭음": sw["nayin"],
        "표기한글": sw["label_kr"],
        "세운_천간_십신": sip_sg,
        "세운_지지_본기십신_근사": sip_sz_approx,
        "오행_변화_메모": _elem_delta_note(day_master, sg, sz, counts),
        "원국_참고_관성오행": officer_el,
        "원국_참고_재성오행": wealth_el,
        "세운_천간합": stem_haps,
        "세운_천간충": stem_clash_lines,
        "세운_천간_압박": stem_pressure,
        "세운_지지_충": br_chong,
        "세운_지지_파": br_po,
        "세운_지지_해": br_hai,
        "세운_지지_형": br_xing,
        "세운_지지_육합": br_he,
        "삼합_반합_메모": san_he_lines,
        "복음": fuyin_lines,
        "반음_전지충": fan_yin_strict,
        "반음_과격": fan_yin_heavy,
        "세운_대입_원본": inj_rows,
        "육친궁별": yuk_summ,
        "사건예측": events,
        "사건예측_설명": event_notes,
        "운세등급": luck_word,
        "별점": stars_main,
        "별점_문자": _rating_bar(stars_main),
        "재물별점": wealth_stars,
        "애정별점": love_stars,
        "직업별점": career_stars,
        "건강별점": health_stars,
        "세운_총평_한줄": story_sum,
        "육친별_상세": yuk_blocks,
        "월별_집중위험": monthly_risk,
        "건강_상세": health_detail,
        "재물운_상세": {"서술": wealth_detail_txt},
        "직업운_상세": {"서술": career_detail_txt},
        "애정운_상세": {"서술": love_detail_txt},
        "종합점수_영역별": domain_scores,
        "행운_키워드": luck_kw,
        "주의_키워드": caution_kw,
        "이해_총평_한마디": closing_advice,
        "출력_트리텍스트": "\n".join(outline_lines),
    }


def sewoon_forecast_pack(
    day_master: str,
    pillars: dict,
    gender: str,
    *,
    center_year: Optional[int] = None,
    span: int = 10,
    counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    기준 연도 ±span 세운 심층표 (기본 21년).

    반환 키:
    - ``기준연도``, ``범위``, ``연도별``: 각 해 ``analyze_sewoon_year`` 결과 리스트
    """
    import datetime

    cy = center_year if center_year is not None else datetime.datetime.now().year
    native_sinsal = sn.analyze_sinsal(day_master, pillars, gender=gender)
    sip_ctr = _sipsin_counter(day_master, pillars)

    years = []
    for y in range(cy - span, cy + span + 1):
        years.append(
            analyze_sewoon_year(
                day_master,
                pillars,
                gender,
                y,
                counts=counts,
                native_sinsal=native_sinsal,
                sip_ctr=sip_ctr,
            )
        )

    return {
        "기준연도": cy,
        "범위": {"전": span, "후": span, "총년수": 2 * span + 1},
        "연도별": years,
        "통합_트리텍스트": "\n\n".join(row["출력_트리텍스트"] for row in years),
    }
