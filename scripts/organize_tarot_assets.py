# -*- coding: utf-8 -*-
"""static/tarot zip·폴더 → cards/ + manifest.json 정리."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "static" / "tarot"
CARDS_DIR = ROOT / "cards"
ARCHIVE_DIR = ROOT / "_archives"
MANIFEST_PATH = ROOT / "manifest.json"

# 木 4~9: 폴더内 1.png~6.png (별도 생성 1~3번 이후 배치)
_WOOD_NUMERIC_FILES = tuple(f"{n}.png" for n in range(1, 7))

GLOBAL_OFFSET = 3

# (zip 키워드, slug, label, global_lo, global_hi)
ZIP_CATEGORY: list[tuple[str, str, str, int, int]] = [
    ("火", "fire", "火 오행", 10, 18),
    ("土", "earth", "土 오행", 19, 27),
    ("金", "metal", "金 오행", 28, 36),
    ("水", "water", "水 오행", 37, 45),
    ("천간", "stems", "천간", 46, 55),
    ("운명", "fate", "운명", 56, 60),
]


def _stem_num(name: str) -> int | None:
    stem = Path(name).stem
    if stem.isdigit():
        return int(stem)
    m = re.match(r"^(\d+)_", stem)
    return int(m.group(1)) if m else None


def _clear_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _global_id(zip_num: int) -> int:
    return zip_num + GLOBAL_OFFSET


def _wood_source_files(wood_dir: Path) -> list[tuple[int, Path]]:
    """04 木 폴더 9장 — 1~3: 이름 파일, 4~9: 1.png~6.png."""
    pairs: list[tuple[int, Path]] = []

    for card_id, name in ((1, "01_씨앗_木.png"), (2, "02_새싹_木.png")):
        p = wood_dir / name
        if p.is_file():
            pairs.append((card_id, p))

    sub = wood_dir / "03_나무_木"
    if sub.is_dir():
        subs = sorted(sub.glob("*.png"))
        if subs:
            pairs.append((3, subs[0]))

    for offset, fname in enumerate(_WOOD_NUMERIC_FILES, start=4):
        p = wood_dir / fname
        if p.is_file():
            pairs.append((offset, p))

    if len(pairs) != 9:
        found = [f"{gid}:{p.name}" for gid, p in pairs]
        raise RuntimeError(
            f"木 오행 PNG 9장 필요, 현재 {len(pairs)}장 ({wood_dir}): {found}"
        )
    return pairs


def _copy_wood_cards(wood_dir: Path, dest: Path) -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    for card_id, src in _wood_source_files(wood_dir):
        target = dest / f"{card_id:02d}.png"
        shutil.copy2(src, target)
        out.append((card_id, target))
    return out


def _extract_zip_mapped(
    zpath: Path, dest: Path, glo_lo: int, glo_hi: int
) -> list[tuple[int, int, Path]]:
    """zip 추출 → (zip번호, 전역번호, 경로)."""
    out: list[tuple[int, int, Path]] = []
    with zipfile.ZipFile(zpath, "r") as zf:
        numbered: dict[int, bytes] = {}
        unnamed: list[bytes] = []
        for entry in zf.namelist():
            if entry.endswith("/") or not entry.lower().endswith(".png"):
                continue
            num = _stem_num(entry)
            data = zf.read(entry)
            if num is not None:
                numbered[num] = data
            else:
                unnamed.append(data)

        written: set[int] = set()
        for zip_num, data in sorted(numbered.items()):
            gid = _global_id(zip_num)
            if not (glo_lo <= gid <= glo_hi):
                continue
            target = dest / f"{gid:02d}.png"
            target.write_bytes(data)
            written.add(gid)
            out.append((zip_num, gid, target))

        missing = [g for g in range(glo_lo, glo_hi + 1) if g not in written]
        if len(unnamed) != len(missing):
            raise RuntimeError(f"{zpath.name}: 번호 없는 PNG {len(unnamed)}장")

        for data, gid in zip(unnamed, missing):
            target = dest / f"{gid:02d}.png"
            target.write_bytes(data)
            out.append((0, gid, target))
    return out


def _zip_category(name: str) -> tuple[str, str, str, int, int] | None:
    for key, slug, label, lo, hi in ZIP_CATEGORY:
        if key in name:
            return slug, label, label, lo, hi
    return None


def _find_wood_dir() -> Path | None:
    for base in (ROOT, ARCHIVE_DIR):
        if not base.is_dir():
            continue
        for d in base.iterdir():
            if d.is_dir() and ("04" in d.name or "木" in d.name):
                return d
    return None


def _ensure_back_image() -> None:
    back_dir = ROOT / "back"
    back_dir.mkdir(parents=True, exist_ok=True)
    if (back_dir / "back.png").is_file():
        return
    for base in (ROOT, ARCHIVE_DIR):
        for p in base.glob("*.png"):
            if "뒷" in p.name or p.name.endswith("면.png"):
                shutil.copy2(p, back_dir / "back.png")
                return


def main() -> None:
    _clear_dir(CARDS_DIR)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_back_image()

    manifest_cards: list[dict] = []

    wood_src = _find_wood_dir()
    if not wood_src:
        raise FileNotFoundError("04 木 폴더를 찾을 수 없습니다 (_archives 확인).")

    wood_dest = CARDS_DIR / "wood"
    wood_dest.mkdir(parents=True, exist_ok=True)
    for num, path in _copy_wood_cards(wood_src, wood_dest):
        src_name = next((src.name for gid, src in _wood_source_files(wood_src) if gid == num), None)
        row = {
            "id": num,
            "file": f"cards/wood/{path.name}",
            "category": "wood",
            "category_kr": "木 오행",
        }
        if src_name:
            row["source_file"] = src_name
        manifest_cards.append(row)

    for zpath in sorted(ARCHIVE_DIR.glob("*.zip")):
        cat = _zip_category(zpath.name)
        if not cat:
            continue
        slug, label_kr, _, glo_lo, glo_hi = cat
        sub = CARDS_DIR / slug
        sub.mkdir(parents=True, exist_ok=True)
        for zip_num, gid, path in _extract_zip_mapped(zpath, sub, glo_lo, glo_hi):
            manifest_cards.append(
                {
                    "id": gid,
                    "zip_id": zip_num,
                    "file": f"cards/{slug}/{path.name}",
                    "category": slug,
                    "category_kr": label_kr,
                }
            )

    by_id = {row["id"]: row for row in manifest_cards}
    manifest_cards = [by_id[k] for k in sorted(by_id)]

    manifest = {
        "version": 2,
        "deck_name": "UNTEIM 오행·천간·운명 카드",
        "back_image": "back/back.png",
        "card_count": len(manifest_cards),
        "note": f"zip 번호 +{GLOBAL_OFFSET} → 전역 번호. apply_tarot_labels.py 실행 권장.",
        "categories": {
            "wood": {"kr": "木 오행", "range": "01-09", "count": 9},
            "fire": {"kr": "火 오행", "range": "10-18", "count": 9},
            "earth": {"kr": "土 오행", "range": "19-27", "count": 9},
            "metal": {"kr": "金 오행", "range": "28-36", "count": 9},
            "water": {"kr": "水 오행", "range": "37-45", "count": 9},
            "stems": {"kr": "천간", "range": "46-55", "count": 10},
            "fate": {"kr": "운명", "range": "56-60", "count": 5},
        },
        "cards": manifest_cards,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wood: 9, total: {len(manifest_cards)}")
    print("라벨 적용: python scripts/apply_tarot_labels.py")


if __name__ == "__main__":
    main()
