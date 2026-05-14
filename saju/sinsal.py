# -*- coding: utf-8 -*-
"""
신살(神煞) — 길신·흉살 탐지 및 한 줄 해석.

각 항목은 ``analyze_sinsal`` 결과의 ``신살_목록``에서
``신살``, ``길흉``, ``글자``, ``위치``, ``해석`` 필드로 통일합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import ganji as gj

PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")
GAN_LABEL_KR = {"year": "년간", "month": "월간", "day": "일간", "hour": "시간"}
ZHI_LABEL = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}

_BRANCH_IDX = {z: i for i, z in enumerate(gj.BRANCHES)}


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
                    "학문·시험·글씨 재능이 살아나기 쉬운 별입니다.",
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
                    "배움의 기운이 두터워 전공·자격에 유리한 편입니다.",
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
                    "복록·생활안정에 긍정적으로 작용하기 쉬운 별입니다.",
                )
            )

    # --- 흉살 · 역마 도화 화개 (년지 삼합 기준 일지 전통과 동일 계열) ---
    ylm, doh, hwg = _yeolma_dohwa_hwagae(year_zhi)
    for tag, marker, msg in (
        ("역마살", ylm, "이동·변동·해외·직무 전환 에너지가 강해졌다 약해졌다 합니다."),
        ("도화살", doh, "인기·이성·표현력이 붙으나 관계 번복도 따라올 수 있습니다."),
        ("화개살", hwg, "종교·예술·고독·내면 탐구 기질이 배경에 깔리기 쉽습니다."),
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
                    "급변·탈취·우발적 손실 기운을 동반할 수 있어 재물·계약을 안정적으로 가져가야 합니다.",
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
                    "망실·허탕·계획 차질을 일으키기 쉬운 공망형 긴장입니다.",
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
                    "칼날·금속·수술·결단력이 강해 한쪽으로는 부상 소인이 되기도 합니다.",
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
                "정신 피로·불안·신경 과민이 올라오기 쉬워 숙면·스트레스 관리가 필요합니다.",
            )
        )

    # 공망 — 일주·년주 순각
    for label_key, pk in (("일주", "day"), ("년주", "year")):
        pillar = pillars[pk]["pillar"]
        k1, k2 = _xunkong_for_pillar(pillar)
        kong_set = {k1, k2}
        hit_labels = [ZHI_LABEL[k] for k in PILLAR_KEYS if zhis[k] in kong_set]
        if hit_labels:
            rows.append(
                _row(
                    "공망(空亡)",
                    "흉",
                    f"{k1}{k2}",
                    f"{label_key} 순공망 시 → {_format_where(hit_labels)}",
                    "허무·실속 부족·인연 공허를 나타내 재물·인연에서 헛수고를 줄여야 합니다.",
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
                "상가·조문·비보 이벤트와 연결되기 쉬워 가족 건강을 챙깁니다.",
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

    # 요약: 신살별 문자열 + 표준 행 목록 (표준 행만 객체 — 프론트에서 표 처리)
    def _fmt(r: Dict[str, str]) -> str:
        return f"{r['글자']} @ {r['위치']} — {r['해석']}"

    by_name: Dict[str, List[str]] = {}
    for r in rows:
        by_name.setdefault(r["신살"], []).append(_fmt(r))

    return {"신살_목록": rows, **by_name}
