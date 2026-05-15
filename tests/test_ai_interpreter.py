# -*- coding: utf-8 -*-
"""AI 해설 모듈 (mock)."""

from __future__ import annotations

import json

import pytest

from saju import ai_cache
from saju import ai_interpreter as ai
from saju import analysis


@pytest.fixture
def sample_report(sample_birth):
    return analysis.build_report(
        calendar=sample_birth.calendar,
        year=sample_birth.year,
        month=sample_birth.month,
        day=sample_birth.day,
        hour=sample_birth.hour,
        minute=sample_birth.minute,
        gender=sample_birth.gender,
        lunar_leap=sample_birth.lunar_leap,
        sewoon_center_year=2026,
    )


def test_chart_cache_key_stable(sample_report):
    k1 = ai_cache.chart_cache_key(sample_report)
    k2 = ai_cache.chart_cache_key(sample_report)
    assert k1 == k2
    assert len(k1) == 32


def test_parse_sections_json():
    raw = json.dumps(
        {
            "sections": [
                {"id": "1-1", "title": "요약", "content": "당신은 불과 흙이 많은 사주입니다."}
            ]
        },
        ensure_ascii=False,
    )
    secs = ai._parse_sections(raw)
    assert len(secs) == 1
    assert secs[0]["content"].startswith("당신은")


def test_interpret_wonkuk_mock(sample_report, monkeypatch):
    fake = json.dumps(
        {
            "sections": [
                {
                    "id": "1-1",
                    "title": "한줄 요약",
                    "content": "당신은 戊(무) 일간으로 묵직한 기운을 타고났습니다.",
                }
            ]
        },
        ensure_ascii=False,
    )

    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(ai, "_call_llm", lambda _s, _u: fake)

    cache_key = ai_cache.chart_cache_key(sample_report)
    ai_cache.delete_cached(cache_key, "wonkuk")

    out = ai.interpret_wonkuk_full(sample_report, force_refresh=True, tier="premium")
    assert out["ok"] is True
    assert out["sections"][0]["content"].startswith("당신은")

    cached = ai.interpret_wonkuk_full(sample_report, tier="premium")
    assert cached["from_cache"] is True


def test_normalize_tab():
    assert ai.normalize_tab("0") == "wonkuk"
    assert ai.normalize_tab("종합") == "jonghap"
