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


def test_tarot_invalid_category(client: TestClient) -> None:
    r = client.get("/api/tarot/draw/today", params={"category": "없는운"})
    assert r.status_code == 400
