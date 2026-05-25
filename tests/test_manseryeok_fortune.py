# -*- coding: utf-8 -*-
"""manseryeok_fortune — 세운·월운 요약."""

from saju import manseryeok_fortune as mf
from saju import manseryeok_profile as msp


def test_wonguk_has_sipsin_jijanggan_sibiunsung_sinsal():
    p = msp.compute_manseryeok_profile(
        calendar="solar",
        year=1966,
        month=12,
        day=15,
        hour=2,
        minute=5,
        gender="female",
    )
    wk = p.get("wonguk") or {}
    year = (wk.get("pillars") or {}).get("year") or {}
    assert year.get("sip_gan")
    assert year.get("sibi_stage")
    assert len(year.get("jijanggan") or []) >= 1
    assert wk.get("ohaeng", {}).get("counts")
    assert len(wk.get("sinsal_all") or []) >= 1


def test_build_fortune_has_sewoon_and_twelve_months():
    p = msp.compute_manseryeok_profile(
        calendar="solar",
        year=1966,
        month=12,
        day=15,
        hour=2,
        minute=5,
        gender="female",
        user_name="테스트",
    )
    f = p.get("fortune") or {}
    assert f.get("center_year")
    se = f.get("sewoon") or {}
    assert se.get("pillar")
    assert se.get("grade") in ("길한 편", "보통", "조심")
    assert se.get("headline")
    assert len(se.get("story") or []) >= 2
    assert len(se.get("phases") or []) == 3
    assert (se.get("position") or {}).get("intro")
    months = (f.get("monthly") or {}).get("months") or []
    assert len(months) == 12
    assert (months[0].get("detail") or {}).get("story")


def test_plain_grade_mapping():
    assert mf._plain_grade("길운") == "길한 편"
    assert mf._plain_grade("흉운") == "조심"
