# -*- coding: utf-8 -*-
"""운테임 narrative DB 로드·연동."""

from __future__ import annotations

from saju import analysis as an
from saju import narrative_loader as nl
from saju import unteim_narrative_bridge as unb


def test_narrative_files_present() -> None:
    files = nl.list_narrative_files()
    assert len(files) >= 15
    assert "money_pattern_db.json" in files
    db = nl.load_narrative_db("money_pattern_db")
    assert "oheng_money" in db
    assert "engine_mapping" in db


def test_unteim_supplement_in_report() -> None:
    r = an.build_report(
        calendar="solar",
        year=1962,
        month=9,
        day=28,
        hour=4,
        minute=10,
        gender="male",
        lunar_leap=False,
    )
    story = r["원국_스토리텔링"]
    unteim = story.get("unteim_서사") or {}
    assert unteim.get("_files_loaded", 0) >= 15
    assert unteim.get("재물", {}).get("한줄_보강") or unteim.get("건강")
    assert "unteim_보강" in story.get("재물_패턴", {}) or story["재물_패턴"].get("버는_방식")


def test_bridge_merge_helpers() -> None:
    w = {"버는_방식": "기존 문장."}
    u = {"재물": {"한줄_보강": "운테임 보강.", "문장_목록": ["운테임 보강."]}}
    out = unb.merge_wealth_with_unteim(w, u)
    assert "운테임 보강" in out["버는_방식"]
