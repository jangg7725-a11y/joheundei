# -*- coding: utf-8 -*-
"""
신살(神煞) — 길신·흉살 탐지 및 한 줄 해석.

각 항목은 ``analyze_sinsal`` 결과의 ``신살_목록``에서
``신살``, ``길흉``, ``글자``, ``위치``, ``해석`` 필드로 통일합니다.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import ganji as gj

PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")
GAN_LABEL_KR = {"year": "년간", "month": "월간", "day": "일간", "hour": "시간"}
ZHI_LABEL = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}

_BRANCH_IDX = {z: i for i, z in enumerate(gj.BRANCHES)}
_PO_SET = {frozenset(p) for p in gj.LIU_PO}
_HAI_SET = {frozenset(p) for p in gj.LIU_HAI}
_LIU_HE_SET = {frozenset(p) for p in gj.LIU_HE}


def _row(kind: str, luck: str, glyph: str, where: str, note: str) -> Dict[str, str]:
    return {"신살": kind, "길흉": luck, "글자": glyph, "위치": where, "해석": note}


def _stem_yang(gan: str) -> bool:
    return gj.STEM_YIN_YANG[gj.stem_index(gan)] == "양"


def _female(gender: str) -> bool:
    g = gender.strip().lower()
    return g in ("female", "f", "여", "여성")


def _collect_zhis(pillars: dict) -> Dict[str, str]:
    return {k: pillars[k]["zhi"] for k in PILLAR_KEYS}


def _collect_gans(pillars: dict) -> Dict[str, str]:
    return {k: pillars[k]["gan"] for k in PILLAR_KEYS}


def _positions_with_zhi(zhis: Dict[str, str], target: str) -> List[str]:
    return [ZHI_LABEL[k] for k in PILLAR_KEYS if zhis[k] == target]


def _format_where(labels: List[str]) -> str:
    return ", ".join(labels) if labels else "해당없음"


def _jie_sha_and_wang_shen() -> Tuple[Dict[str, str], Dict[str, str]]:
    """년지 기준 겁살·망신(亡神) 지지."""
    jie_sha = {
        "申": "巳",
        "子": "巳",
        "辰": "巳",
        "亥": "申",
        "卯": "申",
        "未": "申",
        "寅": "亥",
        "午": "亥",
        "戌": "亥",
        "巳": "寅",
        "酉": "寅",
        "丑": "寅",
    }
    wang_shen = {
        "申": "亥",
        "子": "亥",
        "辰": "亥",
        "亥": "寅",
        "卯": "寅",
        "未": "寅",
        "寅": "巳",
        "午": "巳",
        "戌": "巳",
        "巳": "申",
        "酉": "申",
        "丑": "申",
    }
    return jie_sha, wang_shen


def _yeolma_dohwa_hwagae(year_zhi: str) -> Tuple[str, str, str]:
    groups = [
        (frozenset({"申", "子", "辰"}), "寅", "酉", "辰"),
        (frozenset({"亥", "卯", "未"}), "巳", "子", "未"),
        (frozenset({"寅", "午", "戌"}), "申", "卯", "戌"),
        (frozenset({"巳", "酉", "丑"}), "亥", "午", "丑"),
    ]
    for tri, yeol, doh, hwa in groups:
        if year_zhi in tri:
            return yeol, doh, hwa
    return "", "", ""


def _branch_chong(z1: str, z2: str) -> bool:
    pair = frozenset((z1, z2))
    return any(pair == frozenset(p) for p in gj.CHONG_PAIRS)


def _branch_po(z1: str, z2: str) -> bool:
    return frozenset((z1, z2)) in _PO_SET


def _branch_hai(z1: str, z2: str) -> bool:
    return frozenset((z1, z2)) in _HAI_SET


def _branch_liu_he(z1: str, z2: str) -> bool:
    return frozenset((z1, z2)) in _LIU_HE_SET


def _kongwang_wolwoon_hit(mon_zhi: str, pillars: dict) -> bool:
    """``wolwoon._kongwang_hit`` 과 동일 — 일주·년주 공망 지지."""
    k1, k2 = _xunkong_for_pillar(pillars["day"]["pillar"])
    ky1, ky2 = _xunkong_for_pillar(pillars["year"]["pillar"])
    return mon_zhi in {k1, k2, ky1, ky2}


def _append_period_hit(hits: List[Dict[str, Any]], row: Dict[str, Any], *, key: str = "") -> None:
    dedupe = key or f"{row.get('신살')}:{row.get('글자')}:{row.get('위치')}"
    if any(f"{r.get('신살')}:{r.get('글자')}:{r.get('위치')}" == dedupe for r in hits):
        return
    hits.append(row)


def _split_positions(where: str) -> List[str]:
    """「년지, 일지」처럼 쉼표로 나열된 위치를 분리합니다."""
    s = str(where or "").strip()
    if not s:
        return [s]
    if "→" in s or "기준" in s or "공망" in s:
        return [s]
    parts = [p.strip() for p in re.split(r"[,，、]", s) if p.strip()]
    return parts if len(parts) > 1 else [s]


def expand_sinsal_rows_by_position(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """한 신살이 여러 궁에 걸리면 주(위치)별로 행을 나눕니다."""
    out: List[Dict[str, str]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        where = str(r.get("위치") or "")
        parts = _split_positions(where)
        if len(parts) <= 1:
            out.append(dict(r))
            continue
        for part in parts:
            nr = dict(r)
            nr["위치"] = part
            out.append(nr)
    return out


def build_pillar_sinsal_index(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """원국 연·월·일·시주에 해당하는 신살 목록."""
    out: Dict[str, List[Dict[str, str]]] = {k: [] for k in PILLAR_KEYS}
    seen: Dict[str, Set[str]] = {k: set() for k in PILLAR_KEYS}
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("신살") or "").strip()
        if not name or name == "공망(空亡)":
            continue
        where = str(r.get("위치") or "")
        matched: Set[str] = set()
        for pk in PILLAR_KEYS:
            if ZHI_LABEL[pk] in where or GAN_LABEL_KR[pk] in where:
                matched.add(pk)
        if name == "괴강살" and where in ("일주",):
            matched.add("day")
        if not matched and where in ("해당없음", ""):
            continue
        mini = {
            "신살": name,
            "길흉": str(r.get("길흉") or ""),
            "글자": str(r.get("글자") or ""),
        }
        for pk in matched:
            sig = f"{name}:{mini['글자']}:{pk}"
            if sig in seen[pk]:
                continue
            seen[pk].add(sig)
            out[pk].append(mini)
    return out


def _wolwoon_period_extras(
    day_master: str,
    pillars: dict,
    period_gan: str,
    period_zhi: str,
    sewoon_zhi: str,
    *,
    native_zhi: Set[str],
    native_names: Set[str],
    scope: str = "월운",
) -> List[Dict[str, Any]]:
    """월운·세운 시기에 원국과 맞물리는 충·공망·복음·삼합 신호."""
    extra: List[Dict[str, Any]] = []
    pk_label = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
    period_word = "세운 지지" if scope == "세운" else "이달 월지"

    for pk in PILLAR_KEYS:
        nz = pillars[pk]["zhi"]
        glyph = f"{period_zhi}{nz}"
        if _branch_chong(period_zhi, nz):
            _append_period_hit(
                extra,
                {
                    "신살": f"{pk_label[pk]}충",
                    "길흉": "흉",
                    "글자": glyph,
                    "위치": scope,
                    "해석": f"{period_word} {period_zhi}가 원국 {pk_label[pk]} {nz}와 충합니다. {ZHI_LABEL[pk]} 축 변동을 의식하세요.",
                    "중첩": period_zhi == nz or nz in native_zhi,
                },
                key=f"{pk_label[pk]}충",
            )
        if _branch_po(period_zhi, nz):
            _append_period_hit(
                extra,
                {
                    "신살": f"{scope}파",
                    "길흉": "흉",
                    "글자": f"{period_zhi}×{nz}",
                    "위치": scope,
                    "해석": f"{pk_label[pk]}({nz})와 파(破) — 계약·재물 이탈을 조심하세요.",
                    "중첩": False,
                },
                key=f"{scope}파",
            )
        if _branch_hai(period_zhi, nz):
            _append_period_hit(
                extra,
                {
                    "신살": f"{scope}해",
                    "길흉": "흉",
                    "글자": f"{period_zhi}×{nz}",
                    "위치": scope,
                    "해석": f"{pk_label[pk]}({nz})와 해(害) — 인연·건강 마찰을 의식하세요.",
                    "중첩": False,
                },
                key=f"{scope}해",
            )
        if _branch_liu_he(period_zhi, nz):
            _append_period_hit(
                extra,
                {
                    "신살": f"{scope}육합",
                    "길흉": "길",
                    "글자": glyph,
                    "위치": scope,
                    "해석": f"{pk_label[pk]}({nz})와 육합 — 협력·인연이 붙는 달입니다.",
                    "중첩": False,
                },
                key=f"{scope}육합",
            )

    dual_where: List[str] = []
    for pk in PILLAR_KEYS:
        nz = pillars[pk]["zhi"]
        if sewoon_zhi and _branch_chong(sewoon_zhi, nz) and _branch_chong(period_zhi, nz):
            dual_where.append(f"{pk_label[pk]}({nz})")
    if dual_where:
        _append_period_hit(
            extra,
            {
                "신살": "세운·월운 동시충",
                "길흉": "흉",
                "글자": f"{sewoon_zhi}{period_zhi}",
                "위치": scope,
                "해석": f"세운 {sewoon_zhi}·월운 {period_zhi}가 원국 {', '.join(dual_where)}에 동시 충 — 이달 리스크가 겹칩니다.",
                "중첩": True,
            },
            key="세운·월운 동시충",
        )

    if sewoon_zhi and sewoon_zhi == period_zhi:
        _append_period_hit(
            extra,
            {
                "신살": "세운월운 복음",
                "길흉": "흉",
                "글자": period_zhi,
                "위치": scope,
                "해석": "세운 지지와 월운 지지가 같아 과열·중첩되는 달입니다. 무리한 확장은 줄이세요.",
                "중첩": period_zhi in native_zhi,
            },
            key="세운월운 복음",
        )

    if _kongwang_wolwoon_hit(period_zhi, pillars):
        _append_period_hit(
            extra,
            {
                "신살": f"공망({scope})",
                "길흉": "흉",
                "글자": period_zhi,
                "위치": scope,
                "해석": f"일·년 공망 지지에 {period_word} {period_zhi}가 걸려 실속·약속 허실을 의식하세요.",
                "중첩": period_zhi in native_zhi,
            },
            key=f"공망({scope})",
        )

    all_z = {period_zhi, sewoon_zhi, *native_zhi} if sewoon_zhi else {period_zhi, *native_zhi}
    for tri, label in gj.SAN_HE_GROUPS:
        if tri <= all_z:
            _append_period_hit(
                extra,
                {
                    "신살": "삼합완성",
                    "길흉": "길",
                    "글자": "".join(sorted(tri)),
                    "위치": scope,
                    "해석": f"세운·월운·원국에 {label} 삼합({''.join(sorted(tri))})이 모여 기회가 열리는 달입니다.",
                    "중첩": bool(tri & native_zhi),
                },
                key="삼합완성",
            )
            break

    _ = day_master, period_gan, native_names  # 시그니처 확장 여지
    return extra


def _baekho_period_hit(year_zhi: str, period_zhi: str) -> bool:
    """년지 삼합 백호 지와 일치하거나 충(冲)할 때 발동 — ``ilwoon._baekho_hit`` 과 동일."""
    bh = _baekho_zhi(year_zhi)
    if not bh:
        return False
    return period_zhi == bh or _branch_chong(period_zhi, bh)


def _baekho_zhi(year_zhi: str) -> str:
    """년지 삼합 기준 백호 지."""
    m = {
        "寅": "申",
        "午": "申",
        "戌": "申",
        "申": "寅",
        "子": "寅",
        "辰": "寅",
        "巳": "亥",
        "酉": "亥",
        "丑": "亥",
        "亥": "巳",
        "卯": "巳",
        "未": "巳",
    }
    return m.get(year_zhi, "")


def _xunkong_for_pillar(pillar: str) -> Tuple[str, str]:
    idx = gj.jiazi_index(pillar)
    pair = [
        ("戌", "亥"),
        ("申", "酉"),
        ("午", "未"),
        ("辰", "巳"),
        ("寅", "卯"),
        ("子", "丑"),
    ]
    return pair[idx // 10]


def kongmang_list_for_pillars(pillars: dict) -> List[str]:
    """일주 순공 기준 공망 지지 두 글자."""
    k1, k2 = _xunkong_for_pillar(pillars["day"]["pillar"])
    return [k1, k2]


def kongmang_story(
    kongmang_list: list,
    pillars: dict,
    female: bool,
) -> dict:
    """공망 글자·위치·실생활 영향·보완법."""
    _ = female
    if not kongmang_list:
        return {
            "공망_글자": [],
            "위치": "",
            "해설": "이 사주에는 공망이 없습니다",
            "실생활_영향": "",
            "보완법": "",
        }

    pillar_name = {
        "year": "년주",
        "month": "월주",
        "day": "일주",
        "hour": "시주",
    }
    km_set = set(kongmang_list)

    affected: List[str] = []
    for pk, pv in pillars.items():
        if pk not in pillar_name:
            continue
        if pv["zhi"] in km_set:
            affected.append(f"{pillar_name[pk]}({pv['zhi']})")

    kongmang_effect = {
        "year": (
            "부모·가문 인연이 약하거나 "
            "일찍 독립하는 경우가 많습니다. "
            "초년 환경이 불안정했을 수 있습니다"
        ),
        "month": (
            "직업·사회생활에서 "
            "예상치 못한 공백이 생기기 쉽습니다. "
            "커리어 중단·이직이 반복될 수 있습니다"
        ),
        "day": (
            "배우자 인연이 약하거나 늦습니다. "
            "결혼보다 독립적인 삶이 "
            "더 잘 맞을 수 있습니다"
        ),
        "hour": (
            "자녀 인연이 약하거나 늦습니다. "
            "말년에 혼자 지내는 시간이 "
            "많아질 수 있습니다"
        ),
    }

    effects: List[str] = []
    for pk, pv in pillars.items():
        if pk not in pillar_name:
            continue
        if pv["zhi"] in km_set:
            eff = kongmang_effect.get(pk, "")
            if eff:
                effects.append(eff)

    remedy = (
        "공망은 정신·철학·종교에서 "
        "오히려 큰 능력이 발휘됩니다. "
        "공망이 된 자리의 인연보다 "
        "나머지 자리의 인연을 더 소중히 하세요. "
        "공망이 채워지는 대운·세운(공망 글자가 "
        "들어오는 해)에 해당 영역이 활성화됩니다"
    )

    glyphs = "·".join(kongmang_list)
    affected_str = "·".join(affected) if affected else "원국 지지에는 해당 없음(순공만 적용)"

    if affected:
        haeseol = (
            f"이 사주의 공망은 「{glyphs}」입니다. "
            f"{affected_str}이 공망에 해당합니다. "
            f"공망이 된 자리는 해당 인연·역할이 "
            f"약하거나 비어있는 느낌을 줍니다"
        )
        impact = " ".join(effects)
    else:
        haeseol = (
            f"이 사주의 순공(旬空)은 「{glyphs}」입니다. "
            f"원국 네 지지에는 공망 글자가 없으나, "
            f"대운·세운에서 「{glyphs}」가 들어올 때 해당 주제가 요동칩니다"
        )
        impact = (
            "평소에는 공망 영향이 약하고, "
            "공망 글자가 들어오는 운에서만 허실·공백이 드러나기 쉽습니다"
        )

    return {
        "공망_글자": list(kongmang_list),
        "위치": affected_str,
        "해설": haeseol,
        "실생활_영향": impact,
        "보완법": remedy,
    }


def _cheoneul(day_master: str) -> Set[str]:
    return {
        "甲": {"丑", "未"},
        "戊": {"丑", "未"},
        "庚": {"丑", "未"},
        "乙": {"子", "申"},
        "己": {"子", "申"},
        "丙": {"酉", "亥"},
        "丁": {"酉", "亥"},
        "壬": {"卯", "巳"},
        "癸": {"卯", "巳"},
        "辛": {"寅", "午"},
    }.get(day_master, set())


def _munchang(day_master: str) -> Set[str]:
    return {
        "甲": {"巳"},
        "乙": {"午"},
        "丙": {"申"},
        "戊": {"申"},
        "丁": {"酉"},
        "己": {"酉"},
        "庚": {"亥"},
        "辛": {"子"},
        "壬": {"寅"},
        "癸": {"卯"},
    }.get(day_master, set())


def _hakdang(day_master: str) -> Set[str]:
    elem = gj.element_of_stem(day_master)
    return {
        "목": {"亥"},
        "화": {"寅"},
        "토": {"申"},
        "금": {"巳"},
        "수": {"申"},
    }.get(elem, set())


def _woldeok_month_gan(month_zhi: str) -> Optional[str]:
    if month_zhi in {"寅", "午", "戌"}:
        return "丙"
    if month_zhi in {"申", "子", "辰"}:
        return "壬"
    if month_zhi in {"亥", "卯", "未"}:
        return "甲"
    if month_zhi in {"巳", "酉", "丑"}:
        return "庚"
    return None


def _cheondeok_gan(month_zhi: str) -> Optional[str]:
    return {
        "寅": "丁",
        "卯": "申",
        "辰": "壬",
        "巳": "辛",
        "午": "亥",
        "未": "甲",
        "申": "癸",
        "酉": "寅",
        "戌": "丙",
        "亥": "乙",
        "子": "巳",
        "丑": "庚",
    }.get(month_zhi)


def _bokseong(day_master: str) -> Set[str]:
    return {
        "甲": {"寅", "子"},
        "丙": {"寅", "子"},
        "乙": {"卯", "亥"},
        "癸": {"卯", "丑"},
        "戊": {"申"},
        "己": {"酉"},
        "丁": {"亥"},
        "庚": {"午"},
        "辛": {"巳"},
        "壬": {"辰"},
    }.get(day_master, set())


def _yangin_branch(day_master: str) -> Optional[str]:
    return {
        "甲": "卯",
        "乙": "寅",
        "丙": "午",
        "戊": "午",
        "丁": "巳",
        "己": "巳",
        "庚": "酉",
        "辛": "申",
        "壬": "子",
        "癸": "亥",
    }.get(day_master)


def _wonjin_zhi(year_zhi: str, year_gan: str, gender: str) -> Optional[str]:
    yi = _BRANCH_IDX[year_zhi]
    clash = (yi + 6) % 12
    male = not _female(gender)
    yang_stem = _stem_yang(year_gan)
    yang_nan_yin_nv = (male and yang_stem) or ((not male) and (not yang_stem))
    if yang_nan_yin_nv:
        return gj.BRANCHES[(clash - 1) % 12]
    return gj.BRANCHES[(clash + 1) % 12]


GOEGANG_PILLARS = frozenset({"戊戌", "戊辰", "庚戌", "庚辰", "壬辰"})

# 삼합 왕지(将星) — 장성살이 걸리는 지지
_SANHE_WANG_ZHI = frozenset({"子", "午", "卯", "酉"})


def _dohwa_branch_by_stem(stem: str) -> str:
    """六甲常識 桃花 — 甲戌庚→酉, 乙亥辛→午, 丙丁壬→卯, 戊己癸→子."""
    if stem in {"甲", "庚"}:
        return "酉"
    if stem in {"乙", "辛"}:
        return "午"
    if stem in {"丙", "丁", "壬"}:
        return "卯"
    if stem in {"戊", "己", "癸"}:
        return "子"
    return ""


def _hongyeom_branch(day_master: str) -> str:
    """홍염살 — 일간 기준 지지 (辛→酉 등)."""
    return {
        "甲": "午",
        "乙": "午",
        "丙": "寅",
        "丁": "未",
        "戊": "辰",
        "己": "辰",
        "庚": "戌",
        "辛": "酉",
        "壬": "子",
        "癸": "申",
    }.get(day_master, "")


def _mungok_branch(day_master: str) -> str:
    """문곡귀인(文曲) — 일간 기준 지지."""
    return {
        "甲": "亥",
        "乙": "子",
        "丙": "寅",
        "丁": "卯",
        "戊": "寅",
        "己": "卯",
        "庚": "巳",
        "辛": "午",
        "壬": "申",
        "癸": "酉",
    }.get(day_master, "")


def _cheonbok_branch(day_master: str) -> str:
    """천복귀인(天福) — 일간 기준 지지."""
    return {
        "甲": "酉",
        "乙": "申",
        "丙": "子",
        "丁": "亥",
        "戊": "子",
        "己": "亥",
        "庚": "卯",
        "辛": "巳",
        "壬": "午",
        "癸": "巳",
    }.get(day_master, "")


def _row_sig(row: Dict[str, str]) -> Tuple[str, str, str]:
    return (
        str(row.get("신살") or ""),
        str(row.get("글자") or ""),
        str(row.get("위치") or ""),
    )


def _append_branch_star(
    rows: List[Dict[str, str]],
    seen: Set[Tuple[str, str, str]],
    *,
    kind: str,
    luck: str,
    target_zhi: str,
    zhis: Dict[str, str],
    note: str,
) -> None:
    """대상 지지가 실제로 걸린 주(년·월·일·시 지)에만 신살 행을 추가합니다."""
    if not target_zhi:
        return
    for pk in PILLAR_KEYS:
        if zhis[pk] != target_zhi:
            continue
        where = ZHI_LABEL[pk]
        sig = (kind, target_zhi, where)
        if sig in seen:
            continue
        seen.add(sig)
        rows.append(_row(kind, luck, target_zhi, where, note))


def _append_native_pillar_stars(
    rows: List[Dict[str, str]],
    day_master: str,
    pillars: dict,
    zhis: Dict[str, str],
    gans: Dict[str, str],
) -> None:
    """만세력 앱과 같이 지지·간지가 놓인 주(柱)에 직접 붙는 신살."""
    seen = {_row_sig(r) for r in rows}

    for pk in PILLAR_KEYS:
        z = zhis[pk]
        if z not in _SANHE_WANG_ZHI:
            continue
        where = ZHI_LABEL[pk]
        sig = ("장성살", z, where)
        if sig in seen:
            continue
        seen.add(sig)
        rows.append(
            _row(
                "장성살",
                "길",
                z,
                where,
                "삼합 왕지(中神)에 해당하는 자리로 권위·주관·존재감이 강합니다.",
            )
        )

    for stem, label in ((day_master, "일간"), (gans["year"], "년간")):
        dh = _dohwa_branch_by_stem(stem)
        if dh:
            _append_branch_star(
                rows,
                seen,
                kind="도화살",
                luck="중",
                target_zhi=dh,
                zhis=zhis,
                note=f"{label} 기준 도화(桃花) 지지로 인기·이성·표현력이 풍부합니다.",
            )

    _append_branch_star(
        rows,
        seen,
        kind="홍염살",
        luck="중",
        target_zhi=_hongyeom_branch(day_master),
        zhis=zhis,
        note="홍염(红艳)으로 매력·대인 접촉이 강하나 감정 기복·관계 변수를 주의해야 합니다.",
    )
    _append_branch_star(
        rows,
        seen,
        kind="문곡귀인",
        luck="길",
        target_zhi=_mungok_branch(day_master),
        zhis=zhis,
        note="문곡(文曲)으로 예술·표현·설득력·학습 재능이 있습니다.",
    )
    _append_branch_star(
        rows,
        seen,
        kind="천복귀인",
        luck="길",
        target_zhi=_cheonbok_branch(day_master),
        zhis=zhis,
        note="천복(天福)으로 복덕·후원·생활 안정에 도움이 되는 길신입니다.",
    )

    km_day = set(_xunkong_for_pillar(pillars["day"]["pillar"]))
    for pk in PILLAR_KEYS:
        z = zhis[pk]
        if z not in km_day:
            continue
        where = ZHI_LABEL[pk]
        sig = ("공망살", z, where)
        if sig in seen:
            continue
        seen.add(sig)
        glyphs = "".join(sorted(km_day))
        rows.append(
            _row(
                "공망살",
                "흉",
                z,
                where,
                (
                    f"일주 순공(旬空) {glyphs}에 해당하는 지지로 "
                    "허무·실속 부족·인연 공허가 드러납니다."
                ),
            )
        )


def analyze_sinsal(
    day_master: str,
    pillars: dict,
    *,
    gender: str = "male",
) -> Dict[str, Any]:
    zhis = _collect_zhis(pillars)
    gans = _collect_gans(pillars)
    year_zhi = zhis["year"]
    year_gan = gans["year"]
    month_zhi = zhis["month"]
    day_pillar = pillars["day"]["pillar"]
    rows: List[Dict[str, str]] = []

    # --- 길신 ---
    ce = _cheoneul(day_master)
    for z in ce:
        pos = _positions_with_zhi(zhis, z)
        if pos:
            rows.append(
                _row(
                    "천을귀인",
                    "길",
                    z,
                    _format_where(pos),
                    "위기 시 귀인·도움 손길, 관직·명예 기복 완화에 도움되는 길신입니다.",
                )
            )

    mc = _munchang(day_master)
    for z in mc:
        pos = _positions_with_zhi(zhis, z)
        if pos:
            rows.append(
                _row(
                    "문창귀인",
                    "길",
                    z,
                    _format_where(pos),
                    "학문·시험·글씨 재능이 있습니다.",
                )
            )

    hd = _hakdang(day_master)
    for z in hd:
        pos = _positions_with_zhi(zhis, z)
        if pos:
            rows.append(
                _row(
                    "학당귀인",
                    "길",
                    z,
                    _format_where(pos),
                    "배움의 기운이 두터워 전공·자격에 유리합니다.",
                )
            )

    wg = _woldeok_month_gan(month_zhi)
    if wg:
        pos = [GAN_LABEL_KR[k] for k in PILLAR_KEYS if gans[k] == wg]
        if pos:
            rows.append(
                _row(
                    "월덕귀인",
                    "길",
                    wg,
                    _format_where(pos),
                    "월덕으로 재난·소송을 덜어 주는 덕성 별입니다.",
                )
            )

    cg = _cheondeok_gan(month_zhi)
    if cg:
        pos = [GAN_LABEL_KR[k] for k in PILLAR_KEYS if gans[k] == cg]
        if pos:
            rows.append(
                _row(
                    "천덕귀인",
                    "길",
                    cg,
                    _format_where(pos),
                    "하늘의 덕으로 큰 화를 멀리하는 길신입니다.",
                )
            )

    bs = _bokseong(day_master)
    for z in bs:
        pos = _positions_with_zhi(zhis, z)
        if pos:
            rows.append(
                _row(
                    "복성귀인",
                    "길",
                    z,
                    _format_where(pos),
                    "복록·생활안정에 긍정적으로 작용합니다.",
                )
            )

    # --- 흉살 · 역마 도화 화개 (년지 삼합 기준 일지 전통과 동일 계열) ---
    ylm, doh, hwg = _yeolma_dohwa_hwagae(year_zhi)
    for tag, marker, msg in (
        ("역마살", ylm, "이동·변동·해외·직무 전환 에너지가 강해졌다 약해졌다 합니다."),
        ("도화살", doh, "인기·이성·표현력이 풍부하나 관계 번복에 주의해야 합니다."),
        ("화개살", hwg, "종교·예술·고독·내면 탐구 기질이 배경에 깔립니다."),
    ):
        if not marker:
            continue
        pos = _positions_with_zhi(zhis, marker)
        if pos:
            rows.append(_row(tag, "흉", marker, _format_where(pos), msg))

    jie_tbl, wang_tbl = _jie_sha_and_wang_shen()
    jz = jie_tbl.get(year_zhi, "")
    if jz:
        pos = _positions_with_zhi(zhis, jz)
        if pos:
            rows.append(
                _row(
                    "겁살",
                    "흉",
                    jz,
                    _format_where(pos),
                    "급변·탈취·우발적 손실 기운을 동반합니다. 재물·계약을 안정적으로 관리하세요.",
                )
            )

    wz = wang_tbl.get(year_zhi, "")
    if wz:
        pos = _positions_with_zhi(zhis, wz)
        if pos:
            rows.append(
                _row(
                    "망신살",
                    "흉",
                    wz,
                    _format_where(pos),
                    "망실·허탕·계획 차질의 공망형 긴장입니다.",
                )
            )

    bh = _baekho_zhi(year_zhi)
    if bh:
        pos = _positions_with_zhi(zhis, bh)
        if pos:
            rows.append(
                _row(
                    "백호살",
                    "흉",
                    bh,
                    _format_where(pos),
                    "금 기운의 급성으로 피기·외상·수술·교통 등 급한 붉은 사건을 경계합니다.",
                )
            )

    yr = _yangin_branch(day_master)
    if yr:
        pos = _positions_with_zhi(zhis, yr)
        if pos:
            rows.append(
                _row(
                    "양인살",
                    "흉",
                    yr,
                    _format_where(pos),
                    "칼날·금속·수술·결단력이 강하며 부상·수술 소인이 됩니다.",
                )
            )

    if day_pillar in GOEGANG_PILLARS:
        rows.append(
            _row(
                "괴강살",
                "흉",
                day_pillar,
                "일주",
                "강직하나 충돌이 크고 극단 기복이 있어 관계·건강 급사를 조심합니다.",
            )
        )

    wj = _wonjin_zhi(year_zhi, year_gan, gender)
    if wj:
        pos = _positions_with_zhi(zhis, wj)
        if pos:
            rows.append(
                _row(
                    "원진살",
                    "흉",
                    wj,
                    _format_where(pos),
                    "반복되는 원망·각 세워 싸움이 생겨 부부·동료 갈등 신호로 자주 봅니다.",
                )
            )

    siju_count = sum(1 for z in zhis.values() if z in {"寅", "巳", "申", "亥"})
    if day_master in {"壬", "癸"} and siju_count >= 2:
        hits = [ZHI_LABEL[k] for k in PILLAR_KEYS if zhis[k] in {"寅", "巳", "申", "亥"}]
        rows.append(
            _row(
                "귀문관살",
                "흉",
                "寅巳申亥",
                _format_where(hits),
                "정신 피로·불안·신경 과민이 올라옵니다. 숙면·스트레스 관리가 필요합니다.",
            )
        )

    sm = gj.BRANCHES[(_BRANCH_IDX[year_zhi] + 2) % 12]
    dk = gj.BRANCHES[(_BRANCH_IDX[year_zhi] - 2) % 12]
    sm_pos = _positions_with_zhi(zhis, sm)
    if sm_pos:
        rows.append(
            _row(
                "상문살",
                "흉",
                sm,
                _format_where(sm_pos),
                "상가·조문·비보 이벤트와 연결됩니다. 가족 건강을 챙기세요.",
            )
        )
    dk_pos = _positions_with_zhi(zhis, dk)
    if dk_pos:
        rows.append(
            _row(
                "조객살",
                "흉",
                dk,
                _format_where(dk_pos),
                "애도·이별·공연 한파 기운이 들어와 마음 공황을 조심합니다.",
            )
        )

    _append_native_pillar_stars(rows, day_master, pillars, zhis, gans)

    # 공망 요약(空亡) — 주별 공망살과 별도로 순공 안내·스토리 연동용
    k1, k2 = _xunkong_for_pillar(pillars["day"]["pillar"])
    km_hit = [ZHI_LABEL[k] for k in PILLAR_KEYS if zhis[k] in {k1, k2}]
    rows.append(
        _row(
            "공망(空亡)",
            "흉",
            f"{k1}{k2}",
            _format_where(km_hit) if km_hit else "원국 지지 해당 없음",
            (
                "일주 순공(旬空)에 해당하는 지지는 허무·실속 부족·인연 공허로 읽습니다. "
                "대운·세운에서 공망 지지를 충(沖)하면 충공(沖空)으로 오히려 활성화됩니다."
            ),
        )
    )

    # 요약: 신살별 문자열 + 표준 행 목록 (표준 행만 객체 — 프론트에서 표 처리)
    def _fmt(r: Dict[str, str]) -> str:
        return f"{r['글자']} @ {r['위치']} — {r['해석']}"

    by_name: Dict[str, List[str]] = {}
    for r in rows:
        by_name.setdefault(r["신살"], []).append(_fmt(r))

    km_list = kongmang_list_for_pillars(pillars)
    female = gender.strip().lower() in ("female", "f", "여", "여자", "여성")
    km_story = kongmang_story(km_list, pillars, female)
    rows_expanded = expand_sinsal_rows_by_position(rows)

    return {
        "신살_목록": rows_expanded,
        "신살_목록_요약": rows,
        "신살_주별": build_pillar_sinsal_index(rows_expanded),
        "신살_개수": {
            "전체": len(rows_expanded),
            "길": sum(1 for r in rows_expanded if r.get("길흉") == "길"),
            "흉": sum(1 for r in rows_expanded if r.get("길흉") == "흉"),
            "중": sum(1 for r in rows_expanded if r.get("길흉") not in ("길", "흉")),
        },
        "공망": km_list,
        "공망_맞춤": km_story,
        **by_name,
    }


def _period_jiesha_zhi(year_zhi: str) -> str:
    jie, _ = _jie_sha_and_wang_shen()
    return jie.get(year_zhi, "")


def _period_wangshen_zhi(year_zhi: str) -> str:
    _, wang = _jie_sha_and_wang_shen()
    return wang.get(year_zhi, "")


def _period_star_rules(month_zhi: str, *, day_pillar: str = "") -> Tuple[Tuple[str, str, Any, str], ...]:
    wg = _woldeok_month_gan(month_zhi) or ""
    cg = _cheondeok_gan(month_zhi) or ""
    km_day = set(_xunkong_for_pillar(day_pillar)) if day_pillar else set()
    return (
        ("천을귀인", "길", lambda dm, yz, yg, g, z: z in _cheoneul(dm), "귀인·도움 손길이 들어옵니다."),
        ("문창귀인", "길", lambda dm, yz, yg, g, z: z in _munchang(dm), "학문·시험·표현력이 살아납니다."),
        ("학당귀인", "길", lambda dm, yz, yg, g, z: z in _hakdang(dm), "배움·자격·전문성에 유리합니다."),
        ("복성귀인", "길", lambda dm, yz, yg, g, z: z in _bokseong(dm), "복록·인연·완충 기운이 붙습니다."),
        ("월덕귀인", "길", lambda dm, yz, yg, g, z, _wg=wg: bool(_wg and g == _wg), "월덕으로 재난·소송을 덜어 주는 덕성 별입니다."),
        ("천덕귀인", "길", lambda dm, yz, yg, g, z, _cg=cg: bool(_cg and g == _cg), "하늘의 덕으로 큰 화를 멀리하는 길신입니다."),
        ("역마살", "중", lambda dm, yz, yg, g, z: z == _yeolma_dohwa_hwagae(yz)[0], "이동·전환·외부 활동이 늘어납니다."),
        ("도화살", "중", lambda dm, yz, yg, g, z: z in {_dohwa_branch_by_stem(dm), _dohwa_branch_by_stem(yg), _yeolma_dohwa_hwagae(yz)[1]}, "이성·매력·대인 접촉이 활발해집니다."),
        ("화개살", "중", lambda dm, yz, yg, g, z: z == _yeolma_dohwa_hwagae(yz)[2], "예술·종교·고독·내면 탐구 기운이 붙습니다."),
        ("장성살", "길", lambda dm, yz, yg, g, z: z in _SANHE_WANG_ZHI, "권위·주관·존재감이 강해지는 시기입니다."),
        ("홍염살", "중", lambda dm, yz, yg, g, z: z == _hongyeom_branch(dm), "매력·대인 접촉이 강하나 감정 기복을 주의해야 합니다."),
        ("문곡귀인", "길", lambda dm, yz, yg, g, z: z == _mungok_branch(dm), "예술·표현·학습 재능이 살아납니다."),
        ("천복귀인", "길", lambda dm, yz, yg, g, z: z == _cheonbok_branch(dm), "복덕·후원·안정 기운이 붙습니다."),
        ("공망살", "흉", lambda dm, yz, yg, g, z, _km=km_day: z in _km, "공망 지지에 해당해 허실·인연 공허가 드러납니다."),
        ("겁살", "흉", lambda dm, yz, yg, g, z: z == _period_jiesha_zhi(yz), "급변·탈취·우발 손실을 조심하세요."),
        ("망신살", "흉", lambda dm, yz, yg, g, z: z == _period_wangshen_zhi(yz), "망실·허탕·계획 차질을 의식하세요."),
        ("백호살", "흉", None, "급성·외상·수술·교통 리스크를 의식하세요. (백호 지와 충·일치 시)"),
        ("양인살", "흉", lambda dm, yz, yg, g, z: z == _yangin_branch(dm), "결단력은 강하나 충동·외상·수술 주의가 필요합니다."),
        ("원진살", "흉", None, "반복 갈등·거리두기 이슈가 생깁니다."),
        ("상문살", "흉", lambda dm, yz, yg, g, z: z == gj.BRANCHES[(_BRANCH_IDX[yz] + 2) % 12], "조문·상가·가족 건강을 챙기세요."),
        ("조객살", "흉", lambda dm, yz, yg, g, z: z == gj.BRANCHES[(_BRANCH_IDX[yz] - 2) % 12], "애도·이별·마음 공황을 조심하세요."),
    )


def _period_sinsal_rows(
    day_master: str,
    pillars: dict,
    gender: str,
    period_gan: str,
    period_zhi: str,
    *,
    scope: str,
    sewoon_zhi: str = "",
) -> List[Dict[str, Any]]:
    zhis = _collect_zhis(pillars)
    gans = _collect_gans(pillars)
    native_zhi = set(zhis.values())
    native_block = analyze_sinsal(day_master, pillars, gender=gender)
    native_rows = native_block.get("신살_목록_요약") or native_block.get("신살_목록") or []
    native_names = {
        r.get("신살") for r in native_rows if isinstance(r, dict) and r.get("신살")
    }
    yz = zhis["year"]
    yg = gans["year"]
    mz = zhis["month"]
    hits: List[Dict[str, Any]] = []
    for name, luck, rule, note in _period_star_rules(mz, day_pillar=pillars["day"]["pillar"]):
        if name == "원진살":
            wj = _wonjin_zhi(yz, yg, gender)
            fired = bool(wj and period_zhi == wj)
        elif name == "백호살":
            fired = _baekho_period_hit(yz, period_zhi)
        else:
            fired = bool(rule and rule(day_master, yz, yg, period_gan, period_zhi))
        if not fired:
            continue
        overlap = period_zhi in native_zhi and name in native_names
        row: Dict[str, Any] = {
            "신살": name,
            "길흉": luck,
            "글자": period_zhi,
            "위치": scope,
            "해석": note,
            "중첩": overlap,
        }
        if overlap:
            row["해석"] = f"{note} ⚠️ 원국과 중첩 — {scope}에 특히 강하게 작용"
        hits.append(row)
    yr = _yangin_branch(day_master)
    if period_gan and yr and period_gan == day_master and "양인살" in native_names:
        hits.append(
            {
                "신살": "양인 천간",
                "길흉": "중",
                "글자": period_gan,
                "위치": scope,
                "해석": "결단력이 강하나 충동·날카로운 말·행동을 조절하세요.",
                "중첩": True,
            }
        )
    elif period_gan and _stem_yang(period_gan) and yr and period_zhi == yr:
        if not any(r.get("신살") == "양인살" for r in hits):
            hits.append(
                {
                    "신살": "양인 천간",
                    "길흉": "중",
                    "글자": period_gan,
                    "위치": scope,
                    "해석": "결단력이 강하나 충동·날카로운 말·행동을 조절하세요.",
                    "중첩": False,
                }
            )
    if scope == "일운":
        day_zhi = pillars["day"]["zhi"]
        if _branch_chong(period_zhi, day_zhi) and not any(r.get("신살") == "일지충" for r in hits):
            hits.append(
                {
                    "신살": "일지충",
                    "길흉": "흉",
                    "글자": f"{period_zhi}{day_zhi}",
                    "위치": scope,
                    "해석": "오늘 일진이 원국 일지와 충하여 배우자·내실·건강 리듬을 조절하세요.",
                    "중첩": period_zhi == day_zhi or day_zhi in native_zhi,
                }
            )
        k1, k2 = _xunkong_for_pillar(pillars["day"]["pillar"])
        if period_zhi in {k1, k2} and not any("공망" in str(r.get("신살", "")) for r in hits):
            hits.append(
                {
                    "신살": "공망(日空)",
                    "길흉": "흉",
                    "글자": period_zhi,
                    "위치": scope,
                    "해석": "일주 공망 지지에 오늘 일진이 걸려 실속·인연 허실을 의식하세요.",
                    "중첩": period_zhi in native_zhi,
                }
            )
    if scope in ("월운", "세운"):
        sw_z = sewoon_zhi if scope == "월운" else (sewoon_zhi or period_zhi)
        extra = _wolwoon_period_extras(
            day_master,
            pillars,
            period_gan,
            period_zhi,
            sw_z,
            native_zhi=native_zhi,
            native_names=native_names,
            scope=scope,
        )
        for row in extra:
            _append_period_hit(hits, row)
    return hits


def period_sinsal_pack(
    day_master: str,
    pillars: dict,
    gender: str,
    period_gan: str,
    period_zhi: str,
    *,
    scope: str,
    sewoon_zhi: str = "",
) -> Dict[str, Any]:
    rows = _period_sinsal_rows(
        day_master,
        pillars,
        gender,
        period_gan,
        period_zhi,
        scope=scope,
        sewoon_zhi=sewoon_zhi,
    )
    return {
        "간지": f"{period_gan}{period_zhi}",
        "범위": scope,
        "발동_목록": rows,
        "중첩_목록": [r for r in rows if r.get("중첩")],
    }


def sewoon_sinsal(
    day_master: str,
    pillars: dict,
    gender: str,
    sewoon_gan: str,
    sewoon_zhi: str,
) -> Dict[str, Any]:
    return period_sinsal_pack(
        day_master, pillars, gender, sewoon_gan, sewoon_zhi, scope="세운"
    )


def wolwoon_sinsal(
    day_master: str,
    pillars: dict,
    gender: str,
    month_gan: str,
    month_zhi: str,
    *,
    sewoon_zhi: str = "",
) -> Dict[str, Any]:
    return period_sinsal_pack(
        day_master,
        pillars,
        gender,
        month_gan,
        month_zhi,
        scope="월운",
        sewoon_zhi=sewoon_zhi,
    )


def ilwoon_sinsal(
    day_master: str,
    pillars: dict,
    gender: str,
    day_gan: str,
    day_zhi: str,
) -> Dict[str, Any]:
    return period_sinsal_pack(
        day_master, pillars, gender, day_gan, day_zhi, scope="일운"
    )
