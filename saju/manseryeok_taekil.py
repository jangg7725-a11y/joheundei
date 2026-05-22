# -*- coding: utf-8 -*-
"""만세력 일진 달력 원문 → 행사별 택일(擇日) 판정."""

from __future__ import annotations

import re
from typing import Any

from saju import manseryeok_display as msd

# 행사 유형 → 宜·忌 매칭 키워드 (한자·한글 혼용)
EVENT_RULES: dict[str, dict[str, list[str]]] = {
    "결혼": {
        "yi": ["結婚", "嫁娶", "會親友", "出行", "祈福", "沐浴"],
        "ji": ["行嫁", "行嫁娶", "造葬", "諸事不宜", "陰錯", "血池", "威池"],
        "label": "결혼·혼인",
    },
    "이사": {
        "yi": ["移徙", "移動", "動土上樓", "出行", "納財"],
        "ji": ["諸事不宜", "破土", "造葬", "交易"],
        "label": "이사·이전",
    },
    "제사": {
        "yi": ["祭祀", "祈福", "沐浴"],
        "ji": ["諸事不宜", "造葬", "行嫁"],
        "label": "제사·차례",
    },
    "장례": {
        "yi": ["安葬", "破土", "造葬"],
        "ji": ["諸事不宜", "結婚", "移徙", "開市"],
        "label": "장례·장례식",
    },
    "개업": {
        "yi": ["開市", "開倉庫", "納財", "造醫"],
        "ji": ["諸事不宜", "造葬", "破土"],
        "label": "개업·창업",
    },
    "건축": {
        "yi": ["破土", "動土", "動土上樓", "伐木", "裁種"],
        "ji": ["諸事不宜", "造葬", "結婚"],
        "label": "건축·착공",
    },
    "이장": {
        "yi": ["安葬", "移徙", "破土"],
        "ji": ["諸事不宜", "結婚", "開市"],
        "label": "이장·묘 이장",
    },
    "기도": {
        "yi": ["祈福", "祭祀", "沐浴", "造醫"],
        "ji": ["諸事不宜", "造葬"],
        "label": "기도·기원",
    },
    "택일": {
        "yi": ["祭祀", "祈福", "納財", "出行", "造醫", "沐浴"],
        "ji": ["諸事不宜", "造葬"],
        "label": "일반 택일",
    },
}

DAY_LINE_RE = re.compile(
    r"(?P<label>.+?日)\((?P<week>[日月火水金土])\)\s*"
    r"(?P<ganji>[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+"
    r"(?P<body>.+?)\s*宜(?P<yi>.+?)\s*忌\s*(?P<ji>.+)$"
)

AUSPICIOUS_MARKERS = ("母倉", "陰德", "天赦", "天赦日", "太陽到臨", "乙丙丁三奇", "三奇")
BAD_MARKERS = ("諸事不宜", "五黃", "破", "危")


def _split_tokens(blob: str) -> list[str]:
    """宜·忌 문장을 토큰 단위로 분리 (공백·연속 한자)."""
    blob = (blob or "").strip()
    if not blob:
        return []
    parts = re.split(r"\s+", blob)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > 12:
            out.extend(re.findall(r"[\u4e00-\u9fff]{2,4}", p))
        else:
            out.append(p)
    return out


def parse_calendar_days(original_text: str) -> list[dict[str, Any]]:
    """달력 원문에서 일별 일진·宜·忌 행 추출."""
    days: list[dict[str, Any]] = []
    if not original_text:
        return days
    for raw in original_text.splitlines():
        line = raw.strip()
        if "宜" not in line or "忌" not in line:
            continue
        m = DAY_LINE_RE.search(line)
        if not m:
            continue
        yi_raw = m.group("yi").strip()
        ji_raw = m.group("ji").strip()
        days.append(
            {
                "day_label": m.group("label"),
                "week_element": m.group("week"),
                "ganji": m.group("ganji"),
                "body": m.group("body").strip(),
                "yi_raw": yi_raw,
                "ji_raw": ji_raw,
                "yi_tokens": _split_tokens(yi_raw),
                "ji_tokens": _split_tokens(ji_raw),
                "line": line,
            }
        )
    return days


def score_day_for_event(day: dict[str, Any], event: str) -> dict[str, Any]:
    """행사 유형에 대한 택일 점수·등급."""
    rules = EVENT_RULES.get(event, EVENT_RULES["택일"])
    yi_hits: list[str] = []
    ji_hits: list[str] = []
    score = 0

    yi_blob = day.get("yi_raw", "")
    ji_blob = day.get("ji_raw", "")
    line = day.get("line", "")

    for kw in rules["yi"]:
        if kw in yi_blob or kw in line:
            yi_hits.append(kw)
            score += 12

    for kw in rules["ji"]:
        if kw in ji_blob or kw in line:
            ji_hits.append(kw)
            score -= 18

    if "諸事不宜" in ji_blob or "諸事不宜" in yi_blob:
        score -= 40
        ji_hits.append("諸事不宜")

    for mk in AUSPICIOUS_MARKERS:
        if mk in line:
            score += 4
    for mk in BAD_MARKERS:
        if mk in day.get("body", "") or mk in ji_blob:
            score -= 3

    if score >= 20:
        grade, verdict = "대길", "전통 만세력 기준 이 날은 해당 행사에 매우 유리합니다."
    elif score >= 8:
        grade, verdict = "길", "의(하기 좋음) 항목에 해당 행사가 있어 택일 후보로 좋습니다."
    elif score >= 0:
        grade, verdict = "평", "길·흉이 섞여 있으니 다른 날과 비교해 보세요."
    elif score >= -15:
        grade, verdict = "흉", "기(피할 것) 항목에 해당 행사가 있어 피하는 편이 낫습니다."
    else:
        grade, verdict = "대흉", "만사 길하지 않음(諸事不宜) 또는 강한 흉 요인이 있어 피하세요."

    return {
        "score": score,
        "grade": grade,
        "verdict": verdict,
        "yi_hits": yi_hits,
        "ji_hits": ji_hits,
        "event_label": rules["label"],
    }


def rank_days_for_event(
    calendar_items: list[dict[str, Any]],
    event: str,
    *,
    month: str = "",
    limit: int = 40,
) -> dict[str, Any]:
    """
    달력 DB 항목들에서 행사별 길일·흉일 목록 생성.
    ``calendar_items``: canonical_key 일진달력 또는 sub_category 달력 항목.
    """
    event = event if event in EVENT_RULES else "택일"
    ranked: list[dict[str, Any]] = []
    sources: list[dict[str, str]] = []

    for item in calendar_items:
        days = parse_calendar_days(item.get("original_text", ""))
        if not days:
            continue
        sources.append(
            {
                "id": item.get("id", ""),
                "chapter": item.get("chapter", ""),
                "month_hint": _month_hint(item, month),
            }
        )
        month_hint = _month_hint(item, month)
        for d in days:
            scored = score_day_for_event(d, event)
            row = {
                **d,
                **scored,
                "source_id": item.get("id"),
                "source_chapter": item.get("display_title")
                or item.get("sub_category")
                or item.get("chapter"),
                "calendar_month": month_hint,
            }
            ranked.append(msd.enrich_taekil_day(row, item, month_hint=month_hint))

    ranked.sort(key=lambda x: x["score"], reverse=True)
    good = [r for r in ranked if r["score"] >= 8][:limit]
    bad = sorted(
        [r for r in ranked if r["score"] < 0],
        key=lambda x: x["score"],
    )[: min(15, limit)]

    return {
        "event": event,
        "event_label": EVENT_RULES[event]["label"],
        "month_filter": month,
        "total_parsed_days": len(ranked),
        "good_days": good,
        "avoid_days": bad,
        "all_ranked": ranked[: limit * 2],
        "calendar_sources": sources,
    }


_CN_MONTH_NUM = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
}


def _cn_month_to_kr(token: str) -> str:
    token = (token or "").strip()
    if not token:
        return ""
    if token in _CN_MONTH_NUM:
        return f"{_CN_MONTH_NUM[token]}월"
    if token.endswith("月") and token[:-1] in _CN_MONTH_NUM:
        return f"{_CN_MONTH_NUM[token[:-1]]}월"
    if token.startswith("十") and len(token) > 1:
        rest = token[1:]
        if rest in _CN_MONTH_NUM:
            return f"{10 + _CN_MONTH_NUM[rest]}월"
    return ""


def _month_hint(item: dict[str, Any], month_filter: str = "") -> str:
    """양력 월 표기 (1월~12월). UI 월 필터가 있으면 우선."""
    if month_filter:
        return month_filter

    for kw in item.get("keywords") or []:
        if isinstance(kw, str) and re.fullmatch(r"(?:[1-9]|1[0-2])월", kw):
            return kw

    for key in (
        "modern_interpretation",
        "korean_translation",
        "embedding_text",
        "chapter",
    ):
        val = item.get(key) or ""
        m = re.search(r"양력\s*(\d{1,2})월", val)
        if m:
            return f"{m.group(1)}월"
        m = re.search(r"\d{4}년\s*(\d{1,2})월", val)
        if m:
            return f"{m.group(1)}월"

    ot_head = ((item.get("original_text") or "").split("\n", 1)[0]).strip()
    hm = re.search(r"^([一二三四五六七八九十]+)月", ot_head)
    if hm:
        mk = _cn_month_to_kr(hm.group(1))
        if mk:
            return mk

    ch = item.get("chapter") or ""
    hm = re.search(r"([一二三四五六七八九十]+)月", ch)
    if hm:
        mk = _cn_month_to_kr(hm.group(1))
        if mk:
            return mk

    for key in ("modern_interpretation", "korean_translation", "chapter"):
        val = item.get(key) or ""
        m = re.search(r"(\d{1,2})월", val)
        if m:
            return f"{m.group(1)}월"

    return ""


def related_theory_items(
    db: list[dict[str, Any]],
    event: str,
    *,
    limit: int = 6,
) -> list[dict[str, Any]]:
    """행사·택일 관련 고전 문헌 항목 (달력 제외)."""
    event = event if event in EVENT_RULES else "택일"
    cat_map = {
        "결혼": "혼인",
        "이사": "풍수",
        "장례": "풍수",
        "이장": "풍수",
        "제사": "제례",
        "개업": "기타",
        "건축": "풍수",
        "기도": "제례",
        "택일": "역법",
    }
    prefer_cat = cat_map.get(event, "역법")
    scored: list[tuple[int, dict]] = []

    for r in db:
        if r.get("canonical_key") == "일진달력":
            continue
        if "달력" in (r.get("sub_category") or ""):
            continue
        pr = r.get("practical") or {}
        events = pr.get("applicable_events") or []
        score = 0
        if event in events or "택일" in events:
            score += 5
        if r.get("category") == prefer_cat:
            score += 3
        if event in (r.get("keywords") or []):
            score += 2
        hay = " ".join(
            [
                r.get("chapter", ""),
                r.get("embedding_text", ""),
                r.get("modern_interpretation", ""),
            ]
        )
        for kw in EVENT_RULES[event]["yi"] + EVENT_RULES[event]["ji"][:3]:
            if kw in hay:
                score += 1
        if score > 0:
            scored.append((score, r))

    scored.sort(
        key=lambda x: (
            x[0],
            x[1].get("practical", {}).get("priority_rank", 0),
        ),
        reverse=True,
    )
    return [r for _, r in scored[:limit]]
