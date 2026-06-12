# -*- coding: utf-8 -*-
"""타로 카드 DB 보강 검증."""

from __future__ import annotations

import json
from pathlib import Path

from saju import tarot as tr

ROOT = Path(__file__).resolve().parents[1]
TAROT_DATA = ROOT / "saju" / "data" / "tarot"


def _all_pack_cards() -> list[dict]:
    index = json.loads((TAROT_DATA / "index.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    for pack in index["packs"]:
        rows.extend(
            json.loads((TAROT_DATA / pack["file"]).read_text(encoding="utf-8"))
        )
    return rows


def test_pack_cards_have_db_v2_fields() -> None:
    cards = _all_pack_cards()
    assert len(cards) == 60
    for card in cards:
        assert card.get("db_version") == 2, card["id"]
        assert isinstance(card.get("keywords"), list) and card["keywords"]
        assert card.get("core", {}).get("light")
        assert card.get("core", {}).get("shadow")
        temporal = card.get("temporal") or {}
        for axis in ("past", "present", "future"):
            block = temporal.get(axis) or {}
            assert block.get("upright"), f"{card['id']} {axis} upright"
            assert block.get("reverse"), f"{card['id']} {axis} reverse"


def test_meanings_no_stiff_tail() -> None:
    stiff = 0
    for card in _all_pack_cards():
        for side in ("upright", "reverse"):
            for text in (card.get(side) or {}).values():
                if "시기입니다" in text:
                    stiff += 1
    assert stiff == 0, f"딱딱한 꼬리 {stiff}건 남음"


def test_temporal_excerpt_for_worry_and_week() -> None:
    tr.load_deck.cache_clear()
    card = tr.card_by_id("24")
    for spread in ("worry", "week"):
        past = tr.reading_text(
            card, "종합운", reversed=False, spread_key=spread, position_index=0
        )
        assert "그동안" in past
        assert tr.reading_text(card, "종합운", reversed=False) != past
