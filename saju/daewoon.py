# -*- coding: utf-8 -*-
"""대운 — lunar_python Yun/DaYun 연동."""

from __future__ import annotations

from typing import Any, Dict, List


def compute_daewoon(eight_char: Any, gender_male: bool, *, sect: int = 1) -> Dict[str, Any]:
    yun = eight_char.getYun(1 if gender_male else 0, sect)

    rows: List[Dict[str, Any]] = []
    for d in yun.getDaYun():
        gz = d.getGanZhi()
        gz_val = gz if gz else ""
        row = {
            "index": d.getIndex(),
            "ganzhi": gz_val,
            "표시_간지": gz_val if len(gz_val) >= 2 else "〈대운 시작 전〉",
            "start_age": d.getStartAge(),
            "end_age": d.getEndAge(),
            "start_year": d.getStartYear(),
            "end_year": d.getEndYear(),
            "is_early_period": d.getIndex() < 1,
        }
        rows.append(row)

    start_solar = yun.getStartSolar()
    return {
        "forward": yun.isForward(),
        "gender": "남" if gender_male else "여",
        "start_solar": {
            "year": start_solar.getYear(),
            "month": start_solar.getMonth(),
            "day": start_solar.getDay(),
        },
        "start_year": yun.getStartYear(),
        "start_month": yun.getStartMonth(),
        "start_day": yun.getStartDay(),
        "start_hour": yun.getStartHour(),
        "cycles": rows,
    }
