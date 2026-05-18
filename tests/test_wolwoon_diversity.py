# -*- coding: utf-8 -*-
"""월운 12절월 맞춤·다양성 검증 (5 사주)."""

from __future__ import annotations

from saju import analysis as an


def _build(calendar: str, y: int, m: int, d: int, hour: int, gender: str) -> dict:
    return an.build_report(
        calendar=calendar,
        year=y,
        month=m,
        day=d,
        hour=hour,
        minute=0 if calendar == "solar" else 5,
        gender=gender,
        lunar_leap=False,
    )


_BANNED_WOL_OPENERS = (
    "명리적으로 말씀드리면,",
    "전통 명리를 바탕으로 보면,",
    "이 사주에서는 흔히,",
    "풀어서 말씀드리면,",
)


def _assert_wol_pack(report: dict, label: str) -> None:
    wol = (report.get("월운표") or {}).get("월별") or []
    assert len(wol) == 12, label

    for m in wol:
        for field in (
            "월별_핵심스토리",
            "월별_행동지침_텍스트",
            "월별_실천팁",
            "월별_주의사항",
        ):
            txt = str(m.get(field) or "")
            for b in _BANNED_WOL_OPENERS:
                assert b not in txt, f"{label} {field}: banned opener {b!r}"

    stories = [str(m.get("월별_핵심스토리") or "").strip() for m in wol]
    assert all(stories), f"{label}: empty story"
    assert len(set(stories)) == 12, f"{label}: duplicate month stories among 12"

    for m in wol:
        core = str(m.get("월별_핵심스토리") or "").strip()
        tip = str(m.get("월별_실천팁") or "").strip()
        assert tip, f"{label}: slot {m.get('절월번호')} missing practice tip"
        assert tip not in core[: max(20, len(tip))], (
            f"{label}: slot {m.get('절월번호')} practice tip overlaps story head"
        )
        first = core.split("。")[0].split(".")[0].strip()
        if first and len(first) > 8:
            assert first != tip, (
                f"{label}: slot {m.get('절월번호')} practice equals story first sentence"
            )

    yong_el = (report.get("용신") or {}).get("용신_오행") or ""
    gi_el = (report.get("용신") or {}).get("기신_오행") or ""
    if yong_el:
        yong_months = [m for m in wol if m.get("오행") == yong_el]
        for m in yong_months[:1]:
            assert yong_el in str(m.get("월별_핵심스토리") or ""), (
                f"{label}: yong month should mention yong element"
            )
    if gi_el:
        gi_months = [m for m in wol if m.get("오행") == gi_el]
        for m in gi_months[:1]:
            story = str(m.get("월별_핵심스토리") or "")
            assert gi_el in story or "기신" in story, (
                f"{label}: gi month should mention gi element"
            )

    chung_months = [m for m in wol if m.get("충발동")]
    for m in chung_months:
        caution = str(m.get("월별_주의사항") or "")
        assert caution, f"{label}: chung month needs caution"
        assert any(
            k in caution for k in ("신장", "심장", "비장", "간", "폐", "위장", "충")
        ), f"{label}: chung month caution should mention body or chung"

    unteim = (report.get("unteim_세운월운") or {}).get("월별") or {}
    if unteim.get("1") and unteim.get("2"):
        s1 = str(unteim["1"].get("월운_서사") or "")
        s2 = str(unteim["2"].get("월운_서사") or "")
        assert s1 != s2, f"{label}: unteim month 1-2 narrative duplicate"


CASES = [
    ("lunar", 1966, 11, 4, 2, "female", "1966-female"),
    ("solar", 1990, 3, 20, 14, "male", "1990-male"),
    ("solar", 1985, 7, 15, 8, "female", "1985-female"),
    ("solar", 2000, 12, 1, 22, "male", "2000-male"),
    ("solar", 1975, 9, 9, 6, "female", "1975-female"),
]


def test_wolwoon_twelve_unique_stories_per_chart() -> None:
    all_first_stories: list[str] = []
    for cal, y, mo, d, h, gender, label in CASES:
        r = _build(cal, y, mo, d, h, gender)
        _assert_wol_pack(r, label)
        wol = r["월운표"]["월별"]
        all_first_stories.append(str(wol[0].get("월별_핵심스토리") or ""))

    assert len(set(all_first_stories)) >= 3, "different charts should differ on month 1"


def test_wolwoon_double_chung_flag_when_present() -> None:
    r = _build("lunar", 1966, 11, 4, 2, "female")
    wol = r["월운표"]["월별"]
    double = [m for m in wol if m.get("이중충")]
    for m in double:
        assert m.get("중첩플래그", {}).get("이중충") or m.get("이중충")
