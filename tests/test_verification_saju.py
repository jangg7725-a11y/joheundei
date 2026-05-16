# -*- coding: utf-8 -*-
"""검증용 사주: 음력 1966-11-04 02:05 여성 → 丙午 庚子 戊申 癸丑"""

from __future__ import annotations

from saju import analysis
from saju import chung_pa_hae as cph
from saju import ohaeng as oh
from saju import sewoon as sw


def test_verification_solar_conversion(verification_raw) -> None:
    """음력 1966-11-04 → 양력 변환."""
    solar = verification_raw["solar"]
    lunar = verification_raw["lunar"]
    assert lunar["year"] == 1966 and lunar["month"] == 11 and lunar["day"] == 4
    assert solar["year"] == 1966 and solar["month"] == 12 and solar["day"] == 15
    assert solar["hour"] == 2 and solar["minute"] == 5


def test_verification_pillars(verification_raw) -> None:
    p = verification_raw["pillars"]
    assert p["year"]["pillar"] == "丙午", f"년주 오류: {p['year']['pillar']}"
    assert p["month"]["pillar"] == "庚子", f"월주 오류: {p['month']['pillar']}"
    assert p["day"]["pillar"] == "戊申", f"일주 오류: {p['day']['pillar']}"
    assert p["hour"]["pillar"] == "癸丑", f"시주 오류: {p['hour']['pillar']}"


def test_verification_day_master(verification_raw) -> None:
    assert verification_raw["day_master"] == "戊"
    assert verification_raw.get("eight_char_string") == "丙午 庚子 戊申 癸丑"


def test_verification_chung(verification_pillars) -> None:
    rel = cph.analyze_relations_full(verification_pillars)
    chungs = [r["글자"] for r in rel["원국_충"]]
    assert any("子" in c and "午" in c for c in chungs), f"子午충 미발견: {chungs}"


def test_verification_sewoon_2026(verification_raw) -> None:
    p = verification_raw["pillars"]
    dm = verification_raw["day_master"]
    counts = oh.count_elements(p, include_hidden=True)
    row = sw.analyze_sewoon_year(dm, p, "female", 2026, counts=counts)
    assert row["천간"] == "丙"
    assert row["지지"] == "午"
    assert row.get("간지") == "丙午"


def test_no_null_in_full_report() -> None:
    report = analysis.build_report(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
    )

    def scan_nulls(obj, path: str = "") -> list[str]:
        issues: list[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                issues += scan_nulls(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                issues += scan_nulls(v, f"{path}[{i}]")
        elif obj is None:
            issues.append(f"None 발견: {path}")
        elif isinstance(obj, str) and not obj.strip():
            issues.append(f"빈문자열: {path}")
        return issues

    issues = scan_nulls(report)
    none_issues = [i for i in issues if i.startswith("None")]
    assert not none_issues, "\n".join(none_issues[:20])

    # 핵심 키
    assert report["day_master"] == "戊"
    assert report["원국_스토리텔링"]["사주_한줄_핵심"]
    assert report["분석_카테고리"]
    assert report["pillars"]["day"]["pillar"] == "戊申"

    # 전체 리포트 빈문자열: 대운 첫 구간 ganzhi 등 일부 허용
    empty_issues = [i for i in issues if i.startswith("빈문자열")]
    allowed_empty = {".daewoon.cycles[0].ganzhi"}
    unexpected = [
        i
        for i in empty_issues
        if not any(i.endswith(s) for s in allowed_empty)
        and ".unteim_서사." not in i
    ]
    assert not unexpected, "\n".join(unexpected[:20])
