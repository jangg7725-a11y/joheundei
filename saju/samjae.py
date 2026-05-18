# -*- coding: utf-8 -*-
"""삼재(三災) — 년지(띠) 기준 들·눌·날 삼재 판정."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from . import ganji as gj
from . import narrative_loader as nl
from . import sewoon as sw

# 본인 년지 삼합 → (들삼재 지지, 눌삼재 지지, 날삼재 지지)
# 해묘미(亥卯未) → 사오미(巳午未), 인오술(寅午戌) → 신유술(申酉戌) 등 민간 전통 표
_SAMJAE_BY_BIRTH_GROUP: Dict[frozenset, Tuple[str, str, str]] = {
    frozenset({"申", "子", "辰"}): ("亥", "子", "丑"),
    frozenset({"寅", "午", "戌"}): ("申", "酉", "戌"),
    frozenset({"巳", "酉", "丑"}): ("寅", "卯", "辰"),
    frozenset({"亥", "卯", "未"}): ("巳", "午", "未"),
}

_PHASE_LABEL = {
    "deul": "들삼재",
    "nul": "눌삼재",
    "nal": "날삼재",
    "none": "삼재 아님",
}

_PHASE_DESC = {
    "deul": "삼재가 시작되는 해입니다. 변화·도전이 올 수 있어 신중한 준비가 도움이 됩니다.",
    "nul": "삼재 기운이 가장 강한 해입니다. 건강·무리한 확장을 조심하고 버티는 것이 중요합니다.",
    "nal": "삼재가 끝나가는 해입니다. 정리·관계 마무리 후 새 출발을 준비하기 좋습니다.",
    "none": "올해는 들·눌·날 삼재에 해당하지 않습니다.",
}


def _birth_group_key(year_zhi: str) -> Optional[frozenset]:
    for group in _SAMJAE_BY_BIRTH_GROUP:
        if year_zhi in group:
            return group
    return None


def samjae_triplet_for_birth_year_zhi(year_zhi: str) -> Optional[Tuple[str, str, str]]:
    """(들 지지, 눌 지지, 날 지지) 또는 None."""
    gk = _birth_group_key(year_zhi)
    if not gk:
        return None
    return _SAMJAE_BY_BIRTH_GROUP[gk]


def phase_for_target_zhi(
    birth_year_zhi: str, target_year_zhi: str
) -> str:
    """deul | nul | nal | none"""
    tri = samjae_triplet_for_birth_year_zhi(birth_year_zhi)
    if not tri:
        return "none"
    deul, nul, nal = tri
    if target_year_zhi == deul:
        return "deul"
    if target_year_zhi == nul:
        return "nul"
    if target_year_zhi == nal:
        return "nal"
    return "none"


def _samjae_years_near(
    birth_year_zhi: str, center_year: int, *, span: int = 18
) -> List[Dict[str, Any]]:
    """center 전후에서 들·눌·날 삼재 연도 목록."""
    tri = samjae_triplet_for_birth_year_zhi(birth_year_zhi)
    if not tri:
        return []
    deul_z, nul_z, nal_z = tri
    zhi_set = {deul_z, nul_z, nal_z}
    rows: List[Dict[str, Any]] = []
    for y in range(center_year - span, center_year + span + 1):
        if y < 1800 or y > 2100:
            continue
        info = sw.yearly_pillar_for_solar_year(y)
        zhi = info["zhi"]
        if zhi not in zhi_set:
            continue
        phase = phase_for_target_zhi(birth_year_zhi, zhi)
        rows.append(
            {
                "연도": y,
                "간지": info["pillar"],
                "지지": zhi,
                "단계": _PHASE_LABEL.get(phase, phase),
                "단계_코드": phase,
            }
        )
    return rows


def _pick_tip(phase: str) -> str:
    db = nl.load_narrative_db("sinsal_sentences")
    block = (db.get("samjae_v2") or {}) if isinstance(db, dict) else {}
    key = {"deul": "deul", "nul": "nul", "nal": "nal", "none": "none"}.get(phase, "none")
    pool = block.get(key) or block.get("general") or []
    if isinstance(pool, list) and pool:
        return nl.sanitize_narrative_text(str(pool[0]))
    return _PHASE_DESC.get(phase, "")


def analyze_samjae(
    birth_year_zhi: str,
    *,
    target_year: Optional[int] = None,
) -> Dict[str, Any]:
    """올해(또는 target_year) 삼재 판정 + 본인 삼재 3년 주기 안내."""
    from datetime import datetime

    year = int(target_year if target_year is not None else datetime.now().year)
    sew = sw.yearly_pillar_for_solar_year(year)
    target_zhi = sew["zhi"]
    tri = samjae_triplet_for_birth_year_zhi(birth_year_zhi)
    phase = phase_for_target_zhi(birth_year_zhi, target_zhi)

    deul_z = nul_z = nal_z = ""
    if tri:
        deul_z, nul_z, nal_z = tri

    cycle = _samjae_years_near(birth_year_zhi, year, span=14)
    # 가장 가까운 들·눌·날 3년 묶음 (기준연도 포함 사이클)
    cycle_window = [x for x in cycle if abs(x["연도"] - year) <= 4]
    if not cycle_window and cycle:
        cycle_window = cycle[:3]

    in_samjae = phase in ("deul", "nul", "nal")
    label = _PHASE_LABEL[phase]

    return {
        "기준_연도": year,
        "세운_간지": sew["pillar"],
        "세운_지지": target_zhi,
        "년지_띠": birth_year_zhi,
        "년지_띠_한글": gj.BRANCH_KR[gj.branch_index(birth_year_zhi)],
        "올해_삼재": label if in_samjae else "해당 없음",
        "올해_삼재_코드": phase,
        "삼재_여부": in_samjae,
        "들_지지": deul_z,
        "눌_지지": nul_z,
        "날_지지": nal_z,
        "들_라벨": f"들삼재({deul_z})" if deul_z else "",
        "눌_라벨": f"눌삼재({nul_z})" if nul_z else "",
        "날_라벨": f"날삼재({nal_z})" if nal_z else "",
        "한줄_요약": (
            f"{year}년 {sew['pillar']} — {label}"
            if in_samjae
            else f"{year}년 {sew['pillar']} — 올해는 삼재 해당 없음"
        ),
        "설명": _PHASE_DESC.get(phase, ""),
        "팁": _pick_tip(phase),
        "가까운_삼재_연도": cycle_window,
        "전후_삼재_목록": cycle,
    }
