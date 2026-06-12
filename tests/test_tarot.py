# -*- coding: utf-8
"""타로 API."""

from __future__ import annotations

import random

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    import main

    return TestClient(main.app)


def test_tarot_cards_json_endpoint(client: TestClient) -> None:
    r = client.get("/data/tarot_cards.json")
    assert r.status_code == 200
    data = r.json()
    assert data["card_count"] == 60
    assert len(data["cards"]) == 60
    assert data["cards"][0]["id"] == "01"
    assert "upright" in data["cards"][0]
    assert "reverse" in data["cards"][0]


def test_tarot_spreads_meta(client: TestClient) -> None:
    r = client.get("/api/tarot/spreads")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "today" in body["spreads"]
    assert body["spreads"]["deep"]["count"] == 10
    assert "종합운" in body["reading_categories"]


def test_tarot_draw_today(client: TestClient) -> None:
    import saju.tarot as tr

    tr.load_deck.cache_clear()
    out = tr.draw_cards("today", "연애운", rng=random.Random(42))
    assert len(out["cards"]) == 1
    card = out["cards"][0]
    assert card["reading"]["category"] == "연애운"
    assert card["rotation"] in (0, 180)
    assert card["is_reversed"] == (card["rotation"] == 180)


def test_tarot_draw_week_api(client: TestClient) -> None:
    r = client.get("/api/tarot/draw/week", params={"category": "종합운"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert len(body["cards"]) == 3
    ids = {c["card_id"] for c in body["cards"]}
    assert len(ids) == 3


def test_tarot_reading_lookup(client: TestClient) -> None:
    r = client.get(
        "/api/tarot/reading/01",
        params={"category": "종합운", "reversed": "false"},
    )
    assert r.status_code == 200
    card = r.json()["card"]
    assert card["name"] == "씨앗"
    assert card["is_reversed"] is False
    assert "가능성" in card["reading"]["content"] or len(card["reading"]["content"]) > 10


def test_tarot_invalid_spread(client: TestClient) -> None:
    r = client.get("/api/tarot/draw/invalid")
    assert r.status_code == 400


def test_tarot_reveal_api(client: TestClient) -> None:
    import saju.tarot as tr

    tr.load_deck.cache_clear()
    out = tr.reveal_card("01", "종합운", rng=random.Random(7))
    card = out["card"]
    assert card["card_id"] == "01"
    assert card["reading"]["category"] == "종합운"
    assert card["rotation"] in (0, 180)

    r = client.get("/api/tarot/reveal/01", params={"category": "연애운"})
    assert r.status_code == 200
    assert r.json()["card"]["reading"]["category"] == "연애운"


def test_tarot_invalid_category(client: TestClient) -> None:
    r = client.get("/api/tarot/draw/today", params={"category": "없는운"})
    assert r.status_code == 400


def test_tarot_spread_narrative_week(client: TestClient) -> None:
    import saju.tarot as tr

    tr.load_deck.cache_clear()
    cards = [
        {"card_id": "01", "is_reversed": False},
        {"card_id": "19", "is_reversed": True},
        {"card_id": "20", "is_reversed": False},
    ]
    out = tr.spread_reading("week", cards, "종합운")
    assert out["count"] == 3
    assert len(out["positions"]) == 3
    assert out["positions"][0]["position_label"] == "초반"
    assert "씨앗" in out["narrative"]
    assert "마무리" in out["closing"] or "산" in out["closing"]

    r = client.post(
        "/api/tarot/spread-reading",
        json={"spread": "week", "category": "종합운", "cards": cards},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["spread"] == "week"
    assert len(body["positions"]) == 3
    assert len(body["narrative"]) > 80
    assert "narrative_sections" in body
    assert len(body["narrative_sections"]) >= 4
    assert body.get("synthesis")
    assert body.get("closing")
    types = [s["type"] for s in body["narrative_sections"]]
    assert types.count("scene") == 3
    assert body["positions"][1].get("transition_from_prev")
    assert "이어집니다" in body["narrative"]


def test_tarot_spread_narrative_wrong_count(client: TestClient) -> None:
    r = client.post(
        "/api/tarot/spread-reading",
        json={
            "spread": "week",
            "category": "종합운",
            "cards": [{"card_id": "01", "is_reversed": False}],
        },
    )
    assert r.status_code == 400
