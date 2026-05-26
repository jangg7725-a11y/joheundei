# -*- coding: utf-8 -*-
"""만세력 매칭 결과 → 일반인용 쉬운 해석 문장."""

from __future__ import annotations

import re
from typing import Any

THEME_LABEL: dict[str, str] = {
    "혼인": "결혼·연애",
    "명리": "성격과 운의 흐름",
    "역법": "날짜·달력",
    "풍수": "집·이사·방위",
    "길흉": "좋은 날·피할 날",
    "제례": "제사·차례",
    "기타": "생활 참고",
}

SHINSIN_PLAIN: dict[str, str] = {
    "비견": "스스로 밀고 나가는 힘이 강합니다. 독립심·자존심이 두드러질 수 있어요.",
    "겁재": "경쟁·분배 이슈에 민감할 수 있습니다. 돈·인연에서 '나눔'을 의식하면 좋아요.",
    "식신": "먹을 복·표현·여유가 있습니다. 배움·창작·먹는 일에 기운이 붙기 쉬워요.",
    "상관": "말과 표현, 창의가 강합니다. 규칙보다 새 방식을 선호할 수 있어요.",
    "편재": "돈·일이 움직이는 변화가 많습니다. 기회를 잡는 감각이 있을 수 있어요.",
    "정재": "꾸준한 수입·안정적 재물에 관심이 갑니다. 계획적인 관리가 도움이 됩니다.",
    "편관": "도전·압박·결단이 따를 수 있습니다. 책임감이 크게 느껴질 때가 있어요.",
    "정관": "질서·명분·책임을 중시합니다. 직장·사회생활에서 신뢰를 쌓기 좋아요.",
    "편인": "직관·공부·예술 쪽 기운입니다. 혼자만의 시간이 회복에 도움이 됩니다.",
    "정인": "배움·보호·안정을 받는 기운입니다. 멘토·가족의 도움이 삶에 의미 있을 수 있어요.",
}

SINSAL_PLAIN: dict[str, str] = {
    "역마살": "이동·변화·해외·타지가 잦습니다. 이사·출장·여행운이 붙습니다.",
    "도화살": "인기·매력·이성 인연이 강합니다. 감정 기복·관계 선택에 주의해야 합니다.",
    "괴강살": "의지가 강하고 승부욕이 있습니다. 고집·충돌을 조절하면 추진력이 됩니다.",
    "공망": "헛수고·공허함이 드러납니다. 기대를 낮추고 하나에 집중하세요.",
    "겁살": "갑작스런 손실·경쟁을 조심합니다. 투자·보증·공동투자는 신중히 하세요.",
    "원진살": "가까운 사람과 마찰이 생깁니다. 말 한마디·오해를 줄이세요.",
    "고과살": "시비·구설·관재를 조심합니다. 계약·말실수에 유의하세요.",
    "태양도림": "큰 흉을 눌러주는 길한 기운입니다. 어려운 날에 도움이 됩니다.",
    "삼재": "3년 주기로 변화·시련이 옵니다. 무리한 확장은 피하세요.",
}

GYEOK_PLAIN: dict[str, str] = {
    "상관격": "표현·기술·자유로운 일이 잘 맞는 격으로 봅니다.",
    "식신격": "안정·여유·먹을 복·창작 쪽이 강한 격으로 봅니다.",
    "정관격": "직장·명예·규칙 있는 환경이 맞는 격으로 봅니다.",
    "편관격": "도전·경쟁·리더 역할이 맞는 격으로 봅니다.",
    "정재격": "꾸준한 재물·가정·실속을 챙기는 격으로 봅니다.",
    "편재격": "사업·변동 수입·기회 포착이 맞는 격으로 봅니다.",
    "정인격": "학문·자격·보호받는 구조가 맞는 격으로 봅니다.",
    "편인격": "예술·연구·독립적 일이 맞는 격으로 봅니다.",
}

OHAENG_PLAIN: dict[str, str] = {
    "목": "목(木) 기운을 살리면 — 초록·동쪽·성장·배움·봄이 도움이 됩니다.",
    "화": "화(火) 기운을 살리면 — 밝음·남쪽·표현·추진·여름이 도움이 됩니다.",
    "토": "토(土) 기운을 살리면 — 안정·중앙·부동산·신뢰가 도움이 됩니다.",
    "금": "금(金) 기운을 살리면 — 정리·서쪽·원칙·가을·결단이 도움이 됩니다.",
    "수": "수(水) 기운을 살리면 — 휴식·북쪽·지혜·겨울·유연함이 도움이 됩니다.",
}

EVENT_TIP: dict[str, str] = {
    "결혼": "결혼·가취 날짜는 만세력의 길일·생기복덕 같은 전통 기준을 함께 보면 도움이 됩니다.",
    "이사": "이사·입주는 방위·길일을 함께 보는 것이 전통 택일의 기본입니다.",
    "제사": "제사·차례는 절차와 시기를 지키는 것이 중요합니다.",
    "장례": "장례·묘 관련 일은 날짜와 방위를 특히 조심해서 고릅니다.",
    "개업": "개업·창업은 길일과 재물 기운을 함께 보는 편이 좋습니다.",
    "택일": "중요한 약속·계약은 '피할 날'을 먼저 걸러내고 길일을 고릅니다.",
    "납재": "재물·계약 관련 일은 서두르지 않고 날짜를 고르는 것이 유리합니다.",
}


def _clip(text: str, n: int = 140) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def _first_sentence(text: str) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return ""
    for sep in (". ", "。 ", "? ", "! ", ".\n"):
        if sep in t:
            return t.split(sep, 1)[0].strip() + ("." if sep.strip() == "." else "")
    return _clip(t, 120)


def explain_match_params(
    match_params: dict[str, str],
    profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """사주 조건을 일반인용 문장으로."""
    mp = match_params or {}
    rows: list[dict[str, str]] = []

    s = mp.get("shinsin") or ""
    if s:
        rows.append(
            {
                "key": "shinsin",
                "label": "성격·재능",
                "term": s,
                "plain": SHINSIN_PLAIN.get(s, f"월간 십신 '{s}'에 해당하는 기질로 읽힙니다."),
            }
        )

    sn = mp.get("sinsal") or ""
    if sn:
        plain = SINSAL_PLAIN.get(sn, "")
        if profile:
            for h in profile.get("sinsal_highlights") or []:
                if h.get("신살") == sn and h.get("해석"):
                    plain = _clip(h["해석"], 100) or plain
        rows.append(
            {
                "key": "sinsal",
                "label": "특별 기운(신살)",
                "term": sn,
                "plain": plain or f"'{sn}'은(는) 사주에서 특별히 짚어보는 기운입니다.",
            }
        )

    g = mp.get("gyeokguk") or ""
    if g:
        rows.append(
            {
                "key": "gyeok",
                "label": "전체 격국",
                "term": g.replace("격", "") + " 기운",
                "plain": GYEOK_PLAIN.get(g, f"전체 사주를 '{g}'으로 보는 관점입니다."),
            }
        )

    o = mp.get("ohaeng") or ""
    if o:
        rows.append(
            {
                "key": "ohaeng",
                "label": "도움이 되는 오행(용신)",
                "term": o,
                "plain": OHAENG_PLAIN.get(o, f"용신은 '{o}' 오행입니다."),
            }
        )

    ys = (profile or {}).get("yongsin") or {}
    if ys.get("판단_요약"):
        rows.append(
            {
                "key": "yongsin_sum",
                "label": "용신 한줄",
                "term": ys.get("용신_오행") or o,
                "plain": _clip(str(ys.get("판단_요약")), 120),
            }
        )

    return rows


def build_match_brief(
    profile: dict[str, Any],
    matched_total: int = 0,
) -> dict[str, Any]:
    """사주 매칭 탭 상단 요약."""
    mp = profile.get("match_params") or {}
    dm = profile.get("day_master_kr") or profile.get("day_master") or ""
    explains = explain_match_params(mp, profile)
    lead_parts = [e["plain"] for e in explains[:2] if e.get("plain")]
    lead = " ".join(lead_parts) if lead_parts else "아래에서 생활 주제별로 쉽게 풀어 드립니다."

    return {
        "headline": f"일간 {dm}님의 사주를 만세력 기준으로 풀어 보았습니다.",
        "lead": lead,
        "param_cards": explains,
        "matched_note": (
            f"사주와 맞는 생활 안내 {matched_total}가지를 쉬운 말로 정리했습니다."
            if matched_total
            else "사주 계산 후 안내가 표시됩니다."
        ),
    }


def _why_matched(item: dict[str, Any], match_params: dict[str, str]) -> str:
    mc = item.get("match_conditions") or {}
    mp = match_params or {}
    bits: list[str] = []
    if mp.get("shinsin") and mp["shinsin"] in (mc.get("십신") or []):
        bits.append(f"성격 기운({mp['shinsin']})")
    if mp.get("sinsal") and mp["sinsal"] in (mc.get("신살") or []):
        bits.append(f"신살({mp['sinsal']})")
    if mp.get("gyeokguk") and mp["gyeokguk"] in (mc.get("격국") or []):
        bits.append("격국")
    if mp.get("ohaeng") and mp["ohaeng"] in (mc.get("five_elements") or []):
        bits.append(f"용신 오행({mp['ohaeng']})")
    if not bits:
        return "사주 조건과 비슷한 주제의 만세력 설명입니다."
    return "당신 사주의 " + ", ".join(bits) + "과(와) 연결된 내용입니다."


def _insight_title(item: dict[str, Any]) -> str:
    pr = item.get("practical") or {}
    events = [e for e in (pr.get("applicable_events") or []) if e]
    theme = THEME_LABEL.get(item.get("category") or "", "생활")
    if events:
        ev = events[0]
        if ev in ("결혼", "이사", "제사", "장례", "개업", "택일"):
            return f"{ev} — 이런 일을 앞두고 보면 좋아요"
        return f"{ev}에 참고할 점"
    sub = (item.get("sub_category") or item.get("display_title") or "").strip()
    if sub and not re.search(r"[\u4e00-\u9fff]{3,}", sub):
        return sub
    return f"{theme} 안내"


def doc_to_insight(
    item: dict[str, Any],
    match_params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """문헌 1건 → 쉬운 해석 카드."""
    mp = match_params or {}
    pr = item.get("practical") or {}
    events = pr.get("applicable_events") or []
    theme = THEME_LABEL.get(item.get("category") or "", "생활 참고")

    raw_desc = (
        item.get("modern_interpretation")
        or item.get("korean_translation")
        or item.get("display_card_desc")
        or ""
    )
    summary = _first_sentence(raw_desc) or "전통 만세력에서 이 주제를 다루는 설명입니다."

    tip = ""
    for ev in events:
        if ev in EVENT_TIP:
            tip = EVENT_TIP[ev]
            break
    if not tip and events:
        tip = f"{events[0]}과(와) 관련해 만세력에서 길흉·시기를 참고할 수 있습니다."
    if not tip:
        tip = "자세한 고전 원문은 '원문 보기'에서 확인할 수 있습니다."

    return {
        "id": item.get("id"),
        "theme": theme,
        "category": item.get("category") or "",
        "title": _insight_title(item),
        "summary": summary,
        "why": _why_matched(item, mp),
        "tip": tip,
        "events": events[:4],
        "ref_label": (item.get("sub_category") or item.get("display_title") or "고전 참고")[:40],
        "score": item.get("_match_score", 0),
    }


def build_match_insights(
    docs: list[dict[str, Any]],
    match_params: dict[str, str] | None = None,
    *,
    max_items: int = 12,
) -> dict[str, Any]:
    """주제별 묶음 + 평탄 목록."""
    mp = match_params or {}
    items = [doc_to_insight(d, mp) for d in docs[:max_items]]

    groups_map: dict[str, list[dict[str, Any]]] = {}
    for ins in items:
        groups_map.setdefault(ins["theme"], []).append(ins)

    order = [
        "결혼·연애",
        "좋은 날·피할 날",
        "집·이사·방위",
        "성격과 운의 흐름",
        "날짜·달력",
        "제사·차례",
        "생활 참고",
    ]
    groups: list[dict[str, Any]] = []
    seen = set()
    for label in order:
        if label in groups_map:
            groups.append({"theme": label, "items": groups_map[label]})
            seen.add(label)
    for label, arr in groups_map.items():
        if label not in seen:
            groups.append({"theme": label, "items": arr})

    return {"items": items, "groups": groups, "total_shown": len(items)}
