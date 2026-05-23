# -*- coding: utf-8 -*-
"""만세력 쉬운 해석 변환."""

from saju import manseryeok_insights as msi


def test_explain_match_params_plain_language():
    rows = msi.explain_match_params(
        {"shinsin": "상관", "sinsal": "도화살", "gyeokguk": "상관격", "ohaeng": "목"}
    )
    assert len(rows) >= 3
    assert any("표현" in r["plain"] for r in rows)


def test_doc_to_insight_has_friendly_fields():
    item = {
        "id": "012_001",
        "category": "혼인",
        "sub_category": "생기복덕 혼인 일람표",
        "modern_interpretation": "결혼 택일에 쓰이는 생기복덕법 도표입니다.",
        "match_conditions": {"십신": ["상관"], "신살": [], "격국": [], "five_elements": ["목"]},
        "practical": {"applicable_events": ["결혼", "택일"]},
        "_match_score": 5,
    }
    ins = msi.doc_to_insight(item, {"shinsin": "상관", "ohaeng": "목"})
    assert ins["title"]
    assert ins["summary"]
    assert "결혼" in ins["title"] or "결혼" in str(ins.get("events"))


def test_build_match_insights_groups():
    docs = [
        {
            "id": "a",
            "category": "혼인",
            "modern_interpretation": "혼인 길일.",
            "practical": {"applicable_events": ["결혼"]},
            "match_conditions": {},
        },
        {
            "id": "b",
            "category": "길흉",
            "modern_interpretation": "길신 설명.",
            "practical": {"applicable_events": ["택일"]},
            "match_conditions": {},
        },
    ]
    pack = msi.build_match_insights(docs, {})
    assert len(pack["items"]) == 2
    assert pack["groups"]
