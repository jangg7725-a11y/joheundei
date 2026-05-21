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
                "is_reversed": i in rev,
                "orient": "역방향" if i in rev else "정방향",
                "excerpt": card["upright"]["종합운"],
                "today_message": card.get("today_message", ""),
            }
        )
    return out


def test_build_spread_story_week_has_acts() -> None:
    sections = _sample_sections(3)
    story = tn.build_spread_story("week", "이주의 타로", "종합운", sections)
    types = [s["type"] for s in story["narrative_sections"]]
    assert "opening" in types
    assert types.count("act") == 3
    assert "synthesis" in types
    assert "closing" in types
    assert "씨앗" in story["narrative"] or sections[0]["name"] in story["narrative"]


def test_build_spread_story_year_quarters() -> None:
    sections = _sample_sections(12)
    story = tn.build_spread_story("year", "올해의 타로", "종합운", sections)
    assert story["narrative_sections"][1]["title"].startswith("1분기")
    assert "올해" in story["synthesis"]


def test_spread_reading_includes_scene_summary() -> None:
    tr.load_deck.cache_clear()
    cards = [
        {"card_id": "01", "is_reversed": False},
        {"card_id": "02", "is_reversed": False},
        {"card_id": "03", "is_reversed": True},
    ]
    out = tr.spread_reading("week", cards, "종합운")
    assert out["positions"][0].get("scene_summary")
