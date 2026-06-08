# -*- coding: utf-8
"""스프레드 스토리텔링 — 카드 간 관계·막(Act) 구조·합성 해석."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

CATEGORY_PHRASE: dict[str, str] = {
    "종합운": "삶 전반의 흐름",
    "연애운": "마음과 관계",
    "직업운": "일과 커리어",
    "금전운": "재물과 선택",
    "건강운": "몸과 마음의 균형",
    "대인관계": "사람 사이의 결",
    "이동운": "이동과 변화",
    "이직운": "새로운 자리",
    "이사운": "환경과 보금자리",
    "취업운": "시작과 도전",
    "자녀운": "성장과 돌봄",
    "오행맞춤운": "나에게 맞는 기운",
}

SPREAD_OPENING: dict[str, str] = {
    "week": "이번 주의 이야기는 세 장의 장면으로 펼쳐집니다. 시작의 기운이 중반을 거쳐 어디로 기울는지, 하나의 호흡으로 따라가 보세요.",
    "worry": "고민의 이야기는 ‘지금 — 막힘 — 풀림’ 세 단계로 읽을 때 가장 선명해집니다. 각 장면은 따로가 아니라 한 줄기의 흐름입니다.",
    "month": "한 달은 일곱 개의 장면으로 읽힙니다. 출발에서 이슈, 전환, 조언, 전망, 마무리까지 — 시간의 순서대로 이야기가 깊어집니다.",
    "year": "올해는 다섯 장의 장면으로 읽힙니다. 봄·여름·가을·겨울을 거쳐 총운으로 수렴하는, 계절의 흐름이 이어지는 한 해의 서사입니다.",
    "love": "연애의 이야기는 ‘나 — 상대 — 우리’에서 시작해 장애와 조언을 거쳐 앞으로의 방향으로 수렴합니다.",
    "deep": "심층 리딩은 열 장의 층위로 구성됩니다. 겉으로 드러난 상황부터 무의식, 환경, 최종 결론까지 — 아래로 갈수록 핵심에 닿습니다.",
}

ACT_PLAN: dict[str, list[dict[str, Any]]] = {
    "week": [
        {"title": "1막 · 시작", "range": (0, 1)},
        {"title": "2막 · 전개", "range": (1, 2)},
        {"title": "3막 · 마무리", "range": (2, 3)},
    ],
    "worry": [
        {"title": "1막 · 지금", "range": (0, 1)},
        {"title": "2막 · 막힘", "range": (1, 2)},
        {"title": "3막 · 풀림", "range": (2, 3)},
    ],
    "month": [
        {"title": "1막 · 출발", "range": (0, 2)},
        {"title": "2막 · 전환", "range": (2, 5)},
        {"title": "3막 · 마무리", "range": (5, 7)},
    ],
    "year": [
        {"title": "1막 · 상반", "range": (0, 2)},
        {"title": "2막 · 하반", "range": (2, 4)},
        {"title": "3막 · 총운", "range": (4, 5)},
    ],
    "love": [
        {"title": "1막 · 마음", "range": (0, 3)},
        {"title": "2막 · 시험", "range": (3, 5)},
        {"title": "3막 · 방향", "range": (5, 7)},
    ],
    "deep": [
        {"title": "1막 · 겉", "range": (0, 3)},
        {"title": "2막 · 속", "range": (3, 7)},
        {"title": "3막 · 결", "range": (7, 10)},
    ],
}

BRIDGE_TEMPLATES: list[str] = [
    "「{prev}」에서 만들어진 흐름은 다음 장면에서 이렇게 이어집니다.",
    "앞 장면 「{prev}」의 기운이 다음 자리에 닿으면서,",
    "「{prev}」까지의 이야기를 거쳐 이제",
    "지금까지의 흐름 — 특히 「{prev}」 — 을 바탕으로",
]

BRIDGE_REVERSAL: list[str] = [
    "「{prev}」에서 드러난 마찰을 넘어서면,",
    "앞 장면의 역방향 에너지를 조율한 뒤,",
    "잠시 속도를 늦춘 다음,",
]


def _first_sentence(text: str, max_len: int = 140) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?…])\s+", text)
    sentence = parts[0] if parts else text
    if len(sentence) > max_len:
        sentence = sentence[: max_len - 1].rstrip() + "…"
    return sentence


def _card_line(sec: dict[str, Any]) -> str:
    rev = f" ({sec['orient']})" if sec.get("is_reversed") else ""
    kw = sec.get("keyword") or ""
    kw_part = f" — {kw}" if kw else ""
    label = sec.get("position_label", "")
    role = sec.get("position_role", "")
    return f"「{sec['name']}」{rev}{kw_part} · {label}({role})"


def _reversed_overview(sections: list[dict[str, Any]]) -> str:
    rev = sum(1 for s in sections if s.get("is_reversed"))
    total = len(sections)
    if total <= 1:
        return ""
    if rev == 0:
        return "카드들이 정방향으로 비교적 고르게 놓여, 흐름이 한 방향으로 이어지기 쉬운 배열입니다."
    if rev == total:
        return "모든 카드가 역방향입니다. 지금은 밖으로 확장하기보다 속도를 늦추고, 이미 알고 있는 것을 다시 정리할 때입니다."
    if rev >= (total + 1) // 2:
        return f"역방향 {rev}장이 이야기의 중심에 있습니다. 겉으로 보이는 진행보다 조율·재정비·마음의 정리가 먼저일 수 있습니다."
    return f"역방향 {rev}장이 변수를 만들지만, 전체 서사를 뒤집을 만큼 압도적이지는 않습니다."


def _element_overview(sections: list[dict[str, Any]]) -> str:
    elems = [s.get("element") for s in sections if s.get("element")]
    if not elems:
        return ""
    top, count = Counter(elems).most_common(1)[0]
    if count == 1 and len(elems) > 2:
        return "오행 기운이 고르게 퍼져 있어, 한쪽으로 치우치지 않고 균형을 찾아가는 이야기입니다."
    names = {"木": "성장", "火": "열정", "土": "안정", "金": "결단", "水": "흐름"}
    tone = names.get(top, "기운")
    return f"{top}({tone}) 기운이 {count}번 등장해, 이 리딩의 중심 결을 이룹니다."


def _pick_bridge(prev: dict[str, Any], curr: dict[str, Any]) -> str:
    templates = BRIDGE_REVERSAL if prev.get("is_reversed") else BRIDGE_TEMPLATES
    idx = (hash(prev.get("name", "")) + hash(curr.get("name", ""))) % len(templates)
    return templates[idx].format(prev=prev.get("name", "앞 카드"))


def _compose_scene_paragraph(sec: dict[str, Any], *, lead: str = "") -> str:
    excerpt = sec.get("excerpt", "")
    summary = _first_sentence(excerpt)
    line = _card_line(sec)
    head = f"{lead}{line}."
    if summary:
        return f"{head} {summary}"
    return head


def _compose_act_paragraph(
    act_sections: list[dict[str, Any]],
    *,
    spread_key: str,
    act_title: str,
) -> str:
    if not act_sections:
        return ""
    if spread_key == "year" and len(act_sections) >= 2:
        names = " → ".join(s["name"] for s in act_sections)
        summaries = [_first_sentence(s.get("excerpt", ""), 90) for s in act_sections]
        body = " ".join(f"{s['position_label']}에는 「{s['name']}」." for s in act_sections)
        detail = " ".join(s for s in summaries if s)
        return f"{act_title}에는 {names}의 흐름이 이어집니다. {body} {detail}".strip()

    parts: list[str] = []
    for i, sec in enumerate(act_sections):
        if i == 0:
            lead = ""
        else:
            lead = _pick_bridge(act_sections[i - 1], sec) + " "
        parts.append(_compose_scene_paragraph(sec, lead=lead))
    return " ".join(parts)


def _compose_synthesis(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    if not sections:
        return ""
    first = sections[0]
    last = sections[-1]
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")
    rev_note = _reversed_overview(sections)
    elem_note = _element_overview(sections)

    if spread_key == "today":
        return sections[0].get("excerpt", "")

    if spread_key == "week":
        core = (
            f"이번 주 {cat_phrase}의 이야기는 「{first['name']}」로 문을 연 뒤 "
            f"「{last['name']}」 쪽으로 기울어집니다. "
            "초반의 선택이 중반의 리듬을 만들고, 그 리듬이 주말의 결을 정합니다."
        )
    elif spread_key == "worry":
        mid = sections[1]["name"] if len(sections) > 1 else ""
        core = (
            f"고민의 핵심은 「{first['name']}」에서 시작해 "
            f"「{mid}」에서 막히거나 흔들리고, "
            f"마침내 「{last['name']}」이 풀어갈 실마리를 보여 줍니다."
        )
    elif spread_key == "month":
        core = (
            f"이달 {cat_phrase}는 「{first['name']}」의 출발에서 "
            f"중순의 변수를 거쳐 「{last['name']}」로 정리됩니다. "
            "한 장면만 보지 말고, ‘초반 → 중반 → 후반’의 호흡으로 읽을 때 전체가 보입니다."
        )
    elif spread_key == "year":
        q1 = sections[0]["name"]
        q4 = sections[-1]["name"]
        core = (
            f"올해 {cat_phrase}는 「{q1}」의 봄부터 「{q4}」의 겨울까지 한 호흡입니다. "
            "상반기에 심어 둔 것이 하반기에 모양을 갖추거나, 중간에 조율이 필요한 달이 끼어 있을 수 있습니다."
        )
    elif spread_key == "love":
        core = (
            f"연애 {cat_phrase}에서 「{first['name']}」과 「{last['name']}」 사이에 "
            "나·상대·관계·장애·조언이 모두 한 줄기로 연결됩니다. "
            "한 사람의 카드만 단정하지 말고, ‘우리’의 이야기로 읽어 보세요."
        )
    elif spread_key == "deep":
        core = (
            f"심층 {cat_phrase} 리딩은 「{first['name']}」의 겉장면에서 출발해 "
            f"「{last['name']}」의 결론으로 수렴합니다. "
            "중간의 무의식·환경·희망과 두려움 카드가 ‘왜 그렇게 느껴지는지’를 설명해 줍니다."
        )
    else:
        core = (
            f"{cat_phrase}의 이야기는 「{first['name']}」에서 「{last['name']}」까지 "
            "끊기지 않고 이어집니다."
        )

    extras = " ".join(x for x in (rev_note, elem_note) if x)
    return f"{core} {extras}".strip()


def _compose_closing(
    spread_key: str,
    category: str,
    sections: list[dict[str, Any]],
) -> str:
    if not sections:
        return ""
    last = sections[-1]
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")

    advice: dict[str, str] = {
        "week": "이번 주는 하루 단위로 쪼개기보다, ‘초반에 심을 것 — 중반에 조율할 것 — 후반에 마무리할 것’으로 계획해 보세요.",
        "worry": "답은 한 장에 있지 않습니다. 막힘 카드가 가리키는 부분을 인정한 뒤, 조언·풀림 카드의 방향으로 작은 한 걸음을 옮기면 됩니다.",
        "month": "한 달 전체를 한 번에 바꾸려 하기보다, 초반·중순·후반에 맞는 속도로 나누어 실천해 보세요.",
        "year": "한 해 전체를 한 번에 잡으려 하지 마세요. 지금 계절에 맞는 장면만 충실히 살아도, 총운 카드가 가리키는 방향으로 자연스럽게 이어집니다.",
        "love": "상대를 바꾸기보다, ‘나의 마음 — 우리의 흐름 — 앞으로의 선택’ 순서로 대화와 행동을 맞춰 보세요.",
        "deep": "심층 리딩은 단번에 해결책을 주기보다, 겉과 속이 왜 다른지 알려 줍니다. 결론 카드는 ‘방향’이지 ‘판결’이 아닙니다.",
    }

    base = advice.get(
        spread_key,
        "각 장면은 따로가 아니라 하나의 이야기입니다. 앞뒤 흐름을 함께 두고 오늘의 선택을 정해 보세요.",
    )
    tail = f"마지막 장면 「{last['name']}」은 {cat_phrase}에서 지금 가장 신경 써야 할 결을 가리킵니다."
    return f"{base} {tail}"


def build_spread_story(
    spread_key: str,
    spread_label: str,
    category: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """스프레드 스토리텔링 본문·막·합성·마무리 생성."""
    cat_phrase = CATEGORY_PHRASE.get(category, "이번 주제")
    narrative_sections: list[dict[str, str]] = []

    if spread_key == "today":
        sec = sections[0]
        opening = f"오늘의 {cat_phrase} — 「{sec['name']}」이(가) 지금 이 순간의 메시지입니다."
        body = sec.get("excerpt", "")
        narrative_sections = [
            {"type": "opening", "title": "오늘의 메시지", "text": opening},
            {"type": "scene", "title": _card_line(sec), "text": body},
        ]
        return {
            "opening": opening,
            "narrative_sections": narrative_sections,
            "narrative": f"{opening}\n\n{body}",
            "synthesis": body,
            "closing": _first_sentence(sec.get("today_message") or body, 200)
            if sec.get("today_message")
            else _compose_closing(spread_key, category, sections),
        }

    opening_tpl = SPREAD_OPENING.get(
        spread_key,
        "카드를 뽑은 순서대로, 하나의 이야기로 읽어 갑니다.",
    )
    opening = f"「{spread_label}」 · {cat_phrase}\n{opening_tpl}"
    narrative_sections.append({"type": "opening", "title": "리딩 시작", "text": opening})

    act_plan = ACT_PLAN.get(spread_key)
    if act_plan:
        for act in act_plan:
            start, end = act["range"]
            chunk = sections[start:end]
            if not chunk:
                continue
            text = _compose_act_paragraph(
                chunk,
                spread_key=spread_key,
                act_title=act["title"],
            )
            narrative_sections.append(
                {"type": "act", "title": act["title"], "text": text}
            )
    else:
        for i, sec in enumerate(sections):
            lead = _pick_bridge(sections[i - 1], sec) + " " if i > 0 else ""
            text = _compose_scene_paragraph(sec, lead=lead)
            narrative_sections.append(
                {
                    "type": "scene",
                    "title": f"{sec['position_label']} · {sec['position_role']}",
                    "text": text,
                }
            )

    synthesis = _compose_synthesis(spread_key, category, sections)
    closing = _compose_closing(spread_key, category, sections)

    narrative_sections.append({"type": "synthesis", "title": "흐름 정리", "text": synthesis})
    narrative_sections.append({"type": "closing", "title": "마무리 조언", "text": closing})

    for sec in sections:
        sec["scene_summary"] = _first_sentence(sec.get("excerpt", ""), 100)

    full_parts = [opening]
    for block in narrative_sections[1:-2]:
        full_parts.append(f"【{block['title']}】\n{block['text']}")
    full_parts.append(f"【흐름 정리】\n{synthesis}")
    full_parts.append(f"【마무리 조언】\n{closing}")

    return {
        "opening": opening,
        "narrative_sections": narrative_sections,
        "narrative": "\n\n".join(full_parts),
        "synthesis": synthesis,
        "closing": closing,
    }
