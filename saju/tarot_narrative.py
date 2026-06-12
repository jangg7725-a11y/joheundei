# -*- coding: utf-8
"""스프레드 스토리텔링 — 카드별 대화형 해설·시간축 합성."""

from __future__ import annotations

import re
from typing import Any

from saju import tarot_category_story as tcs
from saju import tarot_reading as trd
from saju import tarot_story_bridge as tsb

CATEGORY_PHRASE = tcs.CATEGORY_PHRASE

_CATEGORY_SLUG_LABEL: dict[str, str] = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
    "stems": "천간",
    "fate": "운명",
}

_ORDINAL_INTRO: dict[int, str] = {
    1: "1번 카드는",
    2: "2번째는",
    3: "3번째는",
}

_LAST_CARD_PREFIX: dict[str, str] = {
    "worry": "마무리 카드로",
    "week": "이번 주를 정리하는 카드로",
    "month": "이달의 결을 짓는 카드로",
    "year": "신년 총운으로",
    "love": "앞으로의 방향을 가리키는 카드로",
    "deep": "심층 리딩의 결론으로",
}


def _first_sentence(text: str, max_len: int = 200) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?…])\s+", text)
    sentence = parts[0] if parts else text
    if len(sentence) > max_len:
        sentence = sentence[: max_len - 1].rstrip() + "…"
    return sentence


def _reading_body(text: str, max_len: int = 280) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for sep in (". ", "! ", "? ", "。"):
        pos = cut.rfind(sep)
        if pos > max_len * 0.5:
            return cut[: pos + 1].strip()
    return cut.rstrip() + "…"


def _card_num(sec: dict[str, Any]) -> str:
    raw = sec.get("card_id", sec.get("position", ""))
    try:
        return str(int(raw))
    except (TypeError, ValueError):
        return str(raw)


def _deck_type_label(sec: dict[str, Any]) -> str:
    slug = (sec.get("category_slug") or "").strip()
    short = _CATEGORY_SLUG_LABEL.get(slug, "")
    if short:
        return f"{short}카드"
    kr = sec.get("category_kr") or ""
    if "천간" in kr:
        return "천간카드"
    if "운명" in kr:
        return "운명카드"
    return "오행카드"


def _keyword_plain(keyword: str) -> str:
    kw = (keyword or "").strip()
    if not kw:
        return ""
    return kw.replace(" · ", "과 ").replace("·", "과")


def _ordinal_intro(position: int) -> str:
    return _ORDINAL_INTRO.get(position, f"{position}번째는")


def compose_card_reading(
    sec: dict[str, Any],
    *,
    spread_key: str,
    category: str,
    index: int,
    total: int,
    prev_sec: dict[str, Any] | None = None,
) -> str:
    """카드 1장 — 전환·덱·이름·키워드·자리·본문 대화형 해설."""
    pos = index + 1
    num = _card_num(sec)
    deck = _deck_type_label(sec)
    name = sec.get("name") or "카드"
    kw = _keyword_plain(sec.get("keyword") or "")
    role = sec.get("position_role") or ""
    is_rev = bool(sec.get("is_reversed"))
    label = sec.get("position_label") or ""

    if index == 0:
        lead = tsb.first_card_lead(spread_key, category) if total > 1 else ""
        intro = _ordinal_intro(pos)
        head = f"{lead} {intro} {num}번 {deck}에서 「{name}」이(가) 나왔어요.".strip()
        if kw:
            head += f" 이 카드는 {kw}의 기운을 담고 있어요."
    else:
        bridge = tsb.bridge_between_cards(
            prev_sec or {},
            sec,
            spread_key=spread_key,
            index=index,
            category=category,
        )
        head = f"{bridge} {num}번 {deck} 「{name}」이(가) 이어집니다."
        if kw and kw not in bridge:
            head += f" ({kw})"

    body = trd.build_position_body(
        sec.get("excerpt") or "",
        category=category,
        spread_key=spread_key,
        index=index,
        is_reversed=is_rev,
        position_role=role,
        excerpt_kind=sec.get("excerpt_kind") or "category",
    )
    body = _reading_body(body, max_len=360)

    if index == total - 1 and total > 1:
        prefix = _LAST_CARD_PREFIX.get(spread_key, "마무리로")
        narrative = f"{head} {prefix} {body}"
    elif label:
        narrative = f"{head} ({label}) {body}"
    else:
        narrative = f"{head} {body}"

    return re.sub(r"\s+", " ", narrative).strip()


def compose_today_reading(sec: dict[str, Any], category: str) -> str:
    num = _card_num(sec)
    deck = _deck_type_label(sec)
    name = sec.get("name") or "카드"
    kw = _keyword_plain(sec.get("keyword") or "")
    cat_phrase = CATEGORY_PHRASE.get(category, "오늘")
    head = f"오늘의 {cat_phrase} — {num}번 {deck} 「{name}」이(가) 지금 이 순간의 메시지예요."
    if kw:
        head += f" {kw}의 기운입니다."
    body = trd.build_position_body(
        sec.get("excerpt") or sec.get("today_message") or "",
        category=category,
        spread_key="today",
        index=0,
        is_reversed=bool(sec.get("is_reversed")),
        position_role="오늘",
    )
    return f"{head} {body}".strip()


def _compose_timeline_synthesis(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    return tsb.compose_arc_synthesis(spread_key, category, sections)


def _compose_closing(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    if not sections:
        return ""
    last = sections[-1]
    action = trd.closing_hint(category, is_reversed=bool(last.get("is_reversed")))
    return tsb.compose_arc_closing(
        spread_key,
        category,
        sections,
        action=action,
    )


def build_spread_story(
    spread_key: str,
    spread_label: str,
    category: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """스프레드 — 카드별 해설 + 세 장의 이야기 + 오늘의 한 걸음."""
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")
    narrative_sections: list[dict[str, str]] = []
    total = len(sections)

    if spread_key == "today":
        sec = sections[0]
        body = compose_today_reading(sec, category)
        narrative_sections = [
            {"type": "opening", "title": "오늘의 메시지", "text": body},
        ]
        return {
            "opening": body,
            "narrative_sections": narrative_sections,
            "narrative": body,
            "synthesis": _first_sentence(sec.get("excerpt") or "", 200),
            "closing": _first_sentence(sec.get("today_message") or body, 200),
        }

    opening_tpl = tcs.spread_opening(spread_key, category)
    opening = f"「{spread_label}」 · {cat_phrase}\n{opening_tpl}"
    narrative_sections.append({"type": "opening", "title": "리딩 시작", "text": opening})

    for i, sec in enumerate(sections):
        prev = sections[i - 1] if i > 0 else None
        text = compose_card_reading(
            sec,
            spread_key=spread_key,
            category=category,
            index=i,
            total=total,
            prev_sec=prev,
        )
        sec["position_reading"] = text
        sec["scene_summary"] = tsb.scene_essence(sec, category=category, max_len=100)
        if i > 0 and prev is not None:
            sec["transition_from_prev"] = tsb.bridge_between_cards(
                prev,
                sec,
                spread_key=spread_key,
                index=i,
                category=category,
            )
        label = sec.get("position_label") or str(i + 1)
        role = sec.get("position_role") or ""
        title = f"{i + 1}장 · {label}"
        if role:
            title = f"{i + 1}장 · {label} ({role})"
        narrative_sections.append({"type": "scene", "title": title, "text": text})

    synthesis = _compose_timeline_synthesis(spread_key, category, sections)
    closing = _compose_closing(spread_key, category, sections)

    _summary_titles = {
        3: "세 장의 이야기",
        5: "다섯 장의 이야기",
        7: "일곱 장의 이야기",
        10: "열 장의 이야기",
    }
    summary_title = _summary_titles.get(total, "흐름 한눈에")
    narrative_sections.append({"type": "synthesis", "title": summary_title, "text": synthesis})
    narrative_sections.append({"type": "closing", "title": "오늘의 한 걸음", "text": closing})

    full_parts = [opening]
    for block in narrative_sections[1:-2]:
        full_parts.append(f"【{block['title']}】\n{block['text']}")
    full_parts.append(f"【{summary_title}】\n{synthesis}")
    full_parts.append(f"【오늘의 한 걸음】\n{closing}")

    return {
        "opening": opening,
        "narrative_sections": narrative_sections,
        "narrative": "\n\n".join(full_parts),
        "synthesis": synthesis,
        "closing": closing,
    }
