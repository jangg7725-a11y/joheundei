# -*- coding: utf-8 -*-
"""타로 카드: zip +3 추출 후 카테고리 내 1칸 시프트(이미지 번호 ↔ 파일명 정렬)."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "static" / "tarot"
ARCHIVE = ROOT / "_archives"
CARDS = ROOT / "cards"
MANIFEST = ROOT / "manifest.json"

GLOBAL_OFFSET = 3

ZIP_CATEGORIES = [
    ("火", "fire", 10, 18),
    ("土", "earth", 19, 27),
    ("金", "metal", 28, 36),
    ("水", "water", 37, 45),
    ("천간", "stems", 46, 55),
    ("운명", "fate", 56, 60),
]

_WOOD_NUMERIC = tuple(f"{n}.png" for n in range(1, 7))


def _stem_num(name: str) -> int | None:
    stem = Path(name).stem
    if stem.isdigit():
        return int(stem)
    m = re.match(r"^(\d+)_", stem)
    return int(m.group(1)) if m else None


def _global_id(zip_num: int) -> int:
    return zip_num + GLOBAL_OFFSET


def _wood_sources(wood_dir: Path) -> list[tuple[int, Path]]:
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
    for offset, fname in enumerate(_WOOD_NUMERIC, start=4):
        p = wood_dir / fname
        if p.is_file():
            pairs.append((offset, p))
    if len(pairs) != 9:
        raise RuntimeError(f"木 9장 필요, 현재 {len(pairs)}")
    return pairs


def _find_wood_dir() -> Path:
    for base in (ARCHIVE, ROOT):
        if not base.is_dir():
            continue
        for d in base.iterdir():
            if d.is_dir() and ("04" in d.name or "木" in d.name):
                return d
    raise FileNotFoundError("04 木 폴더 없음")


def _find_zip(keyword: str) -> Path:
    for z in sorted(ARCHIVE.glob("*.zip")):
        if keyword in z.name:
            return z
    raise FileNotFoundError(f"zip 없음: {keyword}")


def _rebuild_wood() -> None:
    dest = CARDS / "wood"
    dest.mkdir(parents=True, exist_ok=True)
    for card_id, src in _wood_sources(_find_wood_dir()):
        shutil.copy2(src, dest / f"{card_id:02d}.png")


def _extract_zip(keyword: str, slug: str, glo_lo: int, glo_hi: int) -> None:
    zpath = _find_zip(keyword)
    dest_dir = CARDS / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zpath, "r") as zf:
        numbered: list[tuple[int, bytes]] = []
        unnamed: list[bytes] = []
        for entry in zf.namelist():
            if entry.endswith("/") or not entry.lower().endswith(".png"):
                continue
            num = _stem_num(entry)
            data = zf.read(entry)
            if num is not None:
                numbered.append((num, data))
            else:
                unnamed.append(data)

        written: dict[int, Path] = {}
        for zip_num, data in sorted(numbered, key=lambda x: x[0]):
            gid = _global_id(zip_num)
            if not (glo_lo <= gid <= glo_hi):
                continue
            target = dest_dir / f"{gid:02d}.png"
            target.write_bytes(data)
            written[gid] = target

        missing = [g for g in range(glo_lo, glo_hi + 1) if g not in written]
        if len(unnamed) != len(missing):
            raise RuntimeError(f"{slug}: 번호 없는 PNG {len(unnamed)}장, 빈 슬롯 {len(missing)}개")
        for data, gid in zip(unnamed, missing):
            target = dest_dir / f"{gid:02d}.png"
            target.write_bytes(data)
            written[gid] = target

        if len(written) != glo_hi - glo_lo + 1:
            raise RuntimeError(f"{slug}: {len(written)}장, 기대 {glo_hi - glo_lo + 1}장")


# zip+3 추출 직후, 카드 이미지 표기 번호 → 파일명 정렬 (土)
EARTH_REMAP: dict[int, int] = {
    19: 25,
    20: 26,
    21: 20,
    22: 21,
    23: 22,
    24: 23,
    25: 24,
    26: 19,
    27: 27,
}


# zip+3 추출 직후 47↔52 swap (을목·경금)
STEMS_REMAP: dict[int, int] = {47: 52, 52: 47}


def _apply_remap(slug: str, glo_lo: int, glo_hi: int, remap: dict[int, int]) -> None:
    folder = CARDS / slug
    tmp: dict[int, bytes] = {}
    for gid in range(glo_lo, glo_hi + 1):
        p = folder / f"{gid:02d}.png"
        tmp[gid] = p.read_bytes()
    for dest_id, src_id in remap.items():
        if not (glo_lo <= dest_id <= glo_hi and glo_lo <= src_id <= glo_hi):
            raise ValueError(f"{slug} remap {dest_id}←{src_id} 범위 밖")
        (folder / f"{dest_id:02d}.png").write_bytes(tmp[src_id])


def _shift_category(slug: str, glo_lo: int, glo_hi: int) -> None:
    """카테고리 내 1칸 앞으로: new[g]=old[g-1], new[lo]=old[hi] (이미지 표기 번호 정렬)."""
    folder = CARDS / slug
    ids = list(range(glo_lo, glo_hi + 1))
    tmp: dict[int, bytes] = {}
    for gid in ids:
        p = folder / f"{gid:02d}.png"
        if not p.is_file():
            raise FileNotFoundError(p)
        tmp[gid] = p.read_bytes()

    for gid in ids:
        src_id = gid - 1 if gid > glo_lo else glo_hi
        (folder / f"{gid:02d}.png").write_bytes(tmp[src_id])


def _load_labels() -> list[dict]:
    if MANIFEST.is_file():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if data.get("cards"):
            return data["cards"]
    raise RuntimeError("manifest.json 없음")


def main() -> None:
    _rebuild_wood()
    for keyword, slug, lo, hi in ZIP_CATEGORIES:
        _extract_zip(keyword, slug, lo, hi)
        if slug == "earth":
            _apply_remap(slug, lo, hi, EARTH_REMAP)
            print(f"{slug}: zip+{GLOBAL_OFFSET}, remap")
        elif slug == "stems":
            _apply_remap(slug, lo, hi, STEMS_REMAP)
            print(f"{slug}: zip+{GLOBAL_OFFSET}, 47↔52 swap")
        else:
            print(f"{slug}: zip+{GLOBAL_OFFSET}")

    cards = _load_labels()
    categories: dict[str, dict] = {}
    for row in cards:
        slug = row["category"]
        if slug not in categories:
            ids = [c["id"] for c in cards if c["category"] == slug]
            categories[slug] = {
                "kr": row["category_kr"],
                "range": f"{min(ids):02d}-{max(ids):02d}",
                "count": len(ids),
            }

    manifest = {
        "version": 3,
        "deck_name": "UNTEIM 오행·천간·운명 카드",
        "back_image": "back/back.png",
        "card_count": len(cards),
        "note": "zip 번호 +3 → 전역 번호. 土는 추가 remap. scripts/fix_tarot_numbering.py 참고.",
        "categories": categories,
        "cards": cards,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료: {len(cards)}장")


if __name__ == "__main__":
    main()
