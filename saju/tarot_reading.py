# -*- coding: utf-8
"""오행 타로 — 자리·카테고리 렌즈와 본문 다듬기."""

from __future__ import annotations

import re
from typing import Any

# 카테고리별 한 줄 관점 (탭마다 체감 차이)
CATEGORY_HOOK: dict[str, str] = {
    "종합운": "삶 전반을 보면",
    "연애운": "마음과 관계를 보면",
    "직업운": "일과 커리어를 보면",
    "금전운": "돈과 선택을 보면",
    "건강운": "몸과 마음을 보면",
    "대인관계": "사람 사이를 보면",
    "이동운": "이동과 변화를 보면",
    "이직운": "새로운 자리를 보면",
    "이사운": "살아갈 환경을 보면",
    "취업운": "시작과 도전을 보면",
    "자녀운": "성장과 돌봄을 보면",
    "오행맞춤운": "나에게 맞는 기운을 보면",
}

# 스프레드 × 자리 × (정방향/역방향) 짧은 렌즈
_TEMPORAL: dict[str, list[tuple[str, str]]] = {
    "worry": [
        (
            "그동안 쌓여 온 흐름 속에서",
            "그동안 맺혀 있던 패턴을 돌아보면",
        ),
        (
            "지금 이 순간 핵심은",
            "지금은 속도를 늦추고 조율이 먼저일 수 있어요.",
        ),
        (
            "앞으로 펼쳐질 방향으로는",
            "앞으로는 정리한 뒤 다시 열릴 여지가 있어요.",
        ),
    ],
    "week": [
        ("이번 주 초반에는", "초반에는 무리하지 않는 편이 좋아요."),
        ("한 주의 한가운데에는", "중반에는 흐름 점검이 중요해요."),
        ("이번 주 후반에는", "후반에는 마무리와 정리에 초점을 두면 좋아요."),
    ],
    "month": [
        ("이번 달 1주에는", "1주에는 출발을 가볍게 잡아보세요."),
        ("2주에는", "2주에는 리듬을 맞추는 데 신경 쓰면 좋아요."),
        ("3주에는", "3주에는 한 달의 중심이 드러나요."),
        ("4주에는", "4주에는 변화에 유연하게 대응해 보세요."),
        ("이번 달 마무리에는", "마무리에는 지금까지의 흐름을 정리해 보세요."),
    ],
    "year": [
        ("1~2월 흐름으로는", "한 해 시작은 기초를 다지는 쪽으로 읽혀요."),
        ("3~4월에는", "봄에는 성장과 연결이 붙는 때예요."),
        ("5~6월에는", "여름에는 확장과 실행이 강해질 수 있어요."),
        ("7~8월에는", "한가운데에는 전환·조율이 들어갈 수 있어요."),
        ("9~10월에는", "가을에는 수확과 정리의 기운이 올라와요."),
        ("11~12월에는", "겨울에는 내면과 마무리가 중요해요."),
        ("신년 총운으로는", "한 해 전체를 관통하는 메시지로는"),
    ],
}

_GENERIC_TAIL_RE = re.compile(
    r"(시기입니다|하세요|하십시오|권합니다|필요합니다)\s*\.?\s*$"
)
_STIFF_PHRASES: tuple[tuple[str, str], ...] = (
    ("~시기입니다", ""),
    ("시기입니다.", "흐름으로 읽혀요."),
    ("시기입니다", "흐름으로 읽혀요"),
    ("있으십니다", "있습니다"),
    ("되십니다", "됩니다"),
)

_CLOSING_HINT: dict[str, str] = {
    "종합운": "오늘은 한 가지만 차분히 실행해 보세요.",
    "연애운": "마음을 표현하는 작은 한 걸음이 도움이 돼요.",
    "직업운": "일의 우선순위를 한 줄로 정해 보세요.",
    "금전운": "지출과 저축의 균형을 한번 점검해 보세요.",
    "건강운": "몸이 보내는 신호에 귀 기울여 보세요.",
    "대인관계": "먼저 연락하거나 감사를 전해 보세요.",
    "이동운": "무리한 이동보다 계획을 다듬는 쪽이 좋아요.",
    "이직운": "이력·연락 중 하나만이라도 오늘 움직여 보세요.",
    "이사운": "환경 조건을 적어 보고 비교해 보세요.",
    "취업운": "지원·준비 중 막힌 한 가지부터 풀어 보세요.",
    "자녀운": "아이와 대화 한 번, 시간 한 조각을 내어 보세요.",
    "오행맞춤운": "오늘 맞는 색·방향을 의식해 보세요.",
}


def category_hook(category: str) -> str:
    return CATEGORY_HOOK.get(category, "이 주제를 보면")


def temporal_lens(spread_key: str, index: int, *, is_reversed: bool) -> str:
    rows = _TEMPORAL.get(spread_key)
    if not rows or index >= len(rows):
        return ""
    upright, reversed_lens = rows[index]
    return reversed_lens if is_reversed else upright


def soften_body(text: str) -> str:
    """DB 템플릿 꼬리(시기입니다 등)를 읽기 쉬운 말투로."""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", str(text).strip())
    for old, new in _STIFF_PHRASES:
        t = t.replace(old, new)
    if _GENERIC_TAIL_RE.search(t) and "흐름으로" not in t:
        t = _GENERIC_TAIL_RE.sub("흐름으로 읽혀요.", t)
    return t.strip()


def split_meaning_lines(text: str) -> tuple[str, str]:
    """본문을 상황·의미 두 덩어리로 나눔 (있으면)."""
    t = soften_body(text)
    if not t:
        return "", ""
    parts = re.split(r"(?<=[.!?…])\s+", t)
    if len(parts) >= 2:
        return parts[0].strip(), " ".join(parts[1:]).strip()
    return t, ""


def orient_label(is_reversed: bool) -> str:
    if is_reversed:
        return "역방향 — 조율·정리·속도 조절 쪽으로 읽어요."
    return "정방향 — 흐름이 받쳐 주는 쪽으로 읽어요."


def closing_hint(category: str, *, is_reversed: bool) -> str:
    base = _CLOSING_HINT.get(category, "오늘은 한 걸음만 옮겨 보세요.")
    if is_reversed:
        return f"서두르지 말고, {base}"
    return base


def build_position_body(
    excerpt: str,
    *,
    category: str,
    spread_key: str,
    index: int,
    is_reversed: bool,
    position_role: str = "",
    excerpt_kind: str = "category",
) -> str:
    """자리·카테고리 렌즈 + 본문 조합."""
    hook = category_hook(category)
    lens = ""
    if excerpt_kind != "temporal":
        lens = temporal_lens(spread_key, index, is_reversed=is_reversed)
        if spread_key in ("love", "deep") and position_role:
            lens = f"{position_role}에서는"

    main, sub = split_meaning_lines(excerpt)
    orient = orient_label(is_reversed)

    chunks: list[str] = []
    if lens:
        chunks.append(lens)
    chunks.append(f"{hook},")
    if main:
        chunks.append(main)
    if sub:
        chunks.append(sub)
    chunks.append(orient)
    return " ".join(c for c in chunks if c).strip()
