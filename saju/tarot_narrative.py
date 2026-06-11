# -*- coding: utf-8
"""스프레드 스토리텔링 — 카드별 대화형 해설·시간축 합성."""

from __future__ import annotations

import re
from typing import Any

CATEGORY_PHRASE: dict[str, str] = {
    "종합운": "삶 전반",
    "연애운": "마음과 관계",
    "직업운": "일과 커리어",
    "금전운": "재물과 선택",
    "건강운": "몸과 마음",
    "대인관계": "사람 사이",
    "이동운": "이동과 변화",
    "이직운": "새로운 자리",
    "이사운": "환경과 보금자리",
    "취업운": "시작과 도전",
    "자녀운": "성장과 돌봄",
    "오행맞춤운": "나에게 맞는 기운",
}

SPREAD_OPENING: dict[str, str] = {
    "week": "이번 주는 세 장으로 읽습니다. 초반 → 한가운데 → 후반 순서대로 따라가 보세요.",
    "worry": "고민은 과거 → 현재 → 미래 세 장으로 읽습니다. 막힘이 없으면 순풍, 역방향이면 조율이 필요한 흐름으로 해석합니다.",
    "month": "이번 달은 다섯 장으로 읽습니다. 한 주·한 주의 흐름이 이어지는 달의 이야기입니다.",
    "year": "신년은 일곱 장으로 읽습니다. 두 달씩 흐름을 따라가 마지막 총운으로 한 해를 정리합니다.",
    "love": "연애는 일곱 장으로 읽습니다. 나와 상대, 우리의 흐름을 차례대로 짚어 봅니다.",
    "deep": "심층 리딩은 열 장의 층위로 구성됩니다.",
}

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

_POSITION_LEAD: dict[str, list[str]] = {
    "worry": [
        "그동안 회원님은",
        "지금 이 순간 회원님은",
        "앞으로 회원님께는",
    ],
    "week": [
        "이번 주 초반에는",
        "한 주의 한가운데에는",
        "이번 주 후반·마무리에는",
    ],
    "month": [
        "이번 달 1주에는",
        "2주에는",
        "3주에는",
        "4주에는",
        "이번 달 마무리에는",
    ],
    "year": [
        "1~2월에는",
        "3~4월에는",
        "5~6월에는",
        "7~8월에는",
        "9~10월에는",
        "11~12월에는",
        "한 해 전체를 관통하는 총운으로",
    ],
}

_LAST_CARD_PREFIX: dict[str, str] = {
    "worry": "마무리 카드로",
    "week": "이번 주를 정리하는 카드로",
    "month": "이달의 결을 짓는 카드로",
    "year": "신년 총운으로",
    "love": "앞으로의 방향을 가리키는 카드로",
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


def _tone_clause(sec: dict[str, Any]) -> str:
    if sec.get("is_reversed"):
        return "역방향으로 나와, 속도를 늦추고 조율·정리가 먼저일 수 있습니다. "
    return "정방향으로, 흐름이 받쳐 주는 쪽으로 읽힙니다. "


def _ordinal_intro(position: int) -> str:
    return _ORDINAL_INTRO.get(position, f"{position}번째는")


def _position_lead(spread_key: str, index: int, sec: dict[str, Any], total: int) -> str:
    if spread_key == "love":
        role = sec.get("position_role") or sec.get("position_label") or ""
        if role:
            return f"{role}의 자리에서는"
    leads = _POSITION_LEAD.get(spread_key)
    if leads and index < len(leads):
        return leads[index]
    label = sec.get("position_label") or str(index + 1)
    return f"{label} 자리에서는"


def compose_card_reading(
    sec: dict[str, Any],
    *,
    spread_key: str,
    category: str,
    index: int,
    total: int,
) -> str:
    """카드 1장 — 번호·덱·이름·키워드·자리·본문 대화형 해설."""
    pos = index + 1
    num = _card_num(sec)
    deck = _deck_type_label(sec)
    name = sec.get("name") or "카드"
    kw = _keyword_plain(sec.get("keyword") or "")
    intro = _ordinal_intro(pos)
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")

    head = f"{intro} {num}번 {deck}에서 「{name}」이(가) 나왔어요."
    if kw:
        head += f" 이 카드는 {kw}의 기운을 담고 있습니다."

    lead = _position_lead(spread_key, index, sec, total)
    tone = _tone_clause(sec)
    body = _reading_body(sec.get("excerpt") or "")

    if spread_key in ("love", "deep") and sec.get("position_role"):
        role = sec["position_role"]
        kw_part = f"키워드는 {kw}입니다. " if kw else ""
        narrative = (
            f"{intro} {num}번 {deck}에서 「{name}」이(가) 나왔어요. "
            f"{kw_part}{role}으로, {tone}{body}"
        )
    elif index == total - 1 and total > 1:
        prefix = _LAST_CARD_PREFIX.get(spread_key, "마무리로")
        narrative = f"{head} {prefix}, {lead} {tone}{body}"
    else:
        narrative = f"{head} {lead} {tone}{body}"

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
    tone = _tone_clause(sec)
    body = _reading_body(sec.get("excerpt") or sec.get("today_message") or "")
    return f"{head} {tone}{body}".strip()


def _compose_timeline_synthesis(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    if not sections:
        return ""
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")
    parts: list[str] = []

    for i, sec in enumerate(sections):
        name = sec.get("name") or ""
        kw = _keyword_plain(sec.get("keyword") or "")
        label = sec.get("position_label") or str(i + 1)
        rev = " (역방향)" if sec.get("is_reversed") else ""
        snippet = _first_sentence(sec.get("excerpt") or "", 100)

        if spread_key == "worry":
            time_word = ("과거", "현재", "미래")[i] if i < 3 else label
            parts.append(f"{time_word}에는 「{name}」{rev} — {snippet}")
        elif spread_key == "week":
            time_word = ("초반", "중반", "후반")[i] if i < 3 else label
            parts.append(f"{time_word} 「{name}」{rev} — {snippet}")
        elif spread_key == "year":
            parts.append(f"{label} 「{name}」{rev} — {snippet}")
        elif spread_key == "love":
            parts.append(f"{label} 「{name}」{rev} — {snippet}")
        else:
            parts.append(f"{label} 「{name}」{rev} — {snippet}")

    joined = " ".join(parts)
    return f"{cat_phrase} 흐름을 한 줄로 정리하면 — {joined}"


def _compose_closing(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    if not sections:
        return ""
    last = sections[-1]
    name = last.get("name") or "마지막 카드"
    kw = _keyword_plain(last.get("keyword") or "")
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")

    if last.get("is_reversed"):
        action = "서두르지 말고, 지금 필요한 정리부터 해보세요."
    else:
        action = "이 흐름을 믿고 한 걸음씩 옮겨 보세요."

    kw_part = f" {kw}의 기운을" if kw else ""
    return (
        f"마지막 「{name}」{kw_part} 기준으로, {cat_phrase}에서는 "
        f"{_first_sentence(last.get('excerpt') or '', 120)} {action}"
    ).strip()


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

    opening_tpl = SPREAD_OPENING.get(
        spread_key,
        "뽑은 순서대로, 한 장씩 이야기를 이어 갑니다.",
    )
    opening = f"「{spread_label}」 · {cat_phrase}\n{opening_tpl}"
    narrative_sections.append({"type": "opening", "title": "리딩 시작", "text": opening})

    for i, sec in enumerate(sections):
        text = compose_card_reading(
            sec,
            spread_key=spread_key,
            category=category,
            index=i,
            total=total,
        )
        sec["position_reading"] = text
        sec["scene_summary"] = _first_sentence(text, 100)
        label = sec.get("position_label") or str(i + 1)
        role = sec.get("position_role") or ""
        title = f"{i + 1}장 · {label}"
        if role:
            title = f"{i + 1}장 · {label} ({role})"
        narrative_sections.append({"type": "scene", "title": title, "text": text})

    synthesis = _compose_timeline_synthesis(spread_key, category, sections)
    closing = _compose_closing(spread_key, category, sections)

    summary_title = "세 장의 이야기" if total == 3 else "흐름 한눈에"
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
