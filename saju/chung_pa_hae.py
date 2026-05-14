# -*- coding: utf-8 -*-
"""
원국·세운·대운 기준 충·파·해·형·합·복음(伏吟) 분석.

출력 항목 공통 형식:
``{ "관계", "글자", "위치", "강도", "해석" }``
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import ganji as gj

PILLAR_KEYS: Tuple[str, ...] = ("year", "month", "day", "hour")
ZHI_LABEL = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
JU_LABEL = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
GAN_LABEL = {"year": "년간", "month": "월간", "day": "일간", "hour": "시간"}

ZHI_BODY = {
    "子": "하체·신장·귀",
    "丑": "복부·비장",
    "寅": "목·어깨·간담",
    "卯": "목·손발·간",
    "辰": "비장·피부",
    "巳": "화·면부·심장",
    "午": "화·안구·순환",
    "未": "비위·소화",
    "申": "금·대장·호흡",
    "酉": "금·폐·치아",
    "戌": "화개·관절",
    "亥": "수·머리·비복",
}

ZHI_YUKCHIN_SHORT = {
    "year": "조상·환경·대외",
    "month": "부모·직업·사회",
    "day": "배우자·본인·내실",
    "hour": "자녀·말년·아랫사람",
}

CHEON_GAN_HAP_RESULT = {
    frozenset(("甲", "己")): "토",
    frozenset(("乙", "庚")): "금",
    frozenset(("丙", "辛")): "수",
    frozenset(("丁", "壬")): "목",
    frozenset(("戊", "癸")): "화",
}

SAN_HE_ELEMENT = {"목국": "목", "화국": "화", "토국": "토", "금국": "금", "수국": "수"}


def _relation_row(kind: str, glyphs: str, where: str, strength: str, note: str) -> Dict[str, str]:
    return {"관계": kind, "글자": glyphs, "위치": where, "강도": strength, "해석": note}


def _pairs_positions(keys: Sequence[str]) -> List[Tuple[str, str]]:
    return [(keys[i], keys[j]) for i in range(len(keys)) for j in range(i + 1, len(keys))]


def _chong_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.CHONG_PAIRS}


def _hai_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.LIU_HAI}


def _po_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.LIU_PO}


def _liu_he_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.LIU_HE}


def _strength(keys_involved: Iterable[str]) -> str:
    ks = set(keys_involved)
    if "day" in ks:
        return "높음"
    if "month" in ks:
        return "중"
    return "참고"


def _chong_position_note(k1: str, k2: str) -> str:
    roles = (ZHI_YUKCHIN_SHORT[k1], ZHI_YUKCHIN_SHORT[k2])
    base = "지충으로 긴장·이동·관계 균열 신호가 생깁니다."
    if k1 == "day" or k2 == "day":
        return f"일지 충 포함 → 배우자·내실 쪽 {base}"
    if k1 == "month" or k2 == "month":
        return f"월지 충 포함 → 직업·부모·사회 자리 {base}"
    return f"년·시 충 → 조상·환경 또는 자녀·말년 축에서 {base}"


def _hai_position_note(k1: str, k2: str) -> str:
    if k1 == "day" or k2 == "day":
        return "육해가 일지를 건드려 배우자·내실에 배신감·오해 누적형 스트레스가 나타나기 쉽습니다."
    if k1 == "month" or k2 == "month":
        return "월지 육해로 직장·상사·부모 문제가 은근히 끼치는 형태입니다."
    return "년·시 육해로 대외·자녀 축에 근심·방해 요인이 생기기 쉽습니다."


def _po_position_note(k1: str, k2: str) -> str:
    if k1 == "day" or k2 == "day":
        return "일지 파로 계약·결혼·신뢰 관계가 깨지기 쉬운 패턴입니다."
    if k1 == "month" or k2 == "month":
        return "월지 파로 일터·수입 구조가 급히 무너지거나 바뀌는 일이 잦을 수 있습니다."
    return "파가 년·시에 걸려 환경·말년 계획이 예기치 않게 삭는 경우를 경계합니다."


def _xing_note(kind_zh: str, k1: str, k2: str) -> str:
    ks = {k1, k2}
    day_hit = "day" in ks
    base_map = {
        "인사신 삼형": "관재·구설·시비에 노출되기 쉬운 무은지형입니다.",
        "축술미 삼형": "고집·형벌·부상·수술 운이 겹치기 쉬운 고지형입니다.",
        "자묘 상형": "예의·관계 예민도가 높아 구설로 번지기 쉬운 무례지형입니다.",
        "자형": "동일 지지 반복으로 같은 부위 긴장·사고·수술 이슈가 반복될 수 있습니다.",
    }
    core = base_map.get(kind_zh, "형살로 긴장·외상·수술·관재 소지를 함께 봅니다.")
    if day_hit:
        return f"{core} 일지 관여 시 본인·배우자 건강·관계 직결 신호가 강합니다."
    if "month" in ks:
        return f"{core} 월지 관여 시 직업·관직 쪽 형평·규정 리스크를 의식합니다."
    return core


def _san_xing_type(a: str, b: str) -> Optional[str]:
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


def analyze_native_chong(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    ch_set = _chong_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in ch_set:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]} ({glyphs})"
        strength = _strength((k1, k2))
        note = _chong_position_note(k1, k2)
        out.append(_relation_row("충", glyphs, where, strength, note))
    return out


def analyze_native_po(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    po_set = _po_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in po_set:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]}"
        strength = _strength((k1, k2))
        out.append(_relation_row("파", glyphs, where, strength, _po_position_note(k1, k2)))
    return out


def analyze_native_hai(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    hai_set = _hai_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in hai_set:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]}"
        strength = _strength((k1, k2))
        out.append(_relation_row("해", glyphs, where, strength, _hai_position_note(k1, k2)))
    return out


def analyze_native_xing(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        xt = _san_xing_type(za, zb)
        if not xt:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]}"
        strength = _strength((k1, k2))
        note = _xing_note(xt, k1, k2)
        label = "형"
        if xt == "자형":
            label = "자형"
        out.append(_relation_row(label, glyphs, where, strength, note))
    # 세 지지 삼형 완성 여부 (원국 네 지지 안에서 세 개 동시 존재)
    zset = set(zhis.values())
    if gj.XING_SAN_INSAM <= zset:
        out.append(
            _relation_row(
                "삼형완성",
                "寅巳申",
                "원국 지지에 삼형 삼각 완성",
                "높음",
                "무은지형이 동시에 깔려 관재·구설·급박한 사건 소지가 한층 커집니다.",
            )
        )
    if gj.XING_SAN_GOJI <= zset:
        out.append(
            _relation_row(
                "삼형완성",
                "丑戌未",
                "원국 지지에 고지형 삼각 완성",
                "높음",
                "형벌·부상·수술·토목 재해 등 신체·현실 충격을 함께 봅니다.",
            )
        )
    return out


def analyze_native_he(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    gans = {k: pillars[k]["gan"] for k in PILLAR_KEYS}

    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        g1, g2 = gans[k1], gans[k2]
        fs = frozenset((g1, g2))
        if fs not in CHEON_GAN_HAP_RESULT:
            continue
        elem = CHEON_GAN_HAP_RESULT[fs]
        glyphs = f"{g1}{g2}"
        where = f"{GAN_LABEL[k1]}–{GAN_LABEL[k2]} 천간합"
        strength = _strength((k1, k2))
        out.append(
            _relation_row(
                "천간합",
                glyphs,
                where,
                strength,
                f"합화 성향이 {elem} 기운으로 모입니다 — 인연·협력·제도 안으로 끌려드는 힘.",
            )
        )

    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    lh = _liu_he_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in lh:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]} 육합"
        strength = _strength((k1, k2))
        e1, e2 = gj.element_of_branch(za), gj.element_of_branch(zb)
        out.append(
            _relation_row(
                "육합",
                glyphs,
                where,
                strength,
                f"육합으로 인연·유대가 생기며 지지 오행({e1}/{e2})이 서로 끌어당깁니다.",
            )
        )

    zset = set(zhis.values())
    for tri, nation in gj.SAN_HE_GROUPS:
        elem = SAN_HE_ELEMENT[nation]
        inside = zset & tri
        if len(inside) == 3:
            glyphs = "".join(sorted(inside, key=lambda z: gj.branch_index(z)))
            out.append(
                _relation_row(
                    "삼합(완성)",
                    glyphs,
                    f"원국 {nation} 삼합 성립",
                    "높음",
                    f"삼합이 성사되어 {elem} 방향 기운이 크게 뭉칩니다 — 해당 업·인연·재물축을 집중적으로 봅니다.",
                )
            )
        elif len(inside) == 2:
            ordered = "".join(sorted(inside, key=lambda z: gj.branch_index(z)))
            out.append(
                _relation_row(
                    "삼합(두지)",
                    ordered,
                    f"{nation} 삼합 중 둘만 존재",
                    "중",
                    f"{elem} 성향의 삼합 인연은 있으나 마지막 한 지가 없어 완전 결실까지는 변수가 있습니다.",
                )
            )

    return out


def _pillar_string(p: dict) -> str:
    return p.get("pillar") or (p["gan"] + p["zhi"])


def analyze_fuyin(
    pillars: dict,
    *,
    sewoon_pillar: Optional[str] = None,
    sewoon_year: Optional[int] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[Dict[str, str]]:
    """세운·대운 간지가 원국 주와 동일할 때 복음 신호."""
    out: List[Dict[str, str]] = []
    nat = {k: _pillar_string(pillars[k]) for k in PILLAR_KEYS}

    if sewoon_pillar:
        for k in PILLAR_KEYS:
            if sewoon_pillar == nat[k]:
                lbl = JU_LABEL[k]
                yr = f"{sewoon_year}년 " if sewoon_year else ""
                out.append(
                    _relation_row(
                        "복음(세운)",
                        sewoon_pillar,
                        f"{yr}세운이 {lbl}와 동일",
                        "중",
                        f"세운이 {lbl}를 그대로 되풀이해 같은 과제·감정이 표면화되기 쉽습니다.",
                    )
                )
            sz = sewoon_pillar[1] if len(sewoon_pillar) >= 2 else ""
            if sz and sz == pillars[k]["zhi"] and sewoon_pillar != nat[k]:
                out.append(
                    _relation_row(
                        "복음(지중복)",
                        sz,
                        f"세운 지지={sz}가 {ZHI_LABEL[k]}와 동일",
                        "참고",
                        "지지만 겹치는 반복 자극으로 같은 부위·관계 테마가 되살아납니다.",
                    )
                )

    if daewoon_cycles:
        for c in daewoon_cycles:
            gz = c.get("ganzhi") if isinstance(c, dict) else None
            if not gz:
                continue
            for k in PILLAR_KEYS:
                if gz == nat[k]:
                    age = f"{c.get('start_age')}~{c.get('end_age')}세" if isinstance(c, dict) else ""
                    out.append(
                        _relation_row(
                            "복음(대운)",
                            gz,
                            f"대운 {age}·{JU_LABEL[k]}",
                            "중",
                            "대운 간지가 원국 해당 주와 같아 10년간 같은 과제가 확대 재생됩니다.",
                        )
                    )
    return out


def analyze_sewoon_injection(
    pillars: dict,
    sewoon_pillar: str,
    *,
    sewoon_year: Optional[int] = None,
) -> List[Dict[str, str]]:
    """세운 간지와 원국 지지 충·파·해."""
    if len(sewoon_pillar) < 2:
        return []
    sz = sewoon_pillar[1]
    yr_note = f"{sewoon_year}년 세운 " if sewoon_year else "세운 "
    out: List[Dict[str, str]] = []

    ch_set = _chong_set()
    po_set = _po_set()
    hai_set = _hai_set()

    for k in PILLAR_KEYS:
        nz = pillars[k]["zhi"]
        pair = tuple(sorted((sz, nz)))
        pos_lbl = ZHI_LABEL[k]
        yuk = ZHI_YUKCHIN_SHORT[k]
        body = ZHI_BODY.get(nz, "")

        if pair in ch_set:
            out.append(
                _relation_row(
                    "세운충",
                    f"{sz}×{nz}",
                    f"{yr_note}지지 {sz}가 {pos_lbl}({nz})와 충",
                    "중",
                    f"{yuk} 축이 요동하며 신체는 {body} 쪽을 의식합니다.",
                )
            )
        if pair in po_set:
            out.append(
                _relation_row(
                    "세운파",
                    f"{sz}×{nz}",
                    f"{yr_note}{sz}가 {pos_lbl} 파",
                    "중",
                    f"{yuk} 계약·관계가 깨지기 쉽고 {body} 피로가 동반될 수 있습니다.",
                )
            )
        if pair in hai_set:
            out.append(
                _relation_row(
                    "세운해",
                    f"{sz}×{nz}",
                    f"{yr_note}{sz}가 {pos_lbl} 해",
                    "중",
                    f"{yuk} 은근한 방해·시기가 생기고 {body} 만성 통증을 유발하기도 합니다.",
                )
            )

    return out


def analyze_relations_full(
    pillars: dict,
    *,
    sewoon_pillar: Optional[str] = None,
    sewoon_year: Optional[int] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """원국 + 옵션 세운·대운 통합."""
    sections = {
        "원국_충": analyze_native_chong(pillars),
        "원국_파": analyze_native_po(pillars),
        "원국_해": analyze_native_hai(pillars),
        "원국_형": analyze_native_xing(pillars),
        "원국_합": analyze_native_he(pillars),
        "복음": analyze_fuyin(
            pillars,
            sewoon_pillar=sewoon_pillar,
            sewoon_year=sewoon_year,
            daewoon_cycles=daewoon_cycles,
        ),
        "세운_대입": []
        if not sewoon_pillar
        else analyze_sewoon_injection(pillars, sewoon_pillar, sewoon_year=sewoon_year),
    }

    flat: List[Dict[str, str]] = []
    for key in (
        "원국_충",
        "원국_파",
        "원국_해",
        "원국_형",
        "원국_합",
        "복음",
        "세운_대입",
    ):
        for row in sections[key]:
            row2 = dict(row)
            row2["분류"] = key
            flat.append(row2)

    sections["관계_상세_전체"] = flat
    return sections


def analyze_branch_relations(
    pillars: dict,
    *,
    sewoon_pillar: Optional[str] = None,
    sewoon_year: Optional[int] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    - ``관계_상세_전체``: 표준 행 목록
    - ``충``·``파``·``해``·``형``·``합``·``복음``·``세운_대입``: 한 줄 문자열 (기존 UI)
    """
    full = analyze_relations_full(
        pillars,
        sewoon_pillar=sewoon_pillar,
        sewoon_year=sewoon_year,
        daewoon_cycles=daewoon_cycles,
    )

    def _one_line(r: Dict[str, str]) -> str:
        return f"[{r['관계']}] {r['글자']} @ {r['위치']} ({r['강도']}) — {r['해석']}"

    return {
        "관계_상세_전체": full["관계_상세_전체"],
        "충": [_one_line(r) for r in full["원국_충"]],
        "파": [_one_line(r) for r in full["원국_파"]],
        "해": [_one_line(r) for r in full["원국_해"]],
        "형": [_one_line(r) for r in full["원국_형"]],
        "합": [_one_line(r) for r in full["원국_합"]],
        "복음": [_one_line(r) for r in full["복음"]],
        "세운_대입": [_one_line(r) for r in full["세운_대입"]],
    }
