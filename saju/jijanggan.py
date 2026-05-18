# -*- coding: utf-8 -*-
"""지장간(地支蔵干) 추출 · 맞춤 해설."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import ganji as gj

SLOT_STRENGTH = {
    "정기": "항상·가장 강하게",
    "중기": "상황에 따라",
    "여기": "특정 시기에만",
}

PILLAR_CONTEXT = {
    "year": "초년·부모 관계에서",
    "month": "직업·사회생활에서",
    "day": "본인 내면·배우자 관계에서",
    "hour": "자녀·말년에서",
}

SIBU_SHORT = {
    "장생": "생명력이 넘치고 새로운 시작에 강합니다",
    "목욕": "감수성과 매력이 있지만 감정 기복이 있습니다",
    "관대": "패기와 자존심이 강한 에너지입니다",
    "건록": "독립심이 강하고 자수성가 기질이 있습니다",
    "제왕": "강한 추진력과 주도권을 가진 에너지입니다",
    "쇠": "안정을 추구하고 보수적입니다",
    "병": "섬세하고 예술적 감수성이 발달합니다",
    "사": "철학적이고 정신세계가 깊습니다",
    "묘": "저축형이고 집착이 강합니다",
    "절": "단절과 새 출발의 에너지입니다",
    "태": "새로운 계획이 잉태되는 에너지입니다",
    "양": "성장하고 보호받는 에너지입니다",
}

PILLAR_ROLE = {
    "year": "년주 {full}는 당신의 초년과 부모·가문을 나타냅니다.",
    "month": "월주 {full}는 당신의 직업과 사회생활을 나타냅니다.",
    "day": "일주 {full}는 당신 자신과 {spouse}을 나타냅니다.",
    "hour": "시주 {full}는 말년과 자녀·결실을 나타냅니다.",
}


def hidden_stems(zhi: str) -> List[str]:
    return gj.jijanggan_ordered(zhi)


def interpret_slot_for_user(
    pillar_key: str,
    slot: str,
    gan: str,
    sipsin: str,
    female: bool,
) -> str:
    """정기/중기/여기 설명을 사용자 맞춤 문장으로 생성."""
    ctx = PILLAR_CONTEXT.get(pillar_key, "이 궁에서")
    strength = SLOT_STRENGTH.get(slot, "때때로")

    sipsin_user = {
        "정인": (
            f"모친·학문의 기운 — {ctx} {strength} 작용해 "
            f"배움과 보살핌에 대한 욕구가 나타납니다"
        ),
        "편인": (
            f"특수재능·보호의 기운 — {strength} 드러나 "
            f"독특한 재능이나 예상치 못한 도움이 옵니다"
        ),
        "정관": (
            f"{'남편·규범' if female else '명예·직위'}의 기운 — {ctx}에서 {strength} "
            f"{'배우자 인연' if female else '사회적 책임'}이 읽힙니다"
        ),
        "편관": (
            f"{'애인·직장압박' if female else '권위·도전'}의 기운 — {strength} 나타나 "
            f"강한 자극과 변화가 찾아옵니다"
        ),
        "정재": (
            f"{'시어머니·재산' if female else '아내·고정수입'}의 기운 — "
            f"{ctx}에서 {strength} 작용합니다"
        ),
        "편재": (
            f"부친·유동재산의 기운 — {strength} 작용해 "
            f"재물 기회가 들어오는 신호입니다"
        ),
        "식신": (
            f"자녀·표현·복록의 기운 — {ctx}에서 {strength} 나타나 "
            f"창의성과 여유가 발휘됩니다"
        ),
        "상관": (
            f"재능·자유의 기운 — {strength} 작용해 "
            f"뛰어난 표현력과 함께 규칙과의 마찰도 생깁니다"
        ),
        "비견": (
            f"형제·동료의 기운 — {strength} 나타나 "
            f"협력과 경쟁이 교차합니다"
        ),
        "겁재": (
            f"경쟁·지출의 기운 — {strength} 작용해 "
            f"재물 손실이나 강한 경쟁이 생기기 쉽습니다"
        ),
        "일간": (
            "본인 에너지의 뿌리 — 일지 안에 일간과 같은 기운이 있어 "
            "자신의 본성이 내면 깊이 자리잡고 있습니다"
        ),
    }

    return sipsin_user.get(
        sipsin,
        f"{sipsin} 기운이 {ctx}에서 {strength} 작용합니다",
    )


def pillar_bottom_story(
    pillar_key: str,
    gan: str,
    zhi: str,
    sipsin: str,
    sibu: str,
    chungs: list,
    female: bool,
) -> str:
    """각 주(柱) 하단 맞춤 설명."""
    full = gan + zhi
    spouse = "배우자" if female else "본인 내면"
    role_tpl = PILLAR_ROLE.get(pillar_key, "이 주는 {full}입니다.")
    base = role_tpl.format(full=full, spouse=spouse)

    chung_str = ""
    for c in chungs or []:
        glyphs = str((c.get("글자") if isinstance(c, dict) else c) or "")
        if zhi in glyphs:
            chung_str = (
                f" {zhi}가 충을 받아 "
                f"이 자리에서 변화와 긴장이 반복됩니다."
            )
            break

    sibu_str = ""
    if sibu:
        hint = SIBU_SHORT.get(sibu, "")
        if hint:
            sibu_str = f" {sibu}의 기운으로 {hint}."

    _ = sipsin  # 십신은 향후 확장용
    return base + chung_str + sibu_str


def pillar_hidden_detail(zhi: str) -> List[dict]:
    """정기→중기→여기 순으로 지장간과 슬롯명을 함께 반환."""
    triple = gj.JIJANGGAN_DETAIL.get(zhi, {})
    result: List[dict] = []
    for slot in ("정기", "중기", "여기"):
        gan = triple.get(slot)
        if not gan:
            continue
        result.append(
            {
                "slot": slot,
                "gan": gan,
                "element": gj.element_of_stem(gan),
                "kr": gj.STEM_KR[gj.stem_index(gan)],
            }
        )
    return result


def enrich_hidden_for_user(
    hidden_block: dict,
    hidden_sipsin: dict,
    *,
    female: bool,
) -> dict:
    """지장간 슬롯마다 user_desc 필드 추가."""
    out: Dict[str, Any] = {}
    for key in ("year", "month", "day", "hour"):
        block = dict(hidden_block.get(key) or {})
        sp_rows = hidden_sipsin.get(key) or []
        enriched_hidden: List[Dict[str, Any]] = []
        for idx, h in enumerate(block.get("hidden") or []):
            row = dict(h)
            sp = sp_rows[idx] if idx < len(sp_rows) else {}
            if not sp and sp_rows:
                sp = next((x for x in sp_rows if x.get("gan") == h.get("gan")), {})
            row["user_desc"] = interpret_slot_for_user(
                key,
                str(row.get("slot") or ""),
                str(row.get("gan") or ""),
                str(sp.get("sipsin") or ""),
                female,
            )
            enriched_hidden.append(row)
        block["hidden"] = enriched_hidden
        out[key] = block
    return out


def all_hidden_for_pillars(pillars: dict) -> dict:
    """pillars: year/month/day/time 각각 gan, zhi 키 포함."""
    out = {}
    for key in ("year", "month", "day", "hour"):
        p = pillars[key]
        zhi = p["zhi"]
        out[key] = {
            "zhi": zhi,
            "zhi_kr": gj.BRANCH_KR[gj.branch_index(zhi)],
            "hidden": pillar_hidden_detail(zhi),
        }
    return out


def build_pillar_bottom_stories(
    pillars: dict,
    *,
    sipsin_stems: dict,
    sibiunsung: dict,
    native_chungs: list,
    female: bool,
) -> Dict[str, str]:
    """년·월·일·시주 하단 맞춤 문장."""
    stories: Dict[str, str] = {}
    for key in ("year", "month", "day", "hour"):
        p = pillars[key]
        sip = (sipsin_stems or {}).get(key) or {}
        sb = (sibiunsung or {}).get(key) or {}
        stories[key] = pillar_bottom_story(
            key,
            p["gan"],
            p["zhi"],
            str(sip.get("sipsin") or ""),
            str(sb.get("stage") or ""),
            native_chungs,
            female,
        )
    return stories
