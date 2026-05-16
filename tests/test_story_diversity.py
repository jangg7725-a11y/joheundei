# -*- coding: utf-8 -*-
"""원국 스토리텔링이 사주별로 분기되는지 다섯 명의 팔자로 검증한다."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set

import pytest

from saju import analysis as an


_SKIP_DUP_KEYS = frozenset(
    {
        "unteim_서사",
        "감정_상세",
        "일간_심리_상세",
        "unteim_보강",
        "unteim_일간심리",
        "unteim_감정",
        "meta",
        "_source",
        "_files_loaded",
        "_성별",
        "_참고_성별해석축",
    }
)


def _collect_strings(obj: Any, out: List[str]) -> None:
    if isinstance(obj, str):
        t = obj.strip()
        if t:
            out.append(t)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in _SKIP_DUP_KEYS:
                continue
            _collect_strings(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _collect_strings(v, out)


def _min_leaf_len(obj: Any, *, skip_keys: Set[str]) -> Iterable[int]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip_keys:
                continue
            if isinstance(v, str):
                yield len(v.strip())
            else:
                yield from _min_leaf_len(v, skip_keys=skip_keys)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _min_leaf_len(v, skip_keys=skip_keys)


CASES = [
    ("lunar", 1966, 11, 4, 2, 5, "female", False),
    ("solar", 1990, 3, 20, 14, 0, "male", False),
    ("solar", 1985, 7, 15, 8, 0, "female", False),
    ("solar", 2000, 12, 1, 22, 0, "male", False),
    ("solar", 1975, 9, 9, 6, 0, "female", False),
]


@pytest.mark.parametrize("case", CASES)
def test_story_pack_per_chart(case: tuple) -> None:
    cal, y, mo, d, h, mi, gender, leap = case
    r = an.build_report(
        calendar=cal,
        year=y,
        month=mo,
        day=d,
        hour=h,
        minute=mi,
        gender=gender,
        lunar_leap=leap,
    )
    story = r.get("원국_스토리텔링") or {}
    assert story, "원국_스토리텔링 블록이 있어야 합니다"

    core = story.get("사주_한줄_핵심", "")
    assert len(core) >= 100
    for gz in r["eight_char_string"].split():
        assert gz in core, f"한줄핵심에 팔자 글자 {gz}가 포함되어야 합니다: {core!r}"

    pers = story.get("성격_분석") or {}
    strengths = pers.get("장점_5") or []
    assert len(strengths) == 5
    for s in strengths:
        assert len(s) >= 100

    career = story.get("직업_적성") or {}
    top = career.get("최적_직군_TOP5") or []
    assert top
    for item in top:
        assert len(item.get("이유", "")) >= 100

    life = story.get("인생_전체_흐름") or {}
    for k, v in life.items():
        assert len(v.strip()) >= 100, f"{k} 구간이 100자 미만입니다"

    wealth = story.get("재물_패턴") or {}
    for k in ("버는_방식", "평생_재물_흐름", "부자_가능성_판정"):
        assert len(str(wealth.get(k, "")).strip()) >= 100

    health = story.get("건강_평생") or {}
    assert len(str(health.get("장수_가능성", "")).strip()) >= 100

    strings: List[str] = []
    _collect_strings(story, strings)
    dup = sorted({s for s in strings if strings.count(s) > 1 and len(s) > 40})
    assert not dup, f"동일 문장(40자 초과)이 반복됩니다: {dup[:3]}"


def test_five_charts_diverge() -> None:
    cores: List[str] = []
    strength_sets: List[Tuple[str, ...]] = []
    top_jobs: List[str] = []

    for case in CASES:
        cal, y, mo, d, h, mi, gender, leap = case
        r = an.build_report(
            calendar=cal,
            year=y,
            month=mo,
            day=d,
            hour=h,
            minute=mi,
            gender=gender,
            lunar_leap=leap,
        )
        story = r["원국_스토리텔링"]
        cores.append(story["사주_한줄_핵심"])
        strength_sets.append(tuple(story["성격_분석"]["장점_5"]))
        top_jobs.append(story["직업_적성"]["최적_직군_TOP5"][0]["직군"])

    assert len(set(cores)) == 5
    for i in range(5):
        for j in range(i + 1, 5):
            assert strength_sets[i] != strength_sets[j]
    assert len(set(top_jobs)) >= 4, f"직군 TOP1이 지나치게 겹칩니다: {top_jobs}"
