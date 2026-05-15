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

# 세운·복음·충·해 — 사용자가 바로 이해할 수 있는 쉬운 해석 문장
_PILLAR_PLAIN = {
    "year": "가문·유년기·대외 이미지",
    "month": "부모·직장·사회생활·수입 기반",
    "day": "본인·배우자·건강·가정 안정",
    "hour": "자녀·말년·후배·실행·결과",
}


def _fuyin_sewoon_note(pillar_key: str, ju_label: str, year: Optional[int]) -> str:
    yr = f"{year}년 " if year else "올해 "
    theme = _PILLAR_PLAIN.get(pillar_key, ju_label)
    return (
        f"{yr}운의 기운이 태어날 때의 「{ju_label}」와 글자가 똑같습니다(복음). "
        f"예전에 겪었던 {theme} 쪽 일이 비슷한 모양으로 다시 나오기 쉬운 해입니다. "
        f"완전히 새로운 변화라기보다, ‘전에도 한 번 겪은 숙제’를 다시 풀게 되는 느낌으로 보시면 됩니다."
    )


def _fuyin_zhi_repeat_note(pillar_key: str, zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, ZHI_LABEL.get(pillar_key, ""))
    body = ZHI_BODY.get(zhi, "해당 부위")
    return (
        f"올해 지지 「{zhi}」가 원국 {ZHI_LABEL.get(pillar_key, '')}와 같습니다. "
        f"{theme}·{body} 관련 이슈가 작년과 비슷하게 반복될 수 있으니, 같은 실수·갈등을 두 번 하지 않도록 정리하는 것이 좋습니다."
    )


def _fuyin_daewoon_note(pillar_key: str, ju_label: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, ju_label)
    return (
        f"지금 대운 간지가 원국 「{ju_label}」와 같습니다. "
        f"10년 동안 {theme} 주제가 크게 반복·확대되는 시기로, 익숙한 패턴을 알아차리면 손해를 줄일 수 있습니다."
    )


def _sewoon_chong_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    body = ZHI_BODY.get(nat_zhi, "몸의 해당 부위")
    return (
        f"올해 기운(지지 {sew_zhi})이 원국 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})와 정면으로 부딪칩니다(충). "
        f"{theme} 자리에서 이사·이직·관계 갈등·급한 결정·환경 변화가 생기기 쉽습니다. "
        f"몸으로는 {body} 쪽(통증·피로·검진) 신호가 나올 수 있으니 평소보다 챙기세요."
    )


def _sewoon_po_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    body = ZHI_BODY.get(nat_zhi, "몸")
    return (
        f"올해 {sew_zhi}가 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})를 ‘깨뜨리는’ 기운(파)입니다. "
        f"{theme}에서 약속·계약·신뢰·수입 구조가 흔들리거나 갑자기 바뀔 수 있습니다. "
        f"{body} 피로·스트레스도 함께 올라갈 수 있습니다."
    )


def _sewoon_hai_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    body = ZHI_BODY.get(nat_zhi, "몸")
    return (
        f"올해 {sew_zhi}가 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})를 서서히 찌르는 기운(해)입니다. "
        f"{theme}에서 말다툼·서운함·질투·뒤에서 오는 방해가 은근히 쌓일 수 있습니다. "
        f"몸은 {body} 쪽 만성 피로·소화 불편을 먼저 신호로 느끼는 경우가 많습니다."
    )


def _sewoon_liuhe_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    return (
        f"올해 지지 {sew_zhi}와 원국 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})가 서로 잘 맞는 조합(육합)입니다. "
        f"{theme}에서 도움·협력·인연·만남이 늘고 일이 순조롭게 이어지기 쉽습니다. "
        f"너무 편해서 방심하지 않도록, 약속·돈·관계는 그래도 한 번씩 확인하는 것이 좋습니다."
    )


def _sewoon_cheongan_hap_note(
    pillar_key: str,
    sew_gan: str,
    nat_gan: str,
    elem: str,
    sipsin_label: str,
) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    sip_hint = {
        "비견": "형제·동료·경쟁",
        "겁재": "지출·동업·경쟁",
        "식신": "표현·기술·자녀",
        "상관": "말·창작·변화",
        "편재": "부수입·사업",
        "정재": "월급·안정 수입",
        "편관": "압박·이동·규칙",
        "정관": "직장·책임·명예",
        "편인": "학습·이단적 생각",
        "정인": "어머니·보호·자격",
    }.get(sipsin_label, sipsin_label or "해당 주제")
    return (
        f"올해 천간 {sew_gan}이 원국 {GAN_LABEL.get(pillar_key, '')} {nat_gan}과 합쳐집니다(천간합). "
        f"{theme}에서 「{sip_hint}」 쪽 일이 한데 묶여 진행되기 쉽고, 합화 기운은 {elem} 방향으로 흐릅니다. "
        f"혼자 밀기보다 같이 하는 일·계약·관계에서 성과가 나오기 쉬운 신호입니다."
    )


def _native_chong_note(k1: str, k2: str) -> str:
    t1, t2 = _PILLAR_PLAIN.get(k1, ""), _PILLAR_PLAIN.get(k2, "")
    if "day" in (k1, k2):
        return (
            f"원국 안에서 두 지지가 서로 정면으로 부딪칩니다(충). "
            f"배우자·가정·건강({t1}·{t2}) 쪽에서 갈등·이사·환경 변화가 반복되기 쉽습니다."
        )
    if "month" in (k1, k2):
        return (
            f"원국 안에서 두 지지가 충입니다. "
            f"직장·부모·사회생활({t1}·{t2}) 자리에서 마찰·이직·급한 변화가 생기기 쉽습니다."
        )
    return (
        f"원국 안에서 두 지지가 충입니다. "
        f"{t1}·{t2} 관련 환경·인연에서 예기치 않은 변동을 조심하세요."
    )


def _native_hai_note(k1: str, k2: str) -> str:
    if "day" in (k1, k2):
        return (
            "원국 안에서 두 지지가 해(害)입니다. "
            "배우자·가정·일상에서 서운함·오해·말다툼이 쌓이기 쉬우니, 오해는 바로 풀어두는 것이 좋습니다."
        )
    if "month" in (k1, k2):
        return (
            "원국 안에서 두 지지가 해입니다. "
            "직장·상사·부모 문제가 겉으로 드러나지 않고 은근히 신경 쓰이는 형태가 많습니다."
        )
    return (
        "원국 안에서 두 지지가 해입니다. "
        "대외·자녀·말년 쪽에서 작은 방해·질투·근심이 쌓일 수 있습니다."
    )


def _native_po_note(k1: str, k2: str) -> str:
    if "day" in (k1, k2):
        return (
            "원국 안에서 두 지지가 파(破)입니다. "
            "결혼·계약·신뢰·가정 안정이 한 번 깨졌다가 다시 잡히는 패턴이 나오기 쉽습니다."
        )
    if "month" in (k1, k2):
        return (
            "원국 안에서 두 지지가 파입니다. "
            "직장·수입·사업 구조가 갑자기 바뀌거나 약속이 깨지는 일을 조심하세요."
        )
    return (
        "원국 안에서 두 지지가 파입니다. "
        "계획·환경·말년 준비가 중간에 틀어지지 않도록 백업을 두는 것이 좋습니다."
    )


def _native_liuhe_note(k1: str, k2: str, za: str, zb: str) -> str:
    t1, t2 = _PILLAR_PLAIN.get(k1, ""), _PILLAR_PLAIN.get(k2, "")
    return (
        f"원국 안에서 {za}와 {zb}가 육합(六合)으로 맞습니다. "
        f"{t1}·{t2} 쪽 인연이 자연스럽게 이어지고, 서로 도움이 되는 관계가 만들어지기 쉽습니다."
    )


def _native_cheongan_hap_note(k1: str, k2: str, elem: str) -> str:
    t1, t2 = _PILLAR_PLAIN.get(k1, ""), _PILLAR_PLAIN.get(k2, "")
    return (
        f"원국 천간이 천간합으로 묶입니다. "
        f"{t1}·{t2} 주제가 {elem} 기운 쪽으로 한데 흘러, 협력·인연·제도 안에서 끌려 들어가기 쉽습니다."
    )


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
    return _native_chong_note(k1, k2)


def _hai_position_note(k1: str, k2: str) -> str:
    return _native_hai_note(k1, k2)


def _po_position_note(k1: str, k2: str) -> str:
    return _native_po_note(k1, k2)


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
                _native_cheongan_hap_note(k1, k2, elem),
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
                _native_liuhe_note(k1, k2, za, zb),
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
                        _fuyin_sewoon_note(k, lbl, sewoon_year),
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
                        _fuyin_zhi_repeat_note(k, sz),
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
                            _fuyin_daewoon_note(k, JU_LABEL[k]),
                        )
                    )
    return out


def analyze_sewoon_injection(
    pillars: dict,
    sewoon_pillar: str,
    *,
    sewoon_year: Optional[int] = None,
    day_master: Optional[str] = None,
) -> List[Dict[str, str]]:
    """세운 간지·천간과 원국의 충·파·해·육합·천간합."""
    if len(sewoon_pillar) < 2:
        return []
    sg, sz = sewoon_pillar[0], sewoon_pillar[1]
    dm = day_master or pillars.get("day", {}).get("gan", "")
    yr_note = f"{sewoon_year}년 세운 " if sewoon_year else "세운 "
    out: List[Dict[str, str]] = []

    ch_set = _chong_set()
    po_set = _po_set()
    hai_set = _hai_set()
    he_set = _liu_he_set()

    for k in PILLAR_KEYS:
        nz = pillars[k]["zhi"]
        pair = tuple(sorted((sz, nz)))
        pos_lbl = ZHI_LABEL[k]

        if pair in ch_set:
            out.append(
                _relation_row(
                    "세운충",
                    f"{sz}×{nz}",
                    f"{yr_note}지지 {sz}가 {pos_lbl}({nz})와 충",
                    "중",
                    _sewoon_chong_note(k, sz, nz),
                )
            )
        if pair in po_set:
            out.append(
                _relation_row(
                    "세운파",
                    f"{sz}×{nz}",
                    f"{yr_note}{sz}가 {pos_lbl} 파",
                    "중",
                    _sewoon_po_note(k, sz, nz),
                )
            )
        if pair in hai_set:
            out.append(
                _relation_row(
                    "세운해",
                    f"{sz}×{nz}",
                    f"{yr_note}{sz}가 {pos_lbl} 해",
                    "중",
                    _sewoon_hai_note(k, sz, nz),
                )
            )
        if pair in he_set:
            out.append(
                _relation_row(
                    "세운육합",
                    f"{sz}{nz}",
                    f"{yr_note}지지 {sz}와 {pos_lbl}({nz}) 육합",
                    "중",
                    _sewoon_liuhe_note(k, sz, nz),
                )
            )

    if dm and sg:
        try:
            from . import sipsin as sp

            for k in PILLAR_KEYS:
                pg = pillars[k]["gan"]
                if pg == dm:
                    continue
                fs = frozenset((sg, pg))
                if fs not in CHEON_GAN_HAP_RESULT:
                    continue
                elem = CHEON_GAN_HAP_RESULT[fs]
                sip = sp.classify_sipsin(dm, pg)
                out.append(
                    _relation_row(
                        "세운천간합",
                        f"{sg}{pg}",
                        f"{yr_note}천간 {sg}와 {GAN_LABEL[k]} {pg} 합",
                        "중",
                        _sewoon_cheongan_hap_note(k, sg, pg, elem, sip),
                    )
                )
        except ImportError:
            pass

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
        else analyze_sewoon_injection(
            pillars,
            sewoon_pillar,
            sewoon_year=sewoon_year,
            day_master=pillars.get("day", {}).get("gan"),
        ),
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
