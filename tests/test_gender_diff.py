# -*- coding: utf-8 -*-
"""동일 원국(음력 1966-11-04 02:05)에서 성별에 따라 스토리가 완전히 갈리는지 검증한다."""

from __future__ import annotations

from typing import Any, List

import pytest

from saju import analysis as an


def _flatten_strings(obj: Any, out: List[str]) -> None:
    if isinstance(obj, str):
        if obj.strip():
            out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _flatten_strings(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _flatten_strings(v, out)


def _story_text(story: dict) -> str:
    parts: List[str] = []
    _flatten_strings(story, parts)
    return "\n".join(parts)


def _report(*, gender: str) -> dict:
    return an.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender=gender,
        lunar_leap=False,
        sewoon_center_year=2026,
        partner_day_pillar=None,
    )


@pytest.fixture(scope="module")
def male_story() -> dict:
    return _report(gender="male")["원국_스토리텔링"]


@pytest.fixture(scope="module")
def female_story() -> dict:
    return _report(gender="female")["원국_스토리텔링"]


def test_core_line_differs(male_story: dict, female_story: dict) -> None:
    assert male_story["사주_한줄_핵심"] != female_story["사주_한줄_핵심"]


def test_personality_first_strength_differs(male_story: dict, female_story: dict) -> None:
    m = male_story["성격_분석"]["장점_5"][0]
    f = female_story["성격_분석"]["장점_5"][0]
    assert m != f


def test_personality_first_weakness_differs(male_story: dict, female_story: dict) -> None:
    m = male_story["성격_분석"]["단점_5"][0]
    f = female_story["성격_분석"]["단점_5"][0]
    assert m != f


def test_social_style_differs(male_story: dict, female_story: dict) -> None:
    assert male_story["성격_분석"]["대인관계_스타일"] != female_story["성격_분석"]["대인관계_스타일"]


def test_career_top1_job_differs(male_story: dict, female_story: dict) -> None:
    m_top = male_story["직업_적성"]["최적_직군_TOP5"]
    f_top = female_story["직업_적성"]["최적_직군_TOP5"]
    m_jobs = [x["직군"] for x in m_top]
    f_jobs = [x["직군"] for x in f_top]
    m_reasons = [x["이유"] for x in m_top]
    f_reasons = [x["이유"] for x in f_top]
    assert m_jobs != f_jobs or m_reasons != f_reasons


def test_health_first_vulnerable_axis_differs(male_story: dict, female_story: dict) -> None:
    m = male_story["건강_평생"]["선천_취약_축"][0]
    f = female_story["건강_평생"]["선천_취약_축"][0]
    assert m != f


def test_nampyeon_word_female_only(male_story: dict, female_story: dict) -> None:
    tm = _story_text(male_story)
    tf = _story_text(female_story)
    assert "남편" in tf
    assert "남편" not in tm


def test_anae_word_male_only(male_story: dict, female_story: dict) -> None:
    tm = _story_text(male_story)
    tf = _story_text(female_story)
    assert "아내" in tm
    assert "아내" not in tf


def test_buingwa_word_female_only(male_story: dict, female_story: dict) -> None:
    tm = _story_text(male_story)
    tf = _story_text(female_story)
    assert "부인과" in tf
    assert "부인과" not in tm


def test_prostate_word_male_only(male_story: dict, female_story: dict) -> None:
    tm = _story_text(male_story)
    tf = _story_text(female_story)
    assert "전립선" in tm
    assert "전립선" not in tf
