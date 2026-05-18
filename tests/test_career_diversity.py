# -*- coding: utf-8 -*-
"""직업 적성 — 사주별 TOP5 다양성·화(火) 직군 연결 검증."""

from __future__ import annotations

from saju import analysis as an

TEST_CASES = [
    ("solar", 1990, 3, 20, 14, 0, "male", False),
    ("solar", 1985, 6, 15, 8, 0, "female", False),
    ("solar", 1988, 8, 10, 12, 0, "male", False),
    ("solar", 1992, 11, 5, 18, 0, "female", False),
    ("lunar", 1966, 11, 4, 2, 5, "female", False),
    ("solar", 1975, 9, 9, 6, 0, "male", False),
    ("solar", 1980, 12, 1, 22, 0, "female", False),
    ("solar", 1983, 4, 20, 4, 0, "male", False),
    ("solar", 1972, 7, 7, 10, 0, "female", False),
    ("solar", 1969, 2, 14, 16, 0, "male", False),
]

FIRE_KEYWORDS = (
    "용접",
    "철강",
    "제철",
    "에너지",
    "요리",
    "전기",
    "화학",
    "조명",
    "금속",
    "주조",
    "플랜트",
    "방송",
    "미용",
)


def _build(cal: str, y: int, m: int, d: int, h: int, mi: int, gender: str, leap: bool):
    return an.build_report(
        calendar=cal,
        year=y,
        month=m,
        day=d,
        hour=h,
        minute=mi,
        gender=gender,
        lunar_leap=leap,
    )


def test_career_diversity() -> None:
    all_top1: list[str] = []
    for cal, y, m, d, h, mi, gender, leap in TEST_CASES:
        report = _build(cal, y, m, d, h, mi, gender, leap)
        career = report["원국_스토리텔링"]["직업_적성"]
        top5 = career["최적_직군_TOP5"]

        assert len(top5) >= 3, f"{y}-{m}-{d}: 직업 {len(top5)}개"
        assert career.get("직업_핵심_이유"), "직업_핵심_이유가 있어야 합니다"

        for job in top5:
            assert "여명 직업 해석" not in str(job)
            assert "여명" not in job.get("이유", "")
            reason = job.get("이유", "")
            assert len(reason) > 30, f"이유 너무 짧음: {reason}"

        all_top1.append(top5[0]["직군"])

    unique = len(set(all_top1))
    assert unique >= 6, f"직업 다양성 부족: {unique}가지 → {all_top1}"


def test_fire_jobs_specific() -> None:
    """화 용신·戊일간 등 — 화(열·에너지) 맥락 직군이 포함되는지."""
    fire_users = [
        ("lunar", 1966, 11, 4, 2, 5, "female", False),
        ("lunar", 1963, 2, 11, 12, 0, "male", False),
    ]
    for cal, y, m, d, h, mi, gender, leap in fire_users:
        report = _build(cal, y, m, d, h, mi, gender, leap)
        yong = report["yongsin"].get("용신_오행")
        career = report["원국_스토리텔링"]["직업_적성"]
        top5_str = str(career["최적_직군_TOP5"])
        if yong == "화":
            assert any(k in top5_str for k in FIRE_KEYWORDS), (
                f"화 용신인데 화 맥락 직업 없음: {top5_str}"
            )
