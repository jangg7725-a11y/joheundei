# -*- coding: utf-8 -*-
"""10 사주 None·핵심 빈값 스캔."""

from __future__ import annotations

from typing import Any, List

from tests.test_all_daymaster import TEST_CASES
from saju import analysis as an

SKIP_EMPTY_PREFIXES = (
    ".daewoon.cycles[0].ganzhi",
    ".unteim_서사.",
    ".chung_pa_hae.",
    ".분석_카테고리.",
    ".sinsal.공망_맞춤.",
)


def scan_nulls(obj: Any, path: str = "") -> List[str]:
    issues: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            issues += scan_nulls(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            issues += scan_nulls(v, f"{path}[{i}]")
    elif obj is None:
        issues.append(f"None: {path}")
    elif isinstance(obj, str) and not obj.strip():
        issues.append(f"빈값: {path}")
    return issues


def test_ten_charts_no_nulls_in_core() -> None:
    for case in TEST_CASES:
        cal, y, m, d, h, mi, gender = case
        r = an.build_report(
            calendar=cal,
            year=y,
            month=m,
            day=d,
            hour=h,
            minute=mi,
            gender=gender,
            lunar_leap=False,
        )
        issues = scan_nulls(r)
        none_issues = [i for i in issues if i.startswith("None")]
        assert not none_issues, "\n".join(none_issues[:15])
        empty = [i for i in issues if i.startswith("빈값")]
        bad = [
            i
            for i in empty
            if not any(i.endswith(s) or s in i for s in SKIP_EMPTY_PREFIXES)
            and ".보완법" not in i
            and ".부족한_글자" not in i
        ]
        assert not bad, f"{case}: " + "\n".join(bad[:10])
