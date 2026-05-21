# -*- coding: utf-8
"""UNTEIM 타로 덱 — 뽑기·해석."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from saju import tarot_narrative as tn

_DATA_ROOT = Path(__file__).resolve().parent.parent / "data"
_TAROT_JSON = _DATA_ROOT / "tarot_cards.json"
_TAROT_PACKS = Path(__file__).resolve().parent / "data" / "tarot"
_MANIFEST = Path(__file__).resolve().parent.parent / "static" / "tarot" / "manifest.json"

READING_CATEGORIES: tuple[str, ...] = (
    "종합운",
    "연애운",
    "직업운",
    "금전운",
    "건강운",
    "대인관계",
    "이동운",
    "이직운",
    "이사운",
    "취업운",
    "자녀운",
    "오행맞춤운",
)

SPREADS: dict[str, dict[str, Any]] = {
    "today": {"label": "오늘의 타로", "count": 1},
    "week": {"label": "이주의 타로", "count": 3},
    "month": {"label": "이달의 타로", "count": 7},
    "year": {"label": "올해의 타로", "count": 12},
    "worry": {"label": "고민 타로", "count": 3},
    "love": {"label": "연애 타로", "count": 7},
    "deep": {"label": "심층 타로", "count": 10},
}

SPREAD_POSITIONS: dict[str, list[dict[str, str]]] = {
    "today": [{"label": "오늘", "role": "지금 이 순간의 메시지"}],
    "week": [
        {"label": "초반", "role": "이번 주의 시작과 기운"},
        {"label": "중반", "role": "한 주의 전개와 변화"},
        {"label": "후반", "role": "마무리와 결과"},
    ],
    "worry": [
        {"label": "현재", "role": "지금 마주한 상황"},
        {"label": "장애", "role": "막고 있는 요인"},
        {"label": "조언", "role": "풀어갈 방향"},
    ],
    "month": [
        {"label": "1", "role": "한 달의 출발점"},
        {"label": "2", "role": "초반의 흐름"},
        {"label": "3", "role": "떠오르는 이슈"},
        {"label": "4", "role": "전환과 변수"},
        {"label": "5", "role": "필요한 조언"},
        {"label": "6", "role": "다가오는 전망"},
        {"label": "7", "role": "한 달의 마무리"},
    ],
    "year": [{"label": f"{m}월", "role": f"{m}월의 기운"} for m in range(1, 13)],
    "love": [
        {"label": "나", "role": "나의 마음과 태도"},
        {"label": "상대", "role": "상대의 에너지"},
        {"label": "관계", "role": "두 사람 사이의 흐름"},
        {"label": "장애", "role": "막고 있는 것"},
        {"label": "조언", "role": "관계를 위한 제언"},
        {"label": "근접", "role": "가까워질 가능성"},
        {"label": "결말", "role": "앞으로의 방향"},
    ],
    "deep": [
        {"label": "1", "role": "현재 상황"},
        {"label": "2", "role": "직면한 장애"},
        {"label": "3", "role": "무의식의 영향"},
        {"label": "4", "role": "지나간 흐름"},
        {"label": "5", "role": "나의 목표"},
        {"label": "6", "role": "가까운 미래"},
        {"label": "7", "role": "나 자신"},
        {"label": "8", "role": "주변 환경"},
        {"label": "9", "role": "희망과 두려움"},
        {"label": "10", "role": "최종 결론"},
    ],
}

REVERSED_PROBABILITY = 0.3


def _build_from_packs() -> dict[str, Any]:
    index = json.loads((_TAROT_PACKS / "index.json").read_text(encoding="utf-8"))
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    meta_by_id = {c["id"]: c for c in manifest["cards"]}
    cards: list[dict[str, Any]] = []
    for pack in index["packs"]:
        rows = json.loads((_TAROT_PACKS / pack["file"]).read_text(encoding="utf-8"))
        for row in rows:
            cid = int(row["id"])
            m = meta_by_id[cid]
            cards.append(
                {
                    **row,
                    "category_slug": m["category"],
                    "category_kr": m["category_kr"],
                    "image_url": f"/static/tarot/{m['file']}",
                    "label_en_hanja": m.get("label_en"),
                }
            )
    cards.sort(key=lambda c: int(c["id"]))
    return {
        "version": 1,
        "deck_name": manifest.get("deck_name", "오행 타로"),
        "card_count": len(cards),
        "back_image_url": "/static/tarot/back/back.png",
        "reversed_probability": REVERSED_PROBABILITY,
        "reading_categories": list(READING_CATEGORIES),
        "spreads": SPREADS,
        "cards": cards,
    }


@lru_cache(maxsize=1)
def load_deck() -> dict[str, Any]:
    if _TAROT_JSON.is_file():
        return json.loads(_TAROT_JSON.read_text(encoding="utf-8"))
    return _build_from_packs()


def deck_cards() -> list[dict[str, Any]]:
    return load_deck()["cards"]


def card_by_id(card_id: str | int) -> dict[str, Any]:
    key = f"{int(card_id):02d}"
    for c in deck_cards():
        if c["id"] == key or c["id"] == str(int(card_id)):
            return c
    raise KeyError(f"카드 없음: {card_id}")


def normalize_category(category: str) -> str:
    cat = category.strip()
    if cat not in READING_CATEGORIES:
        raise ValueError(
            f"카테고리는 {', '.join(READING_CATEGORIES)} 중 하나여야 합니다."
        )
    return cat


def normalize_spread(spread: str) -> str:
    key = spread.strip().lower()
    aliases = {
        "오늘의 타로": "today",
        "이주의 타로": "week",
        "이달의 타로": "month",
        "올해의 타로": "year",
        "고민 타로": "worry",
        "연애 타로": "love",
        "심층 타로": "deep",
    }
    if key in aliases:
        return aliases[key]
    if key in SPREADS:
        return key
    raise ValueError(f"스프레드 없음: {spread}")


def reading_text(card: dict[str, Any], category: str, *, reversed: bool) -> str:
    cat = normalize_category(category)
    side = "reverse" if reversed else "upright"
    block = card.get(side) or {}
    text = block.get(cat)
    if not text:
        raise KeyError(f"해석 없음: card={card['id']} category={cat} reversed={reversed}")
    return text


def card_response(
    card: dict[str, Any],
    category: str,
    *,
    is_reversed: bool,
) -> dict[str, Any]:
    cat = normalize_category(category)
    return {
        "card_id": card["id"],
        "name": card["name"],
        "name_en": card.get("name_en", ""),
        "element": card.get("element", ""),
        "category_slug": card.get("category_slug", ""),
        "category_kr": card.get("category_kr", ""),
        "is_reversed": is_reversed,
        "rotation": 180 if is_reversed else 0,
        "image_url": card.get("image_url", f"/static/tarot/cards/{card['id']}.png"),
        "back_image_url": load_deck().get("back_image_url", "/static/tarot/back/back.png"),
        "keyword": card.get("keyword", ""),
        "today_message": card.get("today_message", ""),
        "reading": {
            "category": cat,
            "content": reading_text(card, cat, reversed=is_reversed),
        },
    }


def draw_cards(
    spread: str,
    category: str = "종합운",
    *,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    spread_key = normalize_spread(spread)
    cat = normalize_category(category)
    info = SPREADS[spread_key]
    count = info["count"]
    r = rng or random.Random()

    pool = deck_cards()
    if count > len(pool):
        raise ValueError(f"덱 {len(pool)}장보다 많이 뽑을 수 없습니다: {count}장")

    picked = r.sample(pool, count)
    cards_out = [
        card_response(
            c,
            cat,
            is_reversed=r.random() < REVERSED_PROBABILITY,
        )
        for c in picked
    ]

    return {
        "ok": True,
        "spread": spread_key,
        "spread_label": info["label"],
        "count": count,
        "category": cat,
        "cards": cards_out,
    }


def lookup_reading(
    card_id: str | int,
    category: str,
    *,
    reversed: bool = False,
) -> dict[str, Any]:
    card = card_by_id(card_id)
    return {
        "ok": True,
        "card": card_response(card, category, is_reversed=reversed),
    }


def reveal_card(
    card_id: str | int,
    category: str = "종합운",
    *,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """사용자가 고른 카드 1장 — 역방향 확률 적용 후 해석."""
    card = card_by_id(card_id)
    cat = normalize_category(category)
    r = rng or random.Random()
    is_reversed = r.random() < REVERSED_PROBABILITY
    return {
        "ok": True,
        "card": card_response(card, cat, is_reversed=is_reversed),
    }


def spreads_meta() -> dict[str, Any]:
    deck = load_deck()
    spreads_out: dict[str, Any] = {}
    for key, info in SPREADS.items():
        positions = SPREAD_POSITIONS.get(key, [])
        spreads_out[key] = {
            **info,
            "positions": positions,
        }
    return {
        "ok": True,
        "deck_name": deck.get("deck_name"),
        "card_count": deck.get("card_count"),
        "back_image_url": deck.get("back_image_url"),
        "reversed_probability": deck.get("reversed_probability", REVERSED_PROBABILITY),
        "reading_categories": list(READING_CATEGORIES),
        "spreads": spreads_out,
    }


def spread_reading(
    spread: str,
    cards: list[dict[str, Any]],
    category: str = "종합운",
) -> dict[str, Any]:
    """뽑은 순서대로 스프레드 스토리텔링 해석."""
    spread_key = normalize_spread(spread)
    cat = normalize_category(category)
    info = SPREADS[spread_key]
    expected = info["count"]
    if len(cards) != expected:
        raise ValueError(
            f"{info['label']}은(는) {expected}장이 필요합니다. (받음: {len(cards)}장)"
        )

    positions_meta = SPREAD_POSITIONS[spread_key]
    sections: list[dict[str, Any]] = []
    for i, entry in enumerate(cards):
        card = card_by_id(entry["card_id"])
        is_rev = bool(entry.get("is_reversed", False))
        pos = (
            positions_meta[i]
            if i < len(positions_meta)
            else {"label": str(i + 1), "role": "흐름"}
        )
        excerpt = reading_text(card, cat, reversed=is_rev)
        sections.append(
            {
                "position": i + 1,
                "position_label": pos["label"],
                "position_role": pos["role"],
                "card_id": card["id"],
                "name": card["name"],
                "keyword": card.get("keyword", ""),
                "element": card.get("element", ""),
                "category_kr": card.get("category_kr", ""),
                "is_reversed": is_rev,
                "orient": "역방향" if is_rev else "정방향",
                "image_url": card.get("image_url"),
                "excerpt": excerpt,
                "today_message": card.get("today_message", ""),
            }
        )

    narrative = tn.build_spread_story(spread_key, info["label"], cat, sections)

    return {
        "ok": True,
        "spread": spread_key,
        "spread_label": info["label"],
        "category": cat,
        "count": expected,
        "positions": sections,
        "opening": narrative["opening"],
        "narrative_sections": narrative["narrative_sections"],
        "narrative": narrative["narrative"],
        "synthesis": narrative["synthesis"],
        "closing": narrative["closing"],
    }
