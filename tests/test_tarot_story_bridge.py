# -*- coding: utf-8 -*-
"""타로 카드 간 스토리 연결."""

from __future__ import annotations

from saju import tarot as tr
from saju import tarot_narrative as tn
from saju import tarot_story_bridge as tsb


def test_bridge_between_worry_cards() -> None:
    tr.load_deck.cache_clear()
    c24 = tr.card_by_id("24")
    c53 = tr.card_by_id("53")
    prev = {
        "name": c24["name"],
        "keyword": c24["keyword"],
        "keywords": c24.get("keywords") or [],
        "category_slug": c24["category_slug"],
        "element": c24["element"],
        "is_reversed": False,
        "core": c24.get("core") or {},
    }
    curr = {
        "name": c53["name"],
        "keyword": c53["keyword"],
        "keywords": c53.get("keywords") or [],
        "category_slug": c53["category_slug"],
        "element": c53["element"],
        "is_reversed": False,
        "core": c53.get("core") or {},
    }
    bridge = tsb.bridge_between_cards(
        prev, curr, spread_key="worry", index=1, category="종합운"
    )
    assert "집" in bridge
    assert "지금" in bridge or "현재" in bridge or "순간" in bridge
    assert "토" in bridge or "금" in bridge


def test_worry_spread_story_arc_24_53_19() -> None:
    tr.load_deck.cache_clear()
    cards = [
        {"card_id": "24", "is_reversed": False},
        {"card_id": "53", "is_reversed": False},
        {"card_id": "19", "is_reversed": False},
    ]
    out = tr.spread_reading("worry", cards, "종합운")
    narrative = out["narrative"]
    synthesis = out["synthesis"]

    assert out["positions"][1].get("transition_from_prev")
    assert "이어집니다" in narrative
    assert "한 편의 이야기" in synthesis
    assert "집" in synthesis and "신금" in synthesis and "대지" in synthesis

    readings = [p["position_reading"] for p in out["positions"]]
    assert readings[1] != readings[0]
    assert "그렇게 쌓여 온" in readings[1] or "과거" in readings[1]


def test_week_spread_has_first_lead_and_bridge() -> None:
    tr.load_deck.cache_clear()
    cards = [
        {"card_id": "01", "is_reversed": False},
        {"card_id": "10", "is_reversed": True},
        {"card_id": "19", "is_reversed": False},
    ]
    out = tr.spread_reading("week", cards, "연애운")
    assert "초반" in out["opening"] or "초반" in out["narrative"]
    assert out["positions"][1].get("transition_from_prev")
    assert "시작해" in out["synthesis"] or "마무리" in out["synthesis"]


def test_love_spread_closing_references_arc() -> None:
    tr.load_deck.cache_clear()
    ids = ["24", "53", "19", "25", "26", "27", "28"]
    cards = [{"card_id": cid, "is_reversed": False} for cid in ids]
    out = tr.spread_reading("love", cards, "연애운")
    assert "이야기를 관통" in out["closing"] or "흐름" in out["closing"]
    assert len(out["positions"]) == 7
    assert out["positions"][2].get("transition_from_prev")
