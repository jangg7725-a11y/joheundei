# -*- coding: utf-8 -*-
"""운세 카테고리별 스토리 프레임 — 스프레드·전환·합성에 공통 적용."""

from __future__ import annotations

READING_CATEGORIES: tuple[str, ...] = (
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
)

# 짧은 주제명 (합성·오프닝)
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

# 전환 문장에 붙는 카테고리 관점
CATEGORY_BRIDGE_CTX: dict[str, str] = {
    "종합운": "삶 전반의 흐름으로",
    "연애운": "마음과 관계의 층위에서",
    "직업운": "일과 커리어의 맥락에서",
    "금전운": "재물과 선택의 관점에서",
    "건강운": "몸과 마음의 균형으로",
    "대인관계": "사람 사이의 결을 따라",
    "이동운": "이동과 변화의 리듬으로",
    "이직운": "새로운 자리를 향한 흐름으로",
    "이사운": "살아갈 환경의 관점에서",
    "취업운": "시작과 도전의 맥락에서",
    "자녀운": "성장과 돌봄의 층위에서",
    "오행맞춤운": "나에게 맞는 기운으로",
}

# 첫 카드 리드 (카테고리 × 스프레드)
_FIRST_LEAD: dict[str, dict[str, str]] = {
    "week": {
        "default": "이번 주의 첫 장면, 초반부터 살펴볼게요.",
    },
    "worry": {
        "default": "먼저 과거의 흐름부터 짚어 볼게요.",
    },
    "month": {
        "default": "이번 달 이야기는 1주 차 장면부터 시작합니다.",
    },
    "year": {
        "default": "신년 리딩, 한 해의 첫 흐름부터 따라가 볼게요.",
    },
    "love": {
        "연애운": "연애 이야기는 나의 마음부터 열어볼게요.",
        "default": "관계의 흐름은 나의 마음부터 열어볼게요.",
    },
    "deep": {
        "default": "심층 리딩, 첫 층위부터 내려가 볼게요.",
    },
}

_SPREAD_OPENING: dict[str, str] = {
    "week": "이번 주는 세 장으로 읽습니다. 초반 → 한가운데 → 후반 순서대로 따라가 보세요.",
    "worry": "고민은 과거 → 현재 → 미래 세 장으로 읽습니다. 막힘이 없으면 순풍, 역방향이면 조율이 필요한 흐름으로 해석합니다.",
    "month": "이번 달은 다섯 장으로 읽습니다. 한 주·한 주의 흐름이 이어지는 달의 이야기입니다.",
    "year": "신년은 일곱 장으로 읽습니다. 두 달씩 흐름을 따라가 마지막 총운으로 한 해를 정리합니다.",
    "love": "연애는 일곱 장으로 읽습니다. 나와 상대, 우리의 흐름을 차례대로 짚어 봅니다.",
    "deep": "심층 리딩은 열 장의 층위로 구성됩니다. 표면에서 깊은 결론까지 이어집니다.",
}

_CATEGORY_OPENING_HINT: dict[str, str] = {
    "종합운": "삶 전반을 한 줄의 이야기로 엮어 봅니다.",
    "연애운": "마음과 관계에 초점을 맞춰 읽어 갑니다.",
    "직업운": "일과 커리어의 흐름을 중심에 둡니다.",
    "금전운": "재물과 선택의 관점에서 카드를 연결합니다.",
    "건강운": "몸과 마음의 균형을 따라 읽습니다.",
    "대인관계": "사람 사이의 결을 중심에 둡니다.",
    "이동운": "이동과 변화의 리듬으로 이어 갑니다.",
    "이직운": "새로운 자리를 향한 흐름으로 읽습니다.",
    "이사운": "살아갈 환경과 보금자리를 짚습니다.",
    "취업운": "시작과 도전의 맥락에서 연결합니다.",
    "자녀운": "성장과 돌봄의 층위를 따라갑니다.",
    "오행맞춤운": "나에게 맞는 기운을 중심에 둡니다.",
}


def phrase(category: str) -> str:
    return CATEGORY_PHRASE.get(category, "이번 주제")


def bridge_context(category: str) -> str:
    return CATEGORY_BRIDGE_CTX.get(category, "이 주제의 흐름으로")


def first_card_lead(spread_key: str, category: str) -> str:
    spread_map = _FIRST_LEAD.get(spread_key, {})
    base = spread_map.get(category) or spread_map.get("default", "첫 장면부터 차례대로 읽어 볼게요.")
    cat = phrase(category)
    if spread_key == "love" and category == "연애운":
        return base
    return f"{cat} 관점에서 {base}"


def spread_opening(spread_key: str, category: str) -> str:
    base = _SPREAD_OPENING.get(spread_key, "뽑은 순서대로, 한 장씩 이야기를 이어 갑니다.")
    hint = _CATEGORY_OPENING_HINT.get(category, "")
    if hint:
        return f"{base} {hint}"
    return base


def synthesis_opener(spread_key: str, category: str) -> str:
    cat = phrase(category)
    labels = {
        "worry": f"{cat}을 한 편의 이야기로 엮으면 이렇습니다.",
        "week": f"이번 주 {cat}",
        "month": f"이번 달 {cat}",
        "year": f"신년 {cat}",
        "love": f"{'연애' if category == '연애운' else cat}의 이야기",
        "deep": f"심층 {cat}",
    }
    return labels.get(spread_key, f"{cat} 흐름을 이야기로 엮으면")
