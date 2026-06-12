# -*- coding: utf-8 -*-
"""12 운세 카테고리 × 모든 스프레드 스토리 연결 검증."""

from __future__ import annotations

import pytest

from saju import tarot as tr
from saju import tarot_category_story as tcs

CATEGORIES = list(tcs.READING_CATEGORIES)
MULTI_SPREADS = ("week", "month", "year", "worry", "love", "deep")
SPREAD_COUNTS = {
    "week": 3,
    "month": 5,
    "year": 7,
    "worry": 3,
    "love": 7,
    "deep": 10,
}

# 카테고리별로 합성·오프닝에 들어가야 할 키워드
CATEGORY_MARKERS = {
    "종합운": "삶 전반",
    "연애운": "마음과 관계",
    "직업운": "일과 커리어",
    "금전운": "재물",
    "건강운": "몸과 마음",
    "대인관계": "사람 사이",
    "이동운": "이동",
    "이직운": "새로운 자리",
    "이사운": "환경",
    "취업운": "시작",
    "자녀운": "성장",
    "오행맞춤운": "맞는 기운",
}


def _fixed_cards(spread_key: str) -> list[dict]:
    n = SPREAD_COUNTS[spread_key]
    pool = ["01", "10", "19", "24", "28", "37", "46", "53", "56", "60"]
    return [{"card_id": pool[i % len(pool)], "is_reversed": i == 1} for i in range(n)]


@pytest.fixture(autouse=True)
def _clear_deck_cache() -> None:
    tr.load_deck.cache_clear()


@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("spread_key", MULTI_SPREADS)
def test_all_categories_have_story_bridges(category: str, spread_key: str) -> None:
    out = tr.spread_reading(spread_key, _fixed_cards(spread_key), category)
    marker = CATEGORY_MARKERS[category]

    assert marker in out["opening"] or marker in out["synthesis"]
    assert out["positions"][0].get("position_reading")
    assert "이어집니다" in out["narrative"] or spread_key == "week"

    for i in range(1, len(out["positions"])):
        assert out["positions"][i].get("transition_from_prev"), (
            f"{spread_key}/{category} pos {i + 1} missing bridge"
        )

    assert out["synthesis"]
    assert out["closing"]
    assert "이야기를 관통" in out["closing"] or "흐름" in out["closing"]


@pytest.mark.parametrize("category", CATEGORIES)
def test_week_uses_category_in_position_reading(category: str) -> None:
    from saju import tarot_reading as trd

    out = tr.spread_reading("week", _fixed_cards("week"), category)
    text = " ".join(p["position_reading"] for p in out["positions"])
    assert trd.category_hook(category) in text or CATEGORY_MARKERS[category] in text


@pytest.mark.parametrize("category", CATEGORIES)
def test_month_position_labels_in_narrative(category: str) -> None:
    out = tr.spread_reading("month", _fixed_cards("month"), category)
    narrative = out["narrative"]
    assert "1주" in narrative
    assert "마무리" in narrative or "5장" in narrative


@pytest.mark.parametrize("category", CATEGORIES)
def test_year_synthesis_mentions_category(category: str) -> None:
    out = tr.spread_reading("year", _fixed_cards("year"), category)
    assert CATEGORY_MARKERS[category] in out["synthesis"] or tcs.phrase(category) in out["synthesis"]


def test_bridge_includes_category_context() -> None:
    from saju import tarot_story_bridge as tsb

    tr.load_deck.cache_clear()
    a, b = tr.card_by_id("24"), tr.card_by_id("53")
    prev = {"name": a["name"], "keyword": a["keyword"], "keywords": a.get("keywords", []),
            "category_slug": a["category_slug"], "element": a["element"], "is_reversed": False, "core": a.get("core", {})}
    curr = {"name": b["name"], "keyword": b["keyword"], "keywords": b.get("keywords", []),
            "category_slug": b["category_slug"], "element": b["element"], "is_reversed": False, "core": b.get("core", {})}
    bridge = tsb.bridge_between_cards(prev, curr, spread_key="month", index=1, category="직업운")
    assert "일과 커리어" in bridge or "커리어" in bridge
