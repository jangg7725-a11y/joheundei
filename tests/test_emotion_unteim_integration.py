# -*- coding: utf-8 -*-
"""emotion_db · 세운월운 · 궁합 매트릭스 연동 테스트."""

from __future__ import annotations

from saju import analysis as an
from saju import emotion_db_bridge as emb
from saju import goonghap as gh
from saju import narrative_loader as nl
from saju import ohaeng as oh
from saju import saju_calc as sc
from saju import unteim_narrative_bridge as unb
from saju import yongsin as ys


def _birth(calendar: str, y: int, m: int, d: int, hour: int, gender: str):
    birth = sc.BirthInput(
        calendar=calendar,
        year=y,
        month=m,
        day=d,
        hour=hour,
        minute=0,
        lunar_leap=False,
        gender=gender,
    )
    raw = sc.compute_saju(birth)
    counts = oh.count_elements(raw["pillars"], include_hidden=True)
    yong = ys.suggest_useful_gods(
        counts, raw["day_master"], raw["pillars"]["month"]["zhi"], pillars=raw["pillars"]
    )
    return raw, counts, yong


def test_emotion_db_files_loaded():
    files = nl.list_emotion_files()
    assert len(files) >= 6
    pack = emb.build_emotion_supplement(day_master="甲", counts={"목": 4, "화": 1, "토": 1, "금": 1, "수": 1})
    assert pack.get("_files_loaded", 0) >= 6
    assert pack.get("표시_텍스트")


def test_report_has_unteim_timeline_and_emotion():
    report = an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
    )
    story = report.get("원국_스토리텔링") or {}
    unteim = story.get("unteim_서사") or {}
    assert unteim.get("감정_서사")
    tm = report.get("unteim_세운월운") or {}
    assert tm.get("연도별")
    assert tm.get("월별")


def test_goonghap_compatibility_matrix():
    raw_a, ca, ya = _birth("solar", 1990, 1, 15, 12, "male")
    raw_b, cb, yb = _birth("solar", 1991, 6, 20, 12, "female")
    pack = gh.analyze_goonghap_pair(
        raw_a=raw_a,
        raw_b=raw_b,
        counts_a=ca,
        counts_b=cb,
        yong_a=ya,
        yong_b=yb,
    )
    mx = pack.get("일간_매트릭스") or {}
    assert mx.get("found") is True
    assert mx.get("표시_텍스트")


def test_compatibility_matrix_slots():
    slots = unb.pack_compatibility_matrix("甲", "己")
    assert slots.get("found") is True
    assert slots.get("dynamic") or slots.get("strength")
