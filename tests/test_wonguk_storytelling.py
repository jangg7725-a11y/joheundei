# -*- coding: utf-8 -*-
"""원국 맞춤 스토리텔링 — 1966 검증 사주."""

from __future__ import annotations

from saju import analysis as an
from saju import jijanggan as jj
from saju import unteim_narrative_bridge as unb


def _report():
    return an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
    )


def test_jijanggan_user_desc_no_textbook() -> None:
    r = _report()
    for pk in ("year", "month", "day", "hour"):
        block = r["jijanggan"][pk]
        for h in block.get("hidden") or []:
            desc = h.get("user_desc") or ""
            assert "正氣" not in desc
            assert "本氣" not in desc
            assert desc.strip()


def test_pillar_bottom_mentions_branches() -> None:
    r = _report()
    pbs = r.get("pillar_bottom_stories") or {}
    assert "午" in pbs.get("year", "")
    assert "子" in pbs.get("month", "")
    assert "申" in pbs.get("day", "")
    assert "丑" in pbs.get("hour", "")


def test_kongmang_custom_story() -> None:
    r = _report()
    km = r["sinsal"].get("공망_맞춤") or {}
    assert km.get("공망_글자")
    assert "「" in (km.get("해설") or "")
    assert km.get("보완법")


def test_emotion_narrative_connected() -> None:
    r = _report()
    emo = (r["원국_스토리텔링"]["unteim_서사"] or {}).get("감정_서사") or ""
    assert "감정" in emo or "패턴" in emo
    assert len(emo) > 40


def test_daymaster_psychology_all_stems() -> None:
    for dm in "甲乙丙丁戊己庚辛壬癸":
        data = unb.get_daymaster_psychology(dm)
        assert data
        assert data.get("core_image") or data.get("identity_pool")


def test_interpret_slot_female() -> None:
    s = jj.interpret_slot_for_user("day", "정기", "癸", "정재", True)
    assert "시어머니" in s or "재산" in s
