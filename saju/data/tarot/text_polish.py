# -*- coding: utf-8 -*-
"""타로 카드 본문 — 딱딱한 꼬리·명령조를 대화형 톤으로 다듬기."""

from __future__ import annotations

import re

READING_CATEGORIES = [
    "종합운",
    "연애운",
    "직업운",
    "금전운",
    "건강운",
    "대인관계",
    "이동운",
    "이직운",
    "이사운",
    "취업운",
    "자녀운",
    "오행맞춤운",
]

_STIFF_TAIL = re.compile(
    r"(~?시기입니다|하십시오|권합니다|필요합니다)\s*\.?\s*$"
)

_PHRASE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("~시기입니다", ""),
    ("시기입니다.", "흐름으로 읽혀요."),
    ("시기입니다", "흐름으로 읽혀요"),
    ("좋은 시기입니다", "좋은 흐름이에요"),
    ("중요한 시기입니다", "중요한 국면이에요"),
    ("최적의 시기입니다", "맞는 타이밍에 가까워요"),
    ("적절한 시기입니다", "맞는 타이밍이에요"),
    ("있으십니다", "있습니다"),
    ("되십니다", "됩니다"),
    ("하십시오", "해 보세요"),
    ("권합니다", "도움이 됩니다"),
    ("필요합니다.", "필요해 보여요."),
    ("필요합니다", "필요해 보여요"),
    ("당신에게는", "나에게는"),
    ("당신에게", "나에게"),
    ("당신의", "나의"),
    ("당신은", "나는"),
    ("당신 안에", "안에"),
    ("당신안에", "안에"),
)

_CATEGORY_NUDGE: dict[str, tuple[str, str]] = {
    "연애운": ("마음", "상대와의 거리"),
    "직업운": ("일", "커리어"),
    "금전운": ("돈", "재정"),
    "건강운": ("몸", "컨디션"),
    "대인관계": ("사람", "관계"),
    "이동운": ("이동", "여정"),
    "이직운": ("직장", "이직"),
    "이사운": ("집", "환경"),
    "취업운": ("취업", "지원"),
    "자녀운": ("아이", "자녀"),
    "오행맞춤운": ("기운", "오행"),
}


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def soften_tail(text: str) -> str:
    t = _collapse_ws(text)
    for old, new in _PHRASE_REPLACEMENTS:
        t = t.replace(old, new)
    if _STIFF_TAIL.search(t) and "흐름으로" not in t:
        t = _STIFF_TAIL.sub("흐름으로 읽혀요.", t)
    return t.strip()


def first_clause(text: str, *, max_len: int = 72) -> str:
    t = soften_tail(text)
    if not t:
        return ""
    parts = re.split(r"(?<=[.!?…])\s+", t)
    clause = parts[0] if parts else t
    clause = clause.rstrip(".")
    if len(clause) > max_len:
        clause = clause[: max_len - 1].rstrip() + "…"
    return clause


def polish_today_message(text: str) -> str:
    t = soften_tail(text)
    t = t.replace("시간입니다.", "흐름이에요.")
    t = t.replace("시간입니다", "흐름이에요")
    return t


def polish_meaning(
    text: str,
    *,
    category: str,
    card_name: str,
    is_reversed: bool,
) -> str:
    """카테고리 본문 — 2문장 구조·부드러운 말투로 정리."""
    t = soften_tail(text)
    if not t:
        return t

    parts = re.split(r"(?<=[.!?…])\s+", t)
    parts = [p.strip() for p in parts if p.strip()]

    # 역방향: 명령조를 제안형으로
    if is_reversed:
        parts = [
            p.replace("하지 마세요", "하지 않는 편이 좋아요")
            .replace("마세요.", "지 않는 편이 좋아요.")
            .replace("하세요.", "해 보세요.")
            for p in parts
        ]

    # 카테고리 키워드가 전혀 없으면 첫 문장에 살짝 보강
    nudge = _CATEGORY_NUDGE.get(category)
    if nudge and parts and not any(k in parts[0] for k in nudge):
        anchor = nudge[1] if is_reversed else nudge[0]
        parts[0] = f"{anchor} 쪽으로 보면 {parts[0]}"

    # 한 문장뿐이면 카드 이름으로 마무리 한 줄 추가
    if len(parts) == 1 and card_name and card_name not in parts[0]:
        tail = (
            f"「{card_name}」의 막힌 면을 조율하면 흐름이 다시 살아날 수 있어요."
            if is_reversed
            else f"「{card_name}」이 말하는 방향을 한 걸음만 옮겨 보세요."
        )
        parts.append(tail)

    out = " ".join(parts[:2])
    return soften_tail(out)


def parse_keywords(keyword: str) -> list[str]:
    raw = (keyword or "").replace("·", "·").strip()
    if not raw:
        return []
    parts = re.split(r"\s*[·•]\s*", raw)
    return [p.strip() for p in parts if p.strip()]
