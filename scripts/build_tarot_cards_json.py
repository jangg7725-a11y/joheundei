# -*- coding: utf-8 -*-
"""saju/data/tarot/*.json + manifest → data/tarot_cards.json"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAROT_DATA = ROOT / "saju" / "data" / "tarot"
MANIFEST = ROOT / "static" / "tarot" / "manifest.json"
OUT = ROOT / "data" / "tarot_cards.json"

READING_CATEGORIES = [
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
]

SPREADS = {
    "today": {"label": "오늘의 타로", "count": 1},
    "week": {"label": "이주의 타로", "count": 3},
    "month": {"label": "이달의 타로", "count": 7},
    "year": {"label": "올해의 타로", "count": 12},
    "worry": {"label": "고민 타로", "count": 3},
    "love": {"label": "연애 타로", "count": 7},
    "deep": {"label": "심층 타로", "count": 10},
}


def main() -> None:
    index = json.loads((TAROT_DATA / "index.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    meta_by_id = {c["id"]: c for c in manifest["cards"]}

    cards: list[dict] = []
    for pack in index["packs"]:
        rows = json.loads((TAROT_DATA / pack["file"]).read_text(encoding="utf-8"))
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

    doc = {
        "version": 1,
        "deck_name": manifest.get("deck_name", "UNTEIM 타로"),
        "card_count": len(cards),
        "back_image_url": "/static/tarot/back/back.png",
        "reversed_probability": 0.3,
        "reading_categories": READING_CATEGORIES,
        "spreads": SPREADS,
        "cards": cards,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written {OUT} ({len(cards)} cards)")


if __name__ == "__main__":
    main()
