# -*- coding: utf-8 -*-
from saju import saju_calc as sc

STEMS = list("甲乙丙丁戊己庚辛壬癸")
found = {s: None for s in STEMS}

for y in range(1970, 2001):
    for m in range(1, 13):
        for d in range(1, 29):
            try:
                raw = sc.compute_saju(
                    sc.BirthInput(
                        calendar="solar",
                        year=y,
                        month=m,
                        day=d,
                        hour=10,
                        minute=0,
                        lunar_leap=False,
                        gender="male",
                    )
                )
                dm = raw["day_master"]
                if dm in found and found[dm] is None:
                    found[dm] = (y, m, d)
            except Exception:
                pass
    if all(found.values()):
        break

lines = [f'{s}: ("solar", {t[0]}, {t[1]}, {t[2]}, 10, 0)' for s, t in found.items() if t]
open("scripts/_dm_dates.txt", "w", encoding="utf-8").write("\n".join(lines))
