# -*- coding: utf-8
"""타로 스프레드 스토리텔링."""

from __future__ import annotations

from saju import tarot as tr
from saju import tarot_narrative as tn


def _sample_sections(count: int, *, reversed_idx: set[int] | None = None) -> list[dict]:
    rev = reversed_idx or set()
    cards = tr.deck_cards()[:count]
    out = []
    for i, card in enumerate(cards):
        out.append(
            {
                "position": i + 1,
                "position_label": str(i + 1),
                "position_role": "흐름",
                "card_id": card["id"],
                "name": card["name"],
                "keyword": card.get("keyword", ""),
                "element": card.get("element", ""),
                "category_slug": card.get("category_slug", ""),
                "category_kr": card.get("category_kr", ""),
                "is_reversed": i in rev,
                "orient": "역방향" if i in rev else "정방향",
                "excerpt": card["upright"]["종합운"],
                "today_message": card.get("today_message", ""),
            }
        )
    return out


def test_spread_counts() -> None:
    tr.load_deck.cache_clear()
    assert tr.SPREADS["month"]["count"] == 5
    assert tr.SPREADS["year"]["count"] == 7
    assert tr.SPREADS["year"]["label"] == "신년 타로"


def test_worry_positions_past_present_future() -> None:
    positions = tr.SPREAD_POSITIONS["worry"]
    labels = [p["label"] for p in positions]
    assert labels == ["과거", "현재", "미래"]


def test_build_spread_story_worry_card_style() -> None:
    sections = _sample_sections(3)
    story = tn.build_spread_story("worry", "고민 타로", "종합운", sections)
    types = [s["type"] for s in story["narrative_sections"]]
    assert types.count("scene") == 3
    assert "2막 · 막힘" not in story["narrative"]
    assert "장애" not in story["narrative"]
    assert "1번 카드는" in story["narrative"] or "1번째" in story["narrative"]
    assert sections[0].get("position_reading")


def test_build_spread_story_year_seven_cards() -> None:
    sections = _sample_sections(7)
    story = tn.build_spread_story("year", "신년 타로", "종합운", sections)
    assert story["narrative_sections"][0]["title"] == "리딩 시작"
    scene_count = sum(1 for s in story["narrative_sections"] if s["type"] == "scene")
    assert scene_count == 7
    assert "신년" in story["opening"] or "1-2월" in story["narrative"]


def test_spread_reading_includes_position_reading() -> None:
    tr.load_deck.cache_clear()
    cards = [
        {"card_id": "24", "is_reversed": False},
        {"card_id": "53", "is_reversed": False},
        {"card_id": "19", "is_reversed": False},
    ]
    out = tr.spread_reading("worry", cards, "종합운")
    assert out["positions"][0].get("position_reading")
    assert "집" in out["positions"][0]["position_reading"]
    assert out["positions"][0]["position_label"] == "과거"


def test_compose_card_reading_deck_label() -> None:
    card = tr.card_by_id("24")
    sec = {
        "card_id": card["id"],
        "name": card["name"],
        "keyword": card.get("keyword", ""),
        "category_slug": card.get("category_slug", ""),
        "category_kr": card.get("category_kr", ""),
        "position_label": "과거",
        "position_role": "지금까지의 흐름",
        "is_reversed": False,
        "excerpt": card["upright"]["종합운"],
    }
    text = tn.compose_card_reading(sec, spread_key="worry", category="종합운", index=0, total=3)
    assert "24번" in text
    assert "토카드" in text
    assert "집" in text
