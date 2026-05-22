# -*- coding: utf-8 -*-
"""만세력 택일 파서·API 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app
from saju.manseryeok_taekil import (
    EVENT_RULES,
    parse_calendar_days,
    rank_days_for_event,
    score_day_for_event,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "saju" / "data" / "manseryeok_data.json"


@pytest.fixture(scope="module")
def db():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def calendar_items(db):
    return [
        r
        for r in db
        if r.get("canonical_key") == "일진달력"
        or "달력" in (r.get("sub_category") or "")
    ]


def test_parse_calendar_days_finds_yi_ji():
    item = next(r for r in json.loads(DATA_PATH.read_text(encoding="utf-8")) if r["id"] == "001_001")
    days = parse_calendar_days(item["original_text"])
    assert len(days) >= 5
    assert days[0]["ganji"]
    assert days[0]["yi_raw"]
    assert days[0]["ji_raw"]


def test_score_day_for_wedding():
    item = json.loads(DATA_PATH.read_text(encoding="utf-8"))[0]
    day = parse_calendar_days(item["original_text"])[0]
    scored = score_day_for_event(day, "결혼")
    assert "grade" in scored
    assert "score" in scored
    assert scored["event_label"] == EVENT_RULES["결혼"]["label"]


def test_rank_days_for_event():
    db = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    cal = [r for r in db if r.get("canonical_key") == "일진달력"][:2]
    pack = rank_days_for_event(cal, "결혼", limit=10)
    assert pack["total_parsed_days"] > 0
    assert isinstance(pack["good_days"], list)
    assert isinstance(pack["avoid_days"], list)


def test_taekil_api():
    client = TestClient(app)
    r = client.get("/api/manseryeok/taekil", params={"event": "결혼", "month": "1월", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["event"] == "결혼"
    assert body["total_parsed_days"] >= 0
    assert "related_docs" in body


def test_manseryeok_compute_api():
    client = TestClient(app)
    r = client.post(
        "/api/manseryeok/compute",
        json={
            "calendar": "solar",
            "year": 1990,
            "month": 5,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "gender": "male",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    p = data["profile"]
    assert p["day_master"]
    assert p["match_params"]
    assert "matched_docs" in p
