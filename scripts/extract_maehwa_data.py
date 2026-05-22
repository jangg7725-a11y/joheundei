# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "saju" / "data" / "maehwa"
OUT.mkdir(parents=True, exist_ok=True)

HEX_RE = re.compile(
    r"'(\d-\d)':\{name:'([^']*)',hanja:'([^']*)',desc:'([^']*)'\}"
)
DONG_RE = re.compile(
    r"(\d):\{name:'([^']*)',pos:'([^']*)',desc:'([^']*)'\}"
)
G_RE = re.compile(
    r"(\d):\{sym:'([^']*)',name:'([^']*)',nat:'([^']*)',elemK:'([^']*)',ohaeng:(\d+),char:'([^']*)'\}"
)


def main() -> None:
    v2 = (ROOT / "maehwa_v2.html.html").read_text(encoding="utf-8")
    h64 = {
        m.group(1): {
            "name": m.group(2),
            "hanja": m.group(3),
            "desc": m.group(4),
        }
        for m in HEX_RE.finditer(v2)
    }
    (OUT / "hex64.json").write_text(
        json.dumps(h64, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("hex64", len(h64))

    dong = {
        int(m.group(1)): {
            "name": m.group(2),
            "pos": m.group(3),
            "desc": m.group(4),
        }
        for m in DONG_RE.finditer(v2)
    }
    (OUT / "dong_yao.json").write_text(
        json.dumps(dong, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("dong", len(dong))

    trigrams = {
        int(m.group(1)): {
            "sym": m.group(2),
            "name": m.group(3),
            "nat": m.group(4),
            "elemK": m.group(5),
            "ohaeng": int(m.group(6)),
            "char": m.group(7),
        }
        for m in G_RE.finditer(v2)
    }
    (OUT / "trigrams.json").write_text(
        json.dumps(trigrams, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("trigrams", len(trigrams))

    gl_m = re.search(r"const GL=\{(.+?)\};\s*const H64", v2, re.S)
    if gl_m:
        gl_raw = gl_m.group(1)
        lines = {}
        for m in re.finditer(r"(\d+):\[([01,]+)\]", gl_raw):
            lines[int(m.group(1))] = [int(x) for x in m.group(2).split(",")]
        (OUT / "trigram_lines.json").write_text(
            json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("lines", len(lines))

    # SURI from v1 - numeric keys
    v1 = (ROOT / "maehwa_yeoksu.html.html").read_text(encoding="utf-8")
    suri_block = re.search(r"const SURI = \{(.+?)\};\s*/\* ===== UI", v1, re.S)
    if suri_block:
        # parse each N: { ... } at top level only - use exec via simplified approach
        entries = re.findall(
            r"(\d+):\s*\{\s*name:\"([^\"]+)\",\s*kw:\"([^\"]+)\",\s*tags:\[(.*?)\],\s*char:\"([^\"]+)\"",
            suri_block.group(1),
            re.S,
        )
        suri = {}
        for num, name, kw, tags_raw, char in entries:
            tags = re.findall(r"\"([^\"]+)\"", tags_raw)
            suri[int(num)] = {
                "name": name,
                "kw": kw,
                "tags": tags,
                "char": char,
            }
        # aspects - optional second pass
        (OUT / "suri.json").write_text(
            json.dumps(suri, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("suri base", len(suri))


if __name__ == "__main__":
    main()
