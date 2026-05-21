# -*- coding: utf-8 -*-
"""타로 덱 파일 구조·manifest.json 라벨 일괄 적용."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "static" / "tarot"
CARDS = ROOT / "cards"
BACK_DIR = ROOT / "back"
MANIFEST = ROOT / "manifest.json"

# (id, category_slug, category_kr, label_kr, label_en)
DECK: list[tuple[int, str, str, str, str]] = [
    # 木 wood
    (1, "wood", "木 오행", "씨앗", "Seed"),
    (2, "wood", "木 오행", "새싹", "Sprout"),
    (3, "wood", "木 오행", "나무", "Tree"),
    (4, "wood", "木 오행", "꽃", "Blossom"),
    (5, "wood", "木 오행", "열매", "Fruit"),
    (6, "wood", "木 오행", "뿌리", "Root"),
    (7, "wood", "木 오행", "바람", "Wind"),
    (8, "wood", "木 오행", "숲", "Forest"),
    (9, "wood", "木 오행", "봄비", "Spring Rain"),
    # 火 fire
    (10, "fire", "火 오행", "태양", "Sun"),
    (11, "fire", "火 오행", "촛불", "Candle"),
    (12, "fire", "火 오행", "불꽃", "Flame"),
    (13, "fire", "火 오행", "홍등", "Red Lantern"),
    (14, "fire", "火 오행", "노을", "Sunset"),
    (15, "fire", "火 오행", "번개", "Lightning"),
    (16, "fire", "火 오행", "달빛", "Moonlight"),
    (17, "fire", "火 오행", "모닥불", "Bonfire"),
    (18, "fire", "火 오행", "등불", "Lantern"),
    # 土 earth
    (19, "earth", "土 오행", "대지", "Earth"),
    (20, "earth", "土 오행", "산", "Mountain"),
    (21, "earth", "土 오행", "논밭", "Field"),
    (22, "earth", "土 오행", "황토", "Clay"),
    (23, "earth", "土 오행", "돌", "Stone"),
    (24, "earth", "土 오행", "집", "Home"),
    (25, "earth", "土 오행", "다리", "Bridge"),
    (26, "earth", "土 오행", "길", "Path"),
    (27, "earth", "土 오행", "우물", "Well"),
    # 金 metal
    (28, "metal", "金 오행", "검", "Sword"),
    (29, "metal", "金 오행", "보석", "Gem"),
    (30, "metal", "金 오행", "거울", "Mirror"),
    (31, "metal", "金 오행", "저울", "Scale"),
    (32, "metal", "金 오행", "종", "Bell"),
    (33, "metal", "金 오행", "열쇠", "Key"),
    (34, "metal", "金 오행", "방패", "Shield"),
    (35, "metal", "金 오행", "별", "Star"),
    (36, "metal", "金 오행", "왕관", "Crown"),
    # 水 water
    (37, "water", "水 오행", "강", "River"),
    (38, "water", "水 오행", "바다", "Ocean"),
    (39, "water", "水 오행", "이슬", "Dew"),
    (40, "water", "水 오행", "빗물", "Rain"),
    (41, "water", "水 오행", "안개", "Fog"),
    (42, "water", "水 오행", "얼음", "Ice"),
    (43, "water", "水 오행", "파도", "Wave"),
    (44, "water", "水 오행", "샘물", "Spring"),
    (45, "water", "水 오행", "달", "Moon"),
    # 천간 stems
    (46, "stems", "천간", "갑목", "甲木"),
    (47, "stems", "천간", "을목", "乙木"),
    (48, "stems", "천간", "병화", "丙火"),
    (49, "stems", "천간", "정화", "丁火"),
    (50, "stems", "천간", "무토", "戊土"),
    (51, "stems", "천간", "기토", "己土"),
    (52, "stems", "천간", "경금", "庚金"),
    (53, "stems", "천간", "신금", "辛金"),
    (54, "stems", "천간", "임수", "壬水"),
    (55, "stems", "천간", "계수", "癸水"),
    # 운명 fate
    (56, "fate", "운명", "충", "沖"),
    (57, "fate", "운명", "합", "合"),
    (58, "fate", "운명", "용신", "用神"),
    (59, "fate", "운명", "공망", "空亡"),
    (60, "fate", "운명", "대운", "大運"),
]

RENAME_DIRS = {
    "cheongan": "stems",
    "destiny": "fate",
}


def _find_png(card_id: int, slug: str) -> Path | None:
    fname = f"{card_id:02d}.png"
    candidates = [
        CARDS / slug / fname,
        CARDS / fname,
        CARDS / {"stems": "cheongan", "fate": "destiny"}.get(slug, slug) / fname,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def main() -> None:
    # 폴더명 변경
    for old, new in RENAME_DIRS.items():
        src, dst = CARDS / old, CARDS / new
        if src.is_dir() and not dst.exists():
            src.rename(dst)

    BACK_DIR.mkdir(parents=True, exist_ok=True)
    for back in (ROOT / "back.png", CARDS / "back.png"):
        if back.is_file():
            shutil.copy2(back, BACK_DIR / "back.png")
    if (ROOT / "back.png").is_file():
        (ROOT / "back.png").unlink()

    cards_out: list[dict] = []
    categories: dict[str, dict] = {}

    for cid, slug, cat_kr, label_kr, label_en in DECK:
        sub = CARDS / slug
        sub.mkdir(parents=True, exist_ok=True)
        dest = sub / f"{cid:02d}.png"
        src = _find_png(cid, slug)
        if src and src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        elif not dest.is_file():
            raise FileNotFoundError(f"카드 {cid:02d} PNG 없음: {dest}")

        rel = f"cards/{slug}/{cid:02d}.png"
        cards_out.append(
            {
                "id": cid,
                "file": rel,
                "filename": f"{cid:02d}.png",
                "category": slug,
                "category_kr": cat_kr,
                "label_kr": label_kr,
                "label_en": label_en,
                "title": f"{label_kr} {label_en}",
            }
        )
        if slug not in categories:
            ids = [x[0] for x in DECK if x[1] == slug]
            categories[slug] = {
                "kr": cat_kr,
                "range": f"{min(ids):02d}-{max(ids):02d}",
                "count": len(ids),
            }

    # cards/ 루트 flat png 제거
    for p in CARDS.glob("*.png"):
        p.unlink()

    # 빈 구폴더 정리
    for old in ("cheongan", "destiny"):
        d = CARDS / old
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    manifest = {
        "version": 3,
        "deck_name": "UNTEIM 오행·천간·운명 카드",
        "back_image": "back/back.png",
        "card_count": len(cards_out),
        "categories": categories,
        "cards": cards_out,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest v3: {len(cards_out)} cards, back={manifest['back_image']}")


if __name__ == "__main__":
    main()
