# -*- coding: utf-8 -*-
"""
통합 타임라인 — 대운·세운·월운 3중 교차, 연령대별 이벤트 힌트,
과거 역산·향후 5년 요약을 한 번에 묶습니다.

• 규칙 기반 참고용이며, 파종·용신 해석에 따라 달라질 수 있습니다.
"""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import ganji as gj
from . import ilwoon as il
from . import sewoon as sw
from . import sinsal as sn
from . import wolwoon as ww

PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")

_HEX_PAST = "#9ca3af"
_HEX_NOW = "#d4af37"
_HEX_FUTURE = "#3b82f6"


def _native_zhis(pillars: dict) -> Set[str]:
    return {pillars[pk]["zhi"] for pk in PILLAR_KEYS}


def _split_ganzhi(gz: Optional[str]) -> Tuple[str, str]:
    if not gz or len(gz) < 2:
        return "", ""
    return gz[0], gz[1]


def _cycle_for_year(cycles: List[Dict[str, Any]], y: int) -> Optional[Dict[str, Any]]:
    for c in cycles:
        sy = c.get("start_year")
        ey = c.get("end_year")
        if sy is None or ey is None:
            continue
        if sy <= y <= ey:
            return c
    return None


def _dw_branch_clashes_native(dw_zhi: str, pillars: dict) -> bool:
    if not dw_zhi:
        return False
    return any(sw.branch_chong(dw_zhi, pillars[pk]["zhi"]) for pk in PILLAR_KEYS)


def _dw_yong_hit(dw_gan: str, dw_zhi: str, yong_elem: str) -> bool:
    if not dw_gan or not dw_zhi:
        return False
    elems = {gj.element_of_stem(dw_gan), gj.element_of_branch(dw_zhi)}
    return yong_elem in elems


def _sew_hui_hit(sew_row: Dict[str, Any], huisin_elems: List[str]) -> bool:
    if not huisin_elems:
        return False
    sg, sz = sew_row["천간"], sew_row["지지"]
    hit = {gj.element_of_stem(sg), gj.element_of_branch(sz)}
    return bool(hit & set(huisin_elems))


def _sanhap_completion_sewoon(native_zhis: Set[str], sew_zhi: str) -> Tuple[bool, Optional[str]]:
    for tri, label in gj.SAN_HE_GROUPS:
        if sew_zhi not in tri:
            continue
        if len(tri & native_zhis) != 2:
            continue
        if tri <= native_zhis | {sew_zhi}:
            return True, label
    return False, None


def _risk_0_100(sew_row: Dict[str, Any]) -> int:
    stars = int(sew_row.get("별점") or 3)
    luck = sew_row.get("운세등급", "보통")
    r = 48 - (stars - 3) * 14
    if luck == "흉운":
        r += 22
    elif luck == "길운":
        r -= 18
    return max(0, min(100, r))


def _year_phase(year: int, current_year: int) -> Tuple[str, str, str]:
    if year < current_year:
        return "과거", _HEX_PAST, "past_gray"
    if year == current_year:
        return "현재", _HEX_NOW, "present_gold"
    return "미래", _HEX_FUTURE, "future_blue"


def _scan_triple_periods(
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    cycles: List[Dict[str, Any]],
    yong_block: Dict[str, Any],
    year_from: int,
    year_to: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    yong_elem = yong_block.get("용신_오행") or ""
    huisin_elems = list(yong_block.get("희신") or [])

    triple_bad: List[Dict[str, Any]] = []
    triple_good: List[Dict[str, Any]] = []

    for Y in range(year_from, year_to + 1):
        cy = _cycle_for_year(cycles, Y)
        if not cy:
            continue
        dg, dz = _split_ganzhi(cy.get("ganzhi"))
        dw_chong = _dw_branch_clashes_native(dz, pillars)
        dw_yong = _dw_yong_hit(dg, dz, yong_elem)

        sew = sw.analyze_sewoon_year(day_master, pillars, gender, Y, counts=counts)
        sew_chong = len(sew.get("세운_지지_충") or []) > 0
        sew_hui = _sew_hui_hit(sew, huisin_elems)

        for slot in range(1, 13):
            w = ww.analyze_wolwoon_month(day_master, pillars, Y, slot)
            mon_chong = len(w["원국_충파해합형"]["충"]) > 0
            mon_he = len(w["원국_충파해합형"]["육합"]) > 0

            if dw_chong and sew_chong and mon_chong:
                triple_bad.append(
                    {
                        "연도": Y,
                        "절월번호": slot,
                        "월주": w["월주간지"],
                        "대운간지": cy.get("ganzhi"),
                        "세운간지": sew.get("간지"),
                        "유형": "삼중충",
                        "메시지": "생애 최대 위험 시기로 볼 만한 패턴(대운·세운·월운 동시 충)입니다.",
                    }
                )

            if dw_yong and sew_hui and mon_he:
                triple_good.append(
                    {
                        "연도": Y,
                        "절월번호": slot,
                        "월주": w["월주간지"],
                        "대운간지": cy.get("ganzhi"),
                        "세운간지": sew.get("간지"),
                        "유형": "삼중길",
                        "메시지": "생애 최대 기회 시기 후보(대운 용신 방향·세운 희신 오행·월운 육합)입니다.",
                    }
                )

    return triple_bad, triple_good


def _scan_age_events(
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    birth_year: int,
    year_from: int,
    year_to: int,
) -> List[Dict[str, Any]]:
    native_zhis = _native_zhis(pillars)
    year_zhi = pillars["year"]["zhi"]
    ylm = sn._yeolma_dohwa_hwagae(year_zhi)[0]  # type: ignore[attr-defined]

    events: List[Dict[str, Any]] = []
    for Y in range(year_from, year_to + 1):
        age = Y - birth_year
        sew = sw.analyze_sewoon_year(day_master, pillars, gender, Y, counts=counts)
        ev = sew.get("사건예측") or {}
        sz = sew["지지"]

        san_ok, san_lab = _sanhap_completion_sewoon(native_zhis, sz)

        tags: List[str] = []
        if ev.get("연애_결혼"):
            tags.append("결혼적령·연애기회")
        if san_ok or ev.get("재물획득"):
            tags.append("재물기회")
        if ev.get("실직_이직"):
            tags.append("직업변화")
        if ev.get("건강이상") or ev.get("수술_사고"):
            tags.append("건강위기")
        if ylm and sz == ylm:
            tags.append("이사·이동·역마")

        if tags:
            events.append(
                {
                    "연도": Y,
                    "나이": age,
                    "세운간지": sew["간지"],
                    "태그": tags,
                    "한줄": (sew.get("출력_트리텍스트") or "").split("\n")[0],
                    "삼합재물참고": (san_lab if san_ok else "해당 연도에는 삼합 완성으로 읽히는 재물 신호가 두드러지지 않습니다."),
                }
            )

    return events


def ilwoon_year_day_counts(day_master: str, pillars: dict, year: int) -> Dict[str, int]:
    good = bad = neutral = 0
    for month in range(1, 13):
        _, last = calendar.monthrange(year, month)
        for dom in range(1, last + 1):
            r = il.analyze_ilwoon_day(day_master, pillars, year, month, dom)
            c = r["표시색"]
            if c == il.COLOR_GOOD:
                good += 1
            elif c == il.COLOR_BAD:
                bad += 1
            else:
                neutral += 1
    return {"길일수": good, "흉일수": bad, "보통일수": neutral}


def explain_past_year(
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    *,
    birth_year: int,
    daewoon_cycles: List[Dict[str, Any]],
    past_year: int,
    yong_block: Dict[str, Any],
    include_ilwoon_counts: bool = True,
) -> Dict[str, Any]:
    cy = _cycle_for_year(daewoon_cycles, past_year)
    sew = sw.analyze_sewoon_year(day_master, pillars, gender, past_year, counts=counts)
    wpack = ww.wolwoon_year_pack(day_master, pillars, past_year)

    _, dz = _split_ganzhi(cy.get("ganzhi") if cy else None)

    reasons = [
        f"{past_year}년 세운은 {sew.get('간지')}로 일간 대비 십신은 {sew.get('세운_천간_십신')}입니다.",
    ]
    if cy:
        reasons.append(
            f"해당 연도 대운 간지는 {cy.get('ganzhi')}({cy.get('start_age')}~{cy.get('end_age')}세 구간)입니다."
        )
        if dz and _dw_branch_clashes_native(dz, pillars):
            reasons.append("대운 지지가 원국 지지와 충을 이루어 바탕 공격이 컸을 수 있습니다.")
    ch_rows = sew.get("세운_지지_충") or []
    if ch_rows:
        reasons.append("세운 지지 충이 걸린 궁: " + ", ".join(r.get("위치", "") for r in ch_rows[:4]))

    peak_bad_months = [m["절월번호"] for m in wpack["월별"] if m.get("길흉판정") == "대흉우려"]
    if peak_bad_months:
        reasons.append(f"월운상 극히 거친 절월 번호: {','.join(map(str, peak_bad_months))}월.")

    dc = (
        ilwoon_year_day_counts(day_master, pillars, past_year)
        if include_ilwoon_counts
        else {"길일수": 0, "흉일수": 0, "보통일수": 0}
    )
    if include_ilwoon_counts:
        reasons.append(f"연중 일운 집계 — 길일·흉일·보통: {dc['길일수']}·{dc['흉일수']}·{dc['보통일수']}일.")

    narrative = (
        f"{past_year}년 당시 만 나이 약 {past_year - birth_year}세이며, "
        f"위 패턴이 겹치면 그 해 사건 해석의 참고축이 됩니다."
    )

    return {
        "연도": past_year,
        "대운구간": cy,
        "세운요약": {
            "간지": sew.get("간지"),
            "운세등급": sew.get("운세등급"),
            "사건예측": sew.get("사건예측"),
        },
        "월운표참조": {"특별주의": wpack.get("특별주의")},
        "일운연중집계": dc,
        "왜그런일이있었나_설명줄": reasons,
        "종합문장": narrative,
        "용신참고": yong_block.get("출력_문장", {}).get("용신"),
    }


def five_year_focus_pack(
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    *,
    start_year: int,
    ilwoon_detail_year: Optional[int] = None,
    include_ilwoon_counts: bool = True,
) -> Dict[str, Any]:
    rows = []
    for i in range(5):
        Y = start_year + i
        sew = sw.analyze_sewoon_year(day_master, pillars, gender, Y, counts=counts)
        risk = _risk_0_100(sew)
        bar_w = max(0, min(10, risk // 10))
        bad_slots = [
            m["절월번호"]
            for m in ww.wolwoon_year_pack(day_master, pillars, Y)["월별"]
            if m.get("길흉판정") == "대흉우려"
        ]
        dc = (
            ilwoon_year_day_counts(day_master, pillars, Y)
            if include_ilwoon_counts
            else {"길일수": 0, "흉일수": 0, "보통일수": 0}
        )

        detail_calendar = None
        if ilwoon_detail_year is not None and Y == ilwoon_detail_year:
            detail_calendar = il.ilwoon_month_pack(day_master, pillars, Y, 6)

        # 한줄요약: 세운 등급 + 핵심 충·해 신호 + 간지 표기
        sew_gz = sew.get("간지") or ""
        sew_grade = sew.get("운세등급") or ""
        sew_total_kr = sew.get("세운_총평_한줄") or ""
        # 총평이 있으면 앞 50자만, 없으면 기본 포맷
        if sew_total_kr and len(sew_total_kr) > 5:
            short_total = sew_total_kr[:70].rstrip(".,·") + "."
            line = f"{Y}년 {sew_gz} [{sew_grade}] — {short_total}"
        else:
            grade_emoji = {"대길운": "🟢", "길운": "🟢", "보통운": "🟡",
                           "흉운": "🔴", "대흉운": "🔴"}.get(sew_grade, "")
            line = f"{Y}년 {sew_gz} {grade_emoji}[{sew_grade}]"

        rows.append(
            {
                "연도": Y,
                "한줄요약": line,
                "위험도_0_100": risk,
                "위험도바_ASCII": "█" * bar_w + "░" * (10 - bar_w),
                "세운등급": sew.get("운세등급"),
                "월운_대흉우려_절월": bad_slots,
                "기회위기_일운연중": dc,
                "일운샘플달력_6월": (
                    {"달력_ASCII": detail_calendar["달력_ASCII"], "특별길일": detail_calendar["특별길일"]}
                    if detail_calendar
                    else {
                        "달력_ASCII": "(현재 기준 연도에만 6월 일진 샘플 달력을 붙입니다.)",
                        "특별길일": [],
                    }
                ),
            }
        )

    return {"시작연도": start_year, "연도별": rows}


def timeline_visualization_years(
    birth_year: int, current_year: int, *, span_past: int = 55, span_future: int = 35
) -> List[Dict[str, Any]]:
    out = []
    for y in range(current_year - span_past, current_year + span_future + 1):
        label, hex_c, css = _year_phase(y, current_year)
        out.append(
            {
                "연도": y,
                "나이": y - birth_year,
                "구간": label,
                "색상_HEX": hex_c,
                "테마키": css,
            }
        )
    return out


def build_timeline_pack(
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    *,
    birth_year: int,
    daewoon_cycles: List[Dict[str, Any]],
    yong_block: Dict[str, Any],
    current_year: Optional[int] = None,
    past_year: Optional[int] = None,
    triple_scan_years: int = 12,
    include_ilwoon_counts: bool = True,
    age_events_until_year: Optional[int] = None,
) -> Dict[str, Any]:
    cy = current_year if current_year is not None else datetime.now().year

    tb, tg = _scan_triple_periods(
        day_master,
        pillars,
        gender,
        counts,
        daewoon_cycles,
        yong_block,
        cy - triple_scan_years,
        cy + triple_scan_years,
    )

    age_ev = _scan_age_events(
        day_master,
        pillars,
        gender,
        counts,
        birth_year,
        birth_year + 14,
        (cy + 45) if age_events_until_year is None else age_events_until_year,
    )

    fy = five_year_focus_pack(
        day_master,
        pillars,
        gender,
        counts,
        start_year=cy,
        ilwoon_detail_year=cy,
        include_ilwoon_counts=include_ilwoon_counts,
    )

    past_block = None
    if past_year is not None:
        past_block = explain_past_year(
            day_master,
            pillars,
            gender,
            counts,
            birth_year=birth_year,
            daewoon_cycles=daewoon_cycles,
            past_year=past_year,
            yong_block=yong_block,
            include_ilwoon_counts=include_ilwoon_counts,
        )

    viz = timeline_visualization_years(birth_year, cy)

    summary_lines = [
        f"기준 연도 {cy}, 출생 {birth_year}년생 기준 타임라인입니다.",
        f"삼중 충 후보 {len(tb)}건 · 삼중 길 후보 {len(tg)}건 (±{triple_scan_years}년 월별 스캔).",
        "과거는 회색(#9ca3af), 현재는 골드(#d4af37), 미래는 파랑(#3b82f6) 테마입니다.",
    ]

    return {
        "현재연도": cy,
        "출생연도": birth_year,
        "색상범례": {"과거": _HEX_PAST, "현재": _HEX_NOW, "미래": _HEX_FUTURE},
        "삼중분석": {
            "극위험_삼중충": tb,
            "극기회_삼중길": tg,
            "설명": "동일 연도·절월에서 대운 지지 충·세운 지지 충·월운 충이 동시에 성립하면 극위험으로 표시합니다. "
            "대운 간지 오행이 용신과 맞고, 세운 간지 오행이 희신에 걸리며, 월운에 육합이 붙으면 극기회 후보입니다.",
        },
        "연령대_사건예측": age_ev,
        "과거역산": past_block
        if past_block is not None
        else {"요청여부": False, "설명": "과거 특정 연도를 지정하지 않아 역산 상세는 포함되지 않았습니다."},
        "향후5년": fy,
        "타임라인_시각화": {"연도별": viz},
        "출력_요약텍스트": "\n".join(summary_lines),
    }
