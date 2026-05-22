# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
v1 = (ROOT / "maehwa_yeoksu.html.html").read_text(encoding="utf-8")
block = re.search(r"const SURI = \{(.+?)\};\s*/\* ===== UI", v1, re.S).group(1)
suri_path = ROOT / "saju" / "data" / "maehwa" / "suri.json"
suri = json.loads(suri_path.read_text(encoding="utf-8"))

for n in range(1, 10):
    if n < 9:
        m = re.search(rf"{n}:\s*\{{(.+?)\n  \}},", block, re.S)
    else:
        m = re.search(rf"{n}:\s*\{{(.+?)\n  \}}\n\}};", block, re.S)
    if not m:
        m = re.search(rf"{n}:\s*\{{(.+?)\n  \d+:", block, re.S)
    if not m:
        continue
    chunk = m.group(1)
    aspects = [
        {"icon": a, "label": b, "text": c}
        for a, b, c in re.findall(
            r'\{icon:"([^"]+)",label:"([^"]+)",text:"([^"]+)"\}', chunk
        )
    ]
    key = str(n)
    if key in suri:
        suri[key]["aspects"] = aspects

suri_path.write_text(json.dumps(suri, ensure_ascii=False, indent=2), encoding="utf-8")
print("done", {k: len(v.get("aspects", [])) for k, v in suri.items()})
