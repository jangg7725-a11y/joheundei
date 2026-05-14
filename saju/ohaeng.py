# -*- coding: utf-8 -*-
"""오행 분포 분석."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List

from . import ganji as gj
from . import jijanggan as jj


def count_elements(pillars: dict, include_hidden: bool = True) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    order: List[str] = ["목", "화", "토", "금", "수"]

    for key in ("year", "month", "day", "hour"):
        p = pillars[key]
        counts[gj.element_of_stem(p["gan"])] += 1
        counts[gj.element_of_branch(p["zhi"])] += 1
        if include_hidden:
            for gan in jj.hidden_stems(p["zhi"]):
                counts[gj.element_of_stem(gan)] += 1

    return {e: counts.get(e, 0) for e in order}


def count_elements_surface(pillars: dict) -> Dict[str, int]:
    """천간·지지 표면 오행만 (지장간 제외). 주당 천간 1 + 지지 본기 1."""
    return count_elements(pillars, include_hidden=False)


def count_elements_hidden_only(pillars: dict) -> Dict[str, int]:
    """지장간(地支蔵干)에서 나오는 오행만."""
    counts: Counter[str] = Counter()
    order: List[str] = ["목", "화", "토", "금", "수"]
    for key in ("year", "month", "day", "hour"):
        p = pillars[key]
        for gan in jj.hidden_stems(p["zhi"]):
            counts[gj.element_of_stem(gan)] += 1
    return {e: counts.get(e, 0) for e in order}


def element_summary(counts: Dict[str, int]) -> List[str]:
    total = sum(counts.values()) or 1
    lines = []
    for name, v in counts.items():
        pct = round(100 * v / total, 1)
        lines.append(f"{name}: {v} ({pct}%)")
    return lines


def dominant_weak_elements(counts: Dict[str, int]) -> Dict[str, List[str]]:
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    dom = [items[0][0]] if items else []
    weak = [items[-1][0]] if items else []
    if items and items[0][1] == items[-1][1]:
        weak = []
    return {"strong": dom, "weak": weak}
