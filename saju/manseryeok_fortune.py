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


def _avg_phase_score(months: list[dict[str, Any]], lo: int, hi: int) -> float:
    xs = [float(m["score"]) for m in months if lo <= int(m.get("slot") or 0) <= hi]
    return sum(xs) / len(xs) if xs else 3.0


def _score_to_plain_grade(score: float) -> str:
    if score >= 4.0:
        return "길한 편"
    if score >= 2.8:
        return "보통"
    return "조심"


def _pick_phase_months(months: list[dict[str, Any]], lo: int, hi: int) -> list[dict[str, Any]]:
    return [m for m in months if lo <= int(m.get("slot") or 0) <= hi]


def _phase_narrative(
    phase_months: list[dict[str, Any]],
    *,
    label: str,
    period: str,
) -> list[str]:
    if not phase_months:
        return [f"{label}({period})은 월운 데이터가 없어 보통 흐름으로 봅니다."]
    scores = [float(m["score"]) for m in phase_months]
    grade = _score_to_plain_grade(sum(scores) / len(scores))

    if grade == "길한 편":
        open_line = f"{label}({period})은 숨이 트이고 적극적으로 움직이기 좋은 흐름입니다."
    elif grade == "조심":
        open_line = f"{label}({period})은 변동·충돌 신호가 많아 속도 조절과 점검이 필요합니다."
    else:
        open_line = f"{label}({period})은 기회와 부담이 섞여, 무리한 확장보다 균형이 중요합니다."

    lines = [open_line]
    best = sorted(phase_months, key=lambda m: -float(m.get("score") or 0))[:2]
    worst = sorted(phase_months, key=lambda m: float(m.get("score") or 0))[:2]
    if best and best[0].get("summary"):
        b = best[0]
        lines.append(
            f"특히 {b['slot']}월({b.get('ganzhi', '')})은 {b['summary']}"
        )
    if worst and worst[0].get("slot") != (best[0].get("slot") if best else None):
        w = worst[0]
        if w.get("grade_class") == "caution" and w.get("summary"):
            lines.append(
                f"반면 {w['slot']}월은 조심 구간으로, {w['summary']}"
            )
    return lines


def _build_position_block(se: dict[str, Any], yong_block: dict[str, Any]) -> dict[str, Any]:
    """세운이 원국에 놓이는 방식·궁별 배당."""
    sip_g = se.get("세운_천간_십신") or ""
    sip_z = se.get("세운_지지_본기십신_근사") or ""
    yong = yong_block.get("용신_오행") or ""
    gi = yong_block.get("기신_오행") or ""

    intro = [
        f"{se.get('연도')}년 세운 {se.get('간지')}({se.get('표기한글', '')})은 "
        "당신 사주 원국 위에 「그 해 한 장의 운」으로 겹쳐 봅니다.",
        f"세운 천간 십신 「{sip_g}」은 올해 들어오는 하늘 기운이 일간과 맺는 관계이고, "
        f"지지 쪽은 「{sip_z}」 에너지가 땅(년·월·일·시)과 맞물립니다.",
    ]
    if yong:
        intro.append(
            f"용신은 {yong} · 기신은 {gi or '—'}입니다. "
            f"{(se.get('오행_변화_메모') or yong_block.get('판단_요약') or '')[:160]}"
        )

    impacts: list[str] = []
    for row in se.get("세운_지지_충") or []:
        impacts.append(
            f"【{row.get('위치', '')}】 {row.get('글자', '')} 충 — "
            f"{row.get('해석', row.get('육친궁', ''))}"
        )
    for row in (se.get("세운_지지_파") or [])[:2]:
        impacts.append(f"【{row.get('위치', '')}】 파(破) — 관계·계약 틈새 주의")
    for row in (se.get("세운_지지_해") or [])[:2]:
        impacts.append(f"【{row.get('위치', '')}】 해(害) — 은근한 마찰·오해")
    for row in (se.get("세운_지지_육합") or [])[:2]:
        impacts.append(f"【{row.get('위치', '')}】 육합 — {row.get('해석', '인연·협력 보완')}")
    for line in se.get("복음") or []:
        impacts.append(f"복음: {line}")
    if se.get("반음_전지충"):
        impacts.append("반음(全冲): 세운 지지가 원국 네 지지와 모두 충 — 해 전체가 바뀌는 느낌의 해")
    elif se.get("반음_과격"):
        impacts.append("반음형: 여러 궁이 동시에 흔들려 일정·건강·관계가 겹칠 수 있음")

    stem_bits: list[str] = []
    for h in se.get("세운_천간합") or []:
        if isinstance(h, dict):
            stem_bits.append(h.get("해석") or h.get("표기") or str(h))
        else:
            stem_bits.append(str(h))
    if stem_bits:
        impacts.append("천간합: " + " / ".join(stem_bits[:2]))

    assignments: list[dict[str, str]] = []
    yuk = se.get("육친별_상세") or {}
    for key, title in (
        ("배우자", "배우자·일지(配偶)"),
        ("부모", "부모·환경(年)"),
        ("자녀", "자녀·말년(時)"),
        ("직장_사회", "직장·사회(月)"),
    ):
        block = yuk.get(key) or {}
        if not block:
            continue
        status_key = next((k for k in block if k.endswith("_상태")), "")
        role_key = next((k for k in block if "작용" in k), "")
        assignments.append(
            {
                "title": title,
                "status": block.get(status_key, ""),
                "role": block.get(role_key, ""),
                "prediction": block.get("예측", ""),
            }
        )

    return {
        "intro": intro,
        "impacts": impacts[:8],
        "assignments": assignments,
    }


def _build_story_arc(se: dict[str, Any], wo_flow: dict[str, Any]) -> list[str]:
    """연간 스토리 서두·마무리."""
    lines: list[str] = []
    if se.get("세운_총평_한줄"):
        lines.append(str(se["세운_총평_한줄"]))
    wealth = (se.get("재물운_상세") or {}).get("서술") or ""
    career = (se.get("직업운_상세") or {}).get("서술") or ""
    love = (se.get("애정운_상세") or {}).get("서술") or ""
    health = (se.get("건강_상세") or {}).get("권장_검진") or ""
    if wealth:
        lines.append(f"【재물】 {wealth[:200]}")
    if career:
        lines.append(f"【직업】 {career[:200]}")
    if love:
        lines.append(f"【애정】 {love[:200]}")
    if health and isinstance(health, str):
        lines.append(f"【건강】 {health[:120]}")
    if wo_flow.get("상반기_총평"):
        lines.append(wo_flow["상반기_총평"])
    if wo_flow.get("하반기_총평"):
        lines.append(wo_flow["하반기_총평"])
    if se.get("이해_총평_한마디"):
        lines.append(str(se["이해_총평_한마디"]))
    return lines


def _build_phases(months_out: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (1, 4, "초반", "1~4절월 · 입춘~곡우"),
        (5, 8, "중반", "5~8절월 · 입하~처서"),
        (9, 12, "후반", "9~12절월 · 입추~대한"),
    ]
    out = []
    for lo, hi, label, period in specs:
        pm = _pick_phase_months(months_out, lo, hi)
        scores = [float(m["score"]) for m in pm]
        avg = sum(scores) / len(scores) if scores else 3.0
        plain = _score_to_plain_grade(avg)
        out.append(
            {
                "id": label,
                "label": label,
                "period": period,
                "grade": plain,
                "grade_class": _GRADE_CLASS.get(plain, "mid"),
                "paragraphs": _phase_narrative(pm, label=label, period=period),
                "highlight_months": [
                    f"{m['slot']}월 {m.get('ganzhi', '')}"
                    for m in sorted(pm, key=lambda x: -float(x.get("score") or 0))[:2]
                ],
            }
        )
    return out


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
                "score": float(m.get("길흉점수") or 3),
                "emoji": _month_emoji(luck, m.get("특이아이콘")),
                "summary": (m.get("월별_핵심스토리") or m.get("한줄요약") or "")[:160],
                "action": (m.get("월별_행동지침_텍스트") or "")[:80],
            }
        )

    se_plain = _plain_grade(se.get("운세등급"))
    flow = wo.get("연간_월운_요약") or {}
    alerts = wo.get("특별주의") or {}
    position = _build_position_block(se, yong_block)
    story_paragraphs = _build_story_arc(se, flow)
    phases = _build_phases(months_out)
    event_notes = list(se.get("사건예측_설명") or [])[:6]

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
            "story": story_paragraphs,
            "position": position,
            "phases": phases,
            "event_notes": event_notes,
            "sip_gan": se.get("세운_천간_십신") or "",
            "sip_zhi": se.get("세운_지지_본기십신_근사") or "",
            "nayin": se.get("낭음") or "",
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
