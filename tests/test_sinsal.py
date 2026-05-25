# -*- coding: utf-8 -*-
"""STEP 8: 신살."""

from __future__ import annotations

from saju import sinsal as sn


def test_step8_sinsal(day_master: str, sample_pillars, sample_birth) -> None:
    gender = sample_birth.gender if sample_birth.gender else "male"
    out = sn.analyze_sinsal(day_master, sample_pillars, gender=gender)
    assert "신살_목록" in out
    assert isinstance(out["신살_목록"], list)
    if out["신살_목록"]:
        row = out["신살_목록"][0]
        assert row["신살"]
        assert row["길흉"] in ("길", "흉", "중")
    assert "신살_주별" in out
    assert "신살_개수" in out
    assert out["신살_개수"]["전체"] >= len(out.get("신살_목록_요약") or [])


def test_pillar_native_sinsal_1966_solar() -> None:
    """양력 1966-09-19 18:27 여 — 타 만세력과 맞는 주별 신살."""
    from saju.saju_calc import BirthInput, compute_saju

    raw = compute_saju(
        BirthInput(
            calendar="solar",
            year=1966,
            month=9,
            day=19,
            hour=18,
            minute=27,
            gender="female",
        )
    )
    pillars = raw["pillars"]
    dm = pillars["day"]["gan"]
    out = sn.analyze_sinsal(dm, pillars, gender="female")
    by = out["신살_주별"]

    def names(pk: str) -> set[str]:
        return {x["신살"] for x in by.get(pk, [])}

    assert "도화살" in names("year")
    assert "천을귀인" in names("year")
    assert "문곡귀인" in names("year")
    assert "장성살" in names("year")

    assert "장성살" in names("month")
    assert "홍염살" in names("month")
    assert "공망살" in names("month")

    assert "망신살" in names("day")
    assert "천복귀인" in names("day")
    assert "공망살" not in names("day")

    assert "장성살" in names("hour")
    assert "홍염살" in names("hour")
    assert "공망살" in names("hour")


def test_sewoon_sinsal_includes_chong_when_applicable() -> None:
    """세운 지지가 원국과 충이면 세운 신살에 충 항목이 포함되어야 한다."""
    pillars = {
        "year": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
        "month": {"gan": "丙", "zhi": "午", "pillar": "丙午"},
        "day": {"gan": "戊", "zhi": "子", "pillar": "戊子"},
        "hour": {"gan": "庚", "zhi": "申", "pillar": "庚申"},
    }
    pack = sn.sewoon_sinsal("戊", pillars, "male", "丙", "午")
    names = {r.get("신살") for r in pack.get("발동_목록") or []}
    assert any("충" in str(n) for n in names)
