# -*- coding: utf-8 -*-
"""만세력 일진 달력 원문 → 행사별 택일(擇日) 판정."""

from __future__ import annotations

import re
from typing import Any

from saju import manseryeok_display as msd

# 행사 유형 → 宜·忌 매칭 키워드 (한자·한글 혼용)
DEFAULT_TAEKIL_EVENT = "결혼"

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
    rules = EVENT_RULES.get(event, EVENT_RULES[DEFAULT_TAEKIL_EVENT])
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
    event = event if event in EVENT_RULES else DEFAULT_TAEKIL_EVENT
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
    good = _pick_good_days(ranked, limit, month)
    bad = _pick_avoid_days(ranked, min(15, limit), month)

    payload: dict[str, Any] = {
        "event": event,
        "event_label": EVENT_RULES[event]["label"],
        "month_filter": month,
        "total_parsed_days": len(ranked),
        "good_days": good,
        "avoid_days": bad,
        "all_ranked": ranked[: limit * 2],
        "calendar_sources": sources,
    }
    if not month:
        payload["month_overview"] = summarize_taekil_by_month(ranked)
    return payload


SOLAR_MONTHS: tuple[str, ...] = tuple(f"{i}월" for i in range(1, 13))


def _month_sort_key(month: str) -> int:
    m = re.match(r"(\d{1,2})월", month or "")
    return int(m.group(1)) if m else 99


def _pick_good_days(
    ranked: list[dict[str, Any]],
    limit: int,
    month_filter: str = "",
) -> list[dict[str, Any]]:
    """길일 목록. 전체 월일 때는 달마다 골고루 노출(1월만 몰리는 현상 방지)."""
    candidates = [r for r in ranked if r.get("score", 0) >= 8]
    if month_filter:
        return candidates[:limit]

    by_month: dict[str, list[dict[str, Any]]] = {}
    for r in candidates:
        m = (r.get("calendar_month") or "").strip()
        if m:
            by_month.setdefault(m, []).append(r)
    if not by_month:
        return candidates[:limit]

    months = sorted(by_month.keys(), key=_month_sort_key)
    per_month = max(2, (limit + len(months) - 1) // len(months))
    picked: list[dict[str, Any]] = []
    for m in months:
        picked.extend(by_month[m][:per_month])

    if len(picked) < limit:
        seen = {id(x) for x in picked}
        for r in candidates:
            if len(picked) >= limit:
                break
            if id(r) not in seen:
                picked.append(r)
                seen.add(id(r))

    picked.sort(
        key=lambda x: (
            _month_sort_key(x.get("calendar_month") or ""),
            -int(x.get("score", 0)),
        )
    )
    return picked[:limit]


def _pick_avoid_days(
    ranked: list[dict[str, Any]],
    limit: int,
    month_filter: str = "",
) -> list[dict[str, Any]]:
    """흉일 목록. 전체 월일 때 월별로 골고루 노출."""
    candidates = sorted(
        [r for r in ranked if r.get("score", 0) < 0],
        key=lambda x: x.get("score", 0),
    )
    if month_filter:
        return candidates[:limit]

    by_month: dict[str, list[dict[str, Any]]] = {}
    for r in candidates:
        m = (r.get("calendar_month") or "").strip()
        if m:
            by_month.setdefault(m, []).append(r)
    if not by_month:
        return candidates[:limit]

    months = sorted(by_month.keys(), key=_month_sort_key)
    per_month = max(2, (limit + len(months) - 1) // len(months))
    picked: list[dict[str, Any]] = []
    for m in months:
        picked.extend(by_month[m][:per_month])

    if len(picked) < limit:
        seen = {id(x) for x in picked}
        for r in candidates:
            if len(picked) >= limit:
                break
            if id(r) not in seen:
                picked.append(r)
                seen.add(id(r))

    picked.sort(
        key=lambda x: (
            _month_sort_key(x.get("calendar_month") or ""),
            int(x.get("score", 0)),
        )
    )
    return picked[:limit]


def _month_rating(
    good_count: int,
    avoid_count: int,
    max_score: int,
    min_score: int,
) -> str:
    """월 단위 한눈에 보기용 등급."""
    if good_count >= 2 and max_score >= 20:
        return "매우 좋음"
    if good_count >= 1 and max_score >= 8:
        return "좋음"
    if avoid_count >= 3 or min_score <= -25:
        return "피하세요"
    if avoid_count >= 2 or min_score <= -15:
        return "주의"
    if good_count == 0 and avoid_count >= 1:
        return "주의"
    return "보통"


def _month_rating_class(rating: str) -> str:
    return {
        "매우 좋음": "best",
        "좋음": "good",
        "보통": "mid",
        "주의": "warn",
        "피하세요": "bad",
    }.get(rating, "empty")


def summarize_taekil_by_month(ranked: list[dict[str, Any]]) -> dict[str, Any]:
    """
    전체 월 택일 시 1~12월 길·흉을 한눈에 비교.
    DB에 달력이 있는 월만 has_data=True.
    """
    buckets: dict[str, list[dict[str, Any]]] = {m: [] for m in SOLAR_MONTHS}
    for r in ranked:
        cm = (r.get("calendar_month") or "").strip()
        if cm in buckets:
            buckets[cm].append(r)

    months_out: list[dict[str, Any]] = []
    for m in SOLAR_MONTHS:
        days = buckets[m]
        if not days:
            months_out.append(
                {
                    "month": m,
                    "has_data": False,
                    "day_count": 0,
                    "good_count": 0,
                    "avoid_count": 0,
                    "avg_score": 0,
                    "max_score": 0,
                    "min_score": 0,
                    "month_rating": "데이터 없음",
                    "rating_class": "empty",
                    "best_grade": "",
                    "best_day": "",
                    "worst_grade": "",
                    "worst_day": "",
                }
            )
            continue

        scores = [int(d.get("score", 0)) for d in days]
        good_list = [d for d in days if d.get("score", 0) >= 8]
        bad_list = [d for d in days if d.get("score", 0) < 0]
        best = max(days, key=lambda x: x.get("score", 0))
        worst = min(days, key=lambda x: x.get("score", 0))
        rating = _month_rating(
            len(good_list),
            len(bad_list),
            max(scores),
            min(scores),
        )
        months_out.append(
            {
                "month": m,
                "has_data": True,
                "day_count": len(days),
                "good_count": len(good_list),
                "avoid_count": len(bad_list),
                "avg_score": round(sum(scores) / len(scores), 1),
                "max_score": max(scores),
                "min_score": min(scores),
                "month_rating": rating,
                "rating_class": _month_rating_class(rating),
                "best_grade": best.get("grade") or "",
                "best_day": best.get("day_label_kr") or "",
                "worst_grade": worst.get("grade") or "",
                "worst_day": worst.get("day_label_kr") or "",
            }
        )

    with_data = [x for x in months_out if x["has_data"]]
    # 추천: 실제 길일(점수≥8)이 1일 이상인 달만
    good_months = [x for x in with_data if x["good_count"] >= 1]
    best_sorted = sorted(
        good_months,
        key=lambda x: (x["good_count"], x["max_score"], -x["avoid_count"]),
        reverse=True,
    )
    # 주의: 피할 날이 있는 달만
    avoid_months_data = [x for x in with_data if x["avoid_count"] >= 1]
    avoid_sorted = sorted(
        avoid_months_data,
        key=lambda x: (x["min_score"], -x["avoid_count"], -x["good_count"]),
    )

    return {
        "months": months_out,
        "best_months": [x["month"] for x in best_sorted[:3]],
        "avoid_months": [x["month"] for x in avoid_sorted[:3]],
        "summary_line": _overview_summary_line(best_sorted, avoid_sorted),
    }


def _overview_summary_line(
    best_sorted: list[dict[str, Any]],
    avoid_sorted: list[dict[str, Any]],
) -> str:
    parts: list[str] = []
    if best_sorted:
        top = best_sorted[0]
        parts.append(
            f"가장 좋은 달: {top['month']}({top['month_rating']}, 길일 {top['good_count']}일)"
        )
    if avoid_sorted:
        low = avoid_sorted[0]
        if low.get("avoid_count", 0) > 0 or low.get("min_score", 0) < 0:
            parts.append(
                f"가장 조심할 달: {low['month']}({low['month_rating']}, 피할 {low['avoid_count']}일)"
            )
    return " · ".join(parts) if parts else "월별 비교 데이터가 부족합니다."


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
    event = event if event in EVENT_RULES else DEFAULT_TAEKIL_EVENT
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
