# -*- coding: utf-8 -*-
"""만세력 — 세운(총운)·월별 운세 요약 (일반인용)."""

from __future__ import annotations

import datetime
from typing import Any

from . import sewoon as sw
from . import wolwoon as ww

_PLAIN_GRADE = {
    "길운": "길한 편",
    "보통": "보통",
    "흉운": "조심",
    "길": "길한 편",
    "대길우려": "길한 편",
    "대흉우려": "조심",
    "약흉": "조심",
    "흉": "조심",
}

_GRADE_CLASS = {
    "길한 편": "good",
    "보통": "mid",
    "조심": "caution",
}


def _plain_grade(raw: str | None) -> str:
    if not raw:
        return "보통"
    return _PLAIN_GRADE.get(str(raw).strip(), "보통")


def _month_emoji(luck: str, icons: list | None) -> str:
    ic = "".join(icons or [])
    if "🔴" in ic:
        return "🔴"
    if "✅" in ic:
        return "💚"
    if luck in ("대흉우려", "약흉", "흉"):
        return "🔴"
    if luck in ("대길우려",):
        return "💚"
    return "⚪"


def build_manseryeok_fortune(
    day_master: str,
    pillars: dict,
    gender: str,
    counts: dict[str, int],
    yong_block: dict[str, Any],
    *,
    center_year: int | None = None,
) -> dict[str, Any]:
    """올해(또는 지정 연도) 세운·월운을 화면용으로 축약."""
    cy = center_year if center_year is not None else datetime.datetime.now().year

    se = sw.analyze_sewoon_year(
        day_master,
        pillars,
        gender,
        cy,
        counts=counts,
        yong=yong_block,
    )
    wo = ww.wolwoon_year_pack(
        day_master,
        pillars,
        cy,
        gender=gender,
        counts=counts,
        yong=yong_block,
    )

    domains = se.get("종합점수_영역별") or {}
    domain_rows = []
    for key in ("건강", "재물", "직업", "애정"):
        d = domains.get(key) or {}
        stars = int(d.get("별점") or 0)
        domain_rows.append(
            {
                "label": key,
                "stars": stars,
                "bar": d.get("문자") or ("★" * stars + "☆" * (5 - stars)),
            }
        )

    months_out = []
    for m in wo.get("월별") or []:
        luck = m.get("길흉판정") or "보통"
        plain = _plain_grade(m.get("길흉등급") or luck)
        months_out.append(
            {
                "slot": m.get("절월번호"),
                "ganzhi": m.get("월주간지") or "",
                "jieqi": m.get("절기명") or "",
                "grade": plain,
                "grade_class": _GRADE_CLASS.get(plain, "mid"),
                "emoji": _month_emoji(luck, m.get("특이아이콘")),
                "summary": (m.get("월별_핵심스토리") or m.get("한줄요약") or "")[:100],
                "action": (m.get("월별_행동지침_텍스트") or "")[:80],
            }
        )

    se_plain = _plain_grade(se.get("운세등급"))
    flow = wo.get("연간_월운_요약") or {}
    alerts = wo.get("특별주의") or {}

    return {
        "center_year": cy,
        "sewoon": {
            "year": cy,
            "pillar": se.get("간지") or "",
            "pillar_kr": se.get("표기한글") or "",
            "grade": se_plain,
            "grade_class": _GRADE_CLASS.get(se_plain, "mid"),
            "grade_raw": se.get("운세등급") or "",
            "stars": int(se.get("별점") or 0),
            "stars_bar": se.get("별점_문자") or "",
            "headline": se.get("세운_총평_한줄") or "",
            "closing": se.get("이해_총평_한마디") or "",
            "luck_keywords": se.get("행운_키워드") or [],
            "caution_keywords": se.get("주의_키워드") or [],
            "ipchun_note": se.get("입춘_안내") or "",
            "domains": domain_rows,
        },
        "monthly": {
            "months": months_out,
            "first_half": flow.get("상반기_총평") or "",
            "second_half": flow.get("하반기_총평") or "",
            "best_months": flow.get("최고의달_TOP3") or [],
            "caution_months": flow.get("최악의달_TOP3") or [],
            "alerts_good": alerts.get("✅기회") or [],
            "alerts_bad": alerts.get("🔴경고") or [],
            "alerts_kong": alerts.get("⚠️공망") or [],
            "slot_note": wo.get("절월_안내") or "",
        },
    }
