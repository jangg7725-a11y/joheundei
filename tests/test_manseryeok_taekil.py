# -*- coding: utf-8 -*-
"""만세력 택일 파서·API 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app
from saju import manseryeok_profile as msp
from saju.manseryeok_taekil import (
    EVENT_RULES,
    _pick_good_days,
    parse_calendar_days,
    rank_days_for_event,
    score_day_for_event,
    summarize_taekil_by_month,
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


def test_pick_good_days_spreads_by_month():
    ranked = [
        {"calendar_month": "1월", "score": 30, "id": "a"},
        {"calendar_month": "1월", "score": 25, "id": "b"},
        {"calendar_month": "1월", "score": 22, "id": "c"},
        {"calendar_month": "1월", "score": 20, "id": "d"},
        {"calendar_month": "3월", "score": 12, "id": "e"},
        {"calendar_month": "3월", "score": 10, "id": "f"},
    ]
    picked = _pick_good_days(ranked, limit=6, month_filter="")
    months = {d["calendar_month"] for d in picked}
    assert "1월" in months
    assert "3월" in months


def test_summarize_taekil_by_month():
    ranked = [
        {"calendar_month": "1월", "score": 22, "grade": "대길", "day_label_kr": "1월 18일"},
        {"calendar_month": "1월", "score": -18, "grade": "흉", "day_label_kr": "1월 20일"},
        {"calendar_month": "3월", "score": 10, "grade": "길", "day_label_kr": "3월 5일"},
    ]
    ov = summarize_taekil_by_month(ranked)
    assert len(ov["months"]) == 12
    jan = next(m for m in ov["months"] if m["month"] == "1월")
    assert jan["has_data"] is True
    assert jan["good_count"] >= 1
    assert "1월" in ov["best_months"]
    assert "3월" in ov["best_months"]
    assert "1월" not in ov["avoid_months"] or jan["avoid_count"] >= 1
    assert ov.get("summary_line")


def test_taekil_api():
    client = TestClient(app)
    r = client.get("/api/manseryeok/taekil", params={"event": "결혼", "month": "1월", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["event"] == "결혼"
    assert body["total_parsed_days"] >= 0
    if body["good_days"]:
        d = body["good_days"][0]
        assert d.get("day_label_kr")
        assert d.get("calendar_month")
        assert d["calendar_month"] in d["day_label_kr"]
        assert d.get("ganji_kr")
        assert d.get("yi_display") or d.get("yi_hits_kr")

    r2 = client.get("/api/manseryeok/taekil", params={"event": "개업", "limit": 10})
    assert r2.status_code == 200
    full = r2.json()
    assert "month_overview" in full
    assert len(full["month_overview"]["months"]) == 12
    assert full["month_overview"].get("summary_line")


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
    wk = p.get("wonguk") or {}
    assert wk.get("pillars", {}).get("day", {}).get("gan")
    assert wk.get("sipsin_stems")
    assert wk.get("sibiunsung")
    assert wk.get("jijanggan")
    assert wk.get("ohaeng", {}).get("counts")
    assert (wk.get("sinsal") or {}).get("신살_목록") is not None
    assert p.get("sewoon_year")
    sew_ps = (wk.get("sinsal") or {}).get("세운_신살") or {}
    assert sew_ps.get("범위") == "세운"
    assert "발동_목록" in sew_ps


def test_sikshin_rank_prefers_myungri_over_honin(db):
    """월간 십신 식신일 때 명리·역법 문헌이 혼인보다 앞서 정렬된다."""
    mp = {"shinsin": "식신", "sinsal": "", "gyeokguk": "", "ohaeng": ""}
    scored, _ = msp.rank_manseryeok_matches(db, mp, limit=50)
    assert scored
    cats = [r.get("category") for r in scored]
    if "혼인" in cats and "명리" in cats:
        assert cats.index("명리") < cats.index("혼인")


def test_sikshin_category_score_adjustment():
    mc = {"십신": ["식신"], "신살": [], "격국": [], "five_elements": []}
    mp = {"shinsin": "식신", "sinsal": "", "gyeokguk": "", "ohaeng": ""}
    honin = {"category": "혼인", "match_conditions": mc, "practical": {"priority_rank": 1}}
    myungri = {"category": "명리", "match_conditions": mc, "practical": {"priority_rank": 1}}
    assert msp.score_manseryeok_item(myungri, mp) == 5
    assert msp.score_manseryeok_item(honin, mp) == 1
