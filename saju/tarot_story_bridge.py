# -*- coding: utf-8 -*-
"""스프레드 카드 간 전환·오행 연결·아크 합성 (카테고리·스프레드 공통)."""

from __future__ import annotations

import re
from typing import Any

from saju import tarot_category_story as tcs

_ELEMENT_SLUG: dict[str, str] = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
    "stems": "천간",
    "fate": "운명",
}

_ELEMENT_CHAR: dict[str, str] = {
    "木": "목",
    "火": "화",
    "土": "토",
    "金": "금",
    "水": "수",
    "運命": "운명",
}

_SHENG_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("목", "화"),
        ("화", "토"),
        ("토", "금"),
        ("금", "수"),
        ("수", "목"),
    }
)

_POSITION_BRIDGE: dict[str, dict[int, str]] = {
    "week": {
        1: "초반 「{prev}」의 흐름이 한가운데로 이어지며",
        2: "중반을 지나 이번 주 후반으로 넘어가면",
    },
    "worry": {
        1: "그렇게 쌓여 온 과거 「{prev}」의 이야기에서, 지금 이 순간이 열립니다.",
        2: "지금의 「{prev}」를 거쳐, 앞으로 펼쳐질 방향으로 시선을 옮겨 볼게요.",
    },
    "month": {
        1: "1주 「{prev}」 뒤 {cat} 관점에서 2주 차로 넘어가면",
        2: "2주 흐름이 3주의 중심으로 모이고",
        3: "한 달의 중심을 지나 4주에는 조율이 들어가며",
        4: "네 번의 장면을 거쳐 이번 달 마무리 「{curr}」로 향합니다.",
    },
    "year": {
        1: "한 해의 시작 「{prev}」 뒤 {cat} 흐름이 봄의 성장으로 이어지고",
        2: "봄의 기운이 여름의 확장으로 넘어가며",
        3: "여름의 열기가 한가운데 전환점으로 가라앉고",
        4: "전환을 지나 가을 수확의 장면이 열리며",
        5: "가을을 지나 겨울의 정리로 들어가고",
        6: "열두 달의 흐름을 모아 신년 총운 「{curr}」으로 향합니다.",
    },
    "love": {
        1: "나의 「{prev}」 뒤, 상대의 에너지가 「{curr}」에서 드러납니다.",
        2: "두 사람의 흐름이 「{curr}」에서 만납니다.",
        3: "관계의 리듬 속에서 변수가 「{curr}」로 나타나고",
        4: "흔들림을 지나 관계를 위한 조언이 「{curr}」에 담깁니다.",
        5: "조언을 거쳐 가까워질 가능성이 「{curr}」에서 보이고",
        6: "마지막으로 앞으로의 방향을 「{curr}」이 가리킵니다.",
    },
    "deep": {
        1: "현재 「{prev}」 아래 직면한 장애가 「{curr}」로 드러나고",
        2: "장애 뒤 무의식의 영향이 「{curr}」에서 떠오르며",
        3: "지나간 흐름이 「{curr}」로 이어지고",
        4: "목표가 「{curr}」에서 선명해지고",
        5: "가까운 미래가 「{curr}」로 다가오며",
        6: "나 자신의 층이 「{curr}」에서 드러나고",
        7: "주변 환경이 「{curr}」로 비춰지고",
        8: "희망과 두려움이 「{curr}」에 함께 놓이고",
        9: "열 번째 층위, 최종 결론이 「{curr}」로 모입니다.",
    },
}


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _keyword_plain(keyword: str) -> str:
    kw = (keyword or "").strip()
    if not kw:
        return ""
    return kw.replace(" · ", "과 ").replace("·", "과")


def _keywords_list(sec: dict[str, Any]) -> list[str]:
    raw = sec.get("keywords")
    if isinstance(raw, list) and raw:
        return [str(k).strip() for k in raw if str(k).strip()]
    return [p.strip() for p in re.split(r"\s*[·•]\s*", sec.get("keyword") or "") if p.strip()]


def _element_label(sec: dict[str, Any]) -> str:
    slug = (sec.get("category_slug") or "").strip()
    if slug in _ELEMENT_SLUG:
        return _ELEMENT_SLUG[slug]
    elem = (sec.get("element") or "").strip()
    return _ELEMENT_CHAR.get(elem, "오행")


def _element_bridge(prev_elem: str, curr_elem: str) -> str:
    if prev_elem == curr_elem:
        if prev_elem in ("천간", "운명"):
            return f"같은 {prev_elem}의 결을 이어 받아"
        return f"같은 {prev_elem} 기운이 이어지며"
    if (prev_elem, curr_elem) in _SHENG_PAIRS:
        return f"{prev_elem}에서 {curr_elem}으로 자연스럽게 넘어가며"
    if prev_elem in ("천간", "운명") or curr_elem in ("천간", "운명"):
        return f"{prev_elem}의 흐름 뒤 {curr_elem}이(가) 응답하듯"
    return f"{prev_elem}과 {curr_elem}이 맞부딪치며 흐름을 바꾸고"


def _orient_bridge(prev_rev: bool, curr_rev: bool) -> str:
    if not prev_rev and not curr_rev:
        return "순풍이 이어지는 장면에서"
    if not prev_rev and curr_rev:
        return "여기서 속도를 늦추고 조율할 신호가 보이고"
    if prev_rev and not curr_rev:
        return "막혀 있던 흐름이 다시 열리며"
    return "정리와 조율이 계속 필요한 장면으로"


def _keyword_link(prev: dict[str, Any], curr: dict[str, Any]) -> str:
    shared = [k for k in _keywords_list(prev) if k in set(_keywords_list(curr))]
    if shared:
        return f"「{' · '.join(shared[:2])}」의 결을 함께 짊어진"
    pk0 = _keywords_list(prev)[:1]
    ck0 = _keywords_list(curr)[:1]
    if pk0 and ck0:
        return f"「{pk0[0]}」에서 「{ck0[0]}」으로 주제가 넘어가며"
    return ""


def scene_essence(sec: dict[str, Any], *, category: str = "", max_len: int = 56) -> str:
    """카드 한 장 — 카테고리 본문 우선, 없으면 core."""
    excerpt = _collapse(sec.get("excerpt") or "")
    if excerpt:
        parts = re.split(r"(?<=[.!?…])\s+", excerpt)
        line = parts[0] if parts else excerpt
        if len(line) > 12:
            return line[:max_len]

    core = sec.get("core") or {}
    if isinstance(core, dict):
        line = core.get("shadow") if sec.get("is_reversed") else core.get("light")
        if line:
            return _collapse(line)[:max_len]

    name = sec.get("name") or "이 카드"
    cat = tcs.phrase(category) if category else "이 주제"
    return f"「{name}」이 {cat}에 전하는 메시지"


def first_card_lead(spread_key: str, category: str) -> str:
    return tcs.first_card_lead(spread_key, category)


def bridge_between_cards(
    prev: dict[str, Any],
    curr: dict[str, Any],
    *,
    spread_key: str,
    index: int,
    category: str = "종합운",
) -> str:
    """이전 카드 → 현재 카드 연결 (스프레드·카테고리 반영)."""
    prev_name = prev.get("name") or "앞 카드"
    curr_name = curr.get("name") or "이 카드"
    cat_phrase = tcs.phrase(category)
    cat_ctx = tcs.bridge_context(category)
    chunks: list[str] = []

    pos_tpl = (_POSITION_BRIDGE.get(spread_key) or {}).get(index)
    if pos_tpl:
        chunks.append(
            pos_tpl.format(prev=prev_name, curr=curr_name, cat=cat_phrase)
        )
    else:
        chunks.append(f"「{prev_name}」의 장면을 {cat_ctx}")

    kw_chunk = _keyword_link(prev, curr)
    if kw_chunk:
        chunks.append(kw_chunk)
    chunks.append(_element_bridge(_element_label(prev), _element_label(curr)))
    chunks.append(_orient_bridge(bool(prev.get("is_reversed")), bool(curr.get("is_reversed"))))
    return _collapse(" ".join(chunks))


def compose_arc_synthesis(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    """카드들을 한 편의 이야기로 엮은 합성 (카테고리별)."""
    if not sections:
        return ""

    cat_phrase = tcs.phrase(category)
    opener = tcs.synthesis_opener(spread_key, category)
    n = len(sections)
    names = [s.get("name") or f"{i + 1}번" for i, s in enumerate(sections)]

    if spread_key == "worry" and n >= 3:
        p, c, f = sections[0], sections[1], sections[2]
        return _collapse(
            f"{opener} "
            f"과거 「{p.get('name')}」에서는 {scene_essence(p, category=category)}. "
            f"그 흐름이 현재 「{c.get('name')}」과 맞닿아 {scene_essence(c, category=category)}. "
            f"앞으로 「{f.get('name')}」이 방향을 가리키며 {scene_essence(f, category=category)}."
        )

    if spread_key == "week" and n >= 3:
        a, b, c = sections[0], sections[1], sections[2]
        return _collapse(
            f"{opener} — "
            f"초반 「{a.get('name')}」({scene_essence(a, category=category)})에서 시작해 "
            f"중반 「{b.get('name')}」({scene_essence(b, category=category)})으로 전개되고 "
            f"후반 「{c.get('name')}」({scene_essence(c, category=category)})으로 마무리되는 흐름이에요."
        )

    if spread_key == "month" and n >= 5:
        essences = [scene_essence(s, category=category) for s in sections]
        return _collapse(
            f"{opener} — "
            f"1주 「{names[0]}」({essences[0]})로 출발해 "
            f"2주 「{names[1]}」·3주 「{names[2]}」를 거치고 "
            f"4주 「{names[3]}」에서 조율한 뒤, "
            f"마무리 「{names[4]}」({essences[4]})으로 달이 맺어져요."
        )

    if spread_key == "year" and n >= 7:
        return _collapse(
            f"{opener} — "
            f"「{names[0]}」({scene_essence(sections[0], category=category)})에서 한 해가 열리고 "
            f"「{names[2]}」·「{names[4]}」를 거쳐 수확과 정리가 이어지며, "
            f"총운 「{names[-1]}」({scene_essence(sections[-1], category=category)})으로 "
            f"한 해 전체가 {cat_phrase} 관점에서 한 줄로 잇혀요."
        )

    if spread_key == "love" and n >= 3:
        chunks = []
        for sec in sections:
            label = sec.get("position_label") or ""
            chunks.append(
                f"{label} 「{sec.get('name')}」({scene_essence(sec, category=category)})"
            )
        return _collapse(f"{opener}는 {' → '.join(chunks)} 순으로 이어집니다.")

    if spread_key == "deep" and n >= 5:
        head = " → ".join(
            f"「{sec.get('name')}」({scene_essence(sec, category=category)})"
            for sec in sections[:5]
        )
        tail = (
            f" → … → 결론 「{sections[-1].get('name')}」"
            f"({scene_essence(sections[-1], category=category)})"
        )
        return _collapse(f"{opener} — 표면에서 깊은 층으로 {head}{tail if n > 5 else ''}.")

    pieces = [
        f"「{sec.get('name')}」({scene_essence(sec, category=category)})"
        for sec in sections
    ]
    return _collapse(f"{opener} — {' → '.join(pieces)}")


def compose_arc_closing(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
    *,
    action: str,
) -> str:
    """아크를 관통하는 마무리 (카테고리·스프레드 반영)."""
    if not sections:
        return action

    cat_phrase = tcs.phrase(category)
    first = sections[0]
    last = sections[-1]
    fn = first.get("name") or "첫 카드"
    ln = last.get("name") or "마지막 카드"
    fk = _keyword_plain(first.get("keyword") or "")
    lk = _keyword_plain(last.get("keyword") or "")
    n = len(sections)

    spread_arc = {
        "worry": f"과거 「{fn}」에서 시작한 {cat_phrase} 이야기가 현재를 지나 「{ln}」으로 향한다는 점",
        "week": f"이번 주 {cat_phrase}는 「{fn}」에서 열려 「{ln}」으로 닫힌다는 점",
        "month": f"이번 달 {cat_phrase}는 1주 「{fn}」에서 출발해 마무리 「{ln}」으로 맺어진다는 점",
        "year": f"신년 {cat_phrase}는 「{fn}」으로 시작해 총운 「{ln}」으로 한 해를 정리한다는 점",
        "love": f"{cat_phrase}의 연애 흐름이 「{fn}」에서 「{ln}」으로 이어진다는 점",
        "deep": f"심층 {cat_phrase} 리딩이 「{fn}」에서 결론 「{ln}」까지 층층이 맞닿는다는 점",
    }

    if spread_key in spread_arc and n > 1:
        arc = spread_arc[spread_key]
    elif n > 1:
        arc = f"「{fn}」({fk})에서 「{ln}」({lk})으로 이어지는 {n}장의 {cat_phrase} 흐름"
    else:
        arc = f"「{ln}」({lk})의 {cat_phrase} 메시지"

    return _collapse(
        f"이 {n}장의 이야기를 관통하는 핵심은 {arc}이에요. "
        f"{cat_phrase}에서는 {scene_essence(last, category=category)}. {action}"
    )
