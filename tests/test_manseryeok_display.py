# -*- coding: utf-8 -*-
"""만세력 한글 표기·카드 문구 필터."""

from __future__ import annotations

import json
from pathlib import Path

from saju import manseryeok_display as msd

DATA_PATH = Path(__file__).resolve().parents[1] / "saju" / "data" / "manseryeok_data.json"


def test_display_title_uses_sub_category_for_hanja_chapter():
    item = {
        "chapter": "太陽過宮表 / 八節三奇法",
        "sub_category": "태양과궁·삼기법",
        "korean_translation": "태양과궁표(太陽過宮表): 각 월별 절기",
    }
    assert msd.display_title(item) == "태양과궁·삼기법"


def test_card_description_skips_generic_beginner():
    item = {
        "beginner_explanation": (
            "사주팔자의 기초 이론입니다. 천간·지지·오행의 관계를 이해하면 "
            "내 사주를 스스로 분석할 수 있습니다."
        ),
        "modern_interpretation": "태양과궁표는 절기 택일에 활용합니다.",
    }
    assert "사주팔자의 기초" not in msd.card_description(item)
    assert "태양과궁" in msd.card_description(item)


def test_annotate_samjae_line():
    raw = "• 三災入命\n十神 = 比肩·劫財·食神"
    out = msd.annotate_text(raw)
    assert "삼재" in out
    assert "비견" in out
    assert "식신" in out


def test_enrich_item_fields():
    db = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    item = next(r for r in db if r["id"] == "012_001")
    enriched = msd.enrich_item(item)
    assert enriched["display_title"] == "삼재·육친·장간 이론"
    assert enriched["display_card_desc"]
    assert "삼재" in enriched["display_original"] or "삼재" in enriched["display_body_primary"]
