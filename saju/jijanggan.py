# -*- coding: utf-8 -*-
"""지장간(地支蔵干) 추출."""

from __future__ import annotations

from typing import Dict, List

from . import ganji as gj


def hidden_stems(zhi: str) -> List[str]:
    return gj.jijanggan_ordered(zhi)


def pillar_hidden_detail(zhi: str) -> List[dict]:
    result = []
    for gan in hidden_stems(zhi):
        result.append(
            {
                "gan": gan,
                "element": gj.element_of_stem(gan),
                "kr": gj.STEM_KR[gj.stem_index(gan)],
            }
        )
    return result


def all_hidden_for_pillars(pillars: dict) -> dict:
    """pillars: year/month/day/time 각각 gan, zhi 키 포함."""
    out = {}
    for key in ("year", "month", "day", "hour"):
        p = pillars[key]
        zhi = p["zhi"]
        out[key] = {
            "zhi": zhi,
            "zhi_kr": gj.BRANCH_KR[gj.branch_index(zhi)],
            "hidden": pillar_hidden_detail(zhi),
        }
    return out
