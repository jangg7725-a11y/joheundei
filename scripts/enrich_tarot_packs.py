# -*- coding: utf-8 -*-
"""saju/data/tarot/*.json — keywords·core·temporal 보강 및 본문 톤 정리."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from saju.data.tarot.card_essence import essence_bundle  # noqa: E402
from saju.data.tarot.text_polish import (  # noqa: E402
    READING_CATEGORIES,
    parse_keywords,
    polish_meaning,
    polish_today_message,
)

TAROT_DATA = ROOT / "saju" / "data" / "tarot"


def enrich_card(row: dict) -> dict:
    cid = row["id"]
    name = row["name"]
    keyword = row.get("keyword", "")

    upright = dict(row.get("upright") or {})
    reverse = dict(row.get("reverse") or {})
    up_gen = upright.get("종합운", "")
    rev_gen = reverse.get("종합운", "")

    bundle = essence_bundle(cid, name, keyword, up_gen, rev_gen)
    keywords = bundle["keywords"] or parse_keywords(keyword)

    new_upright: dict[str, str] = {}
    new_reverse: dict[str, str] = {}
    for cat in READING_CATEGORIES:
        new_upright[cat] = polish_meaning(
            upright.get(cat, ""),
            category=cat,
            card_name=name,
            is_reversed=False,
        )
        new_reverse[cat] = polish_meaning(
            reverse.get(cat, ""),
            category=cat,
            card_name=name,
            is_reversed=True,
        )

    out = {
        **row,
        "db_version": 2,
        "keywords": keywords,
        "keyword": " · ".join(keywords) if keywords else keyword,
        "core": bundle["core"],
        "temporal": bundle["temporal"],
        "today_message": polish_today_message(row.get("today_message", "")),
        "upright": new_upright,
        "reverse": new_reverse,
    }
    return out


def main() -> None:
    index = json.loads((TAROT_DATA / "index.json").read_text(encoding="utf-8"))
    total = 0
    for pack in index["packs"]:
        path = TAROT_DATA / pack["file"]
        rows = json.loads(path.read_text(encoding="utf-8"))
        enriched = [enrich_card(r) for r in rows]
        path.write_text(
            json.dumps(enriched, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        total += len(enriched)
        print(f"enriched {path.name} ({len(enriched)} cards)")

    print(f"done: {total} cards (db_version=2)")


if __name__ == "__main__":
    main()
