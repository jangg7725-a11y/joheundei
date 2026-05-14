# -*- coding: utf-8 -*-
"""
일운(日運) — 양력 일자별 일진(日干日支)과 원국의 관계·길흉 참고.

일주 계산은 ``saju_calc``와 동일하게 **1900-01-01 = 甲戌日** 역산 규칙을 따릅니다.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import ganji as gj
from . import saju_calc as sc
from . import sewoon as sw
from . import sipsin as sp
from . import sinsal as sn
from .chung_pa_hae import CHEON_GAN_HAP_RESULT, ZHI_BODY
from .yongsin import RESOURCE_MAP

PILLAR_KEYS: Sequence[str] = ("year", "month", "day", "hour")

COLOR_GOOD = "green"
COLOR_BAD = "red"
COLOR_NEUTRAL = "white"

_WDAY_KR = ("월", "화", "수", "목", "금", "토", "일")

_DIRECTION_COMFORT = {"목": "동쪽", "화": "남쪽", "토": "중앙·낮은 산", "금": "서쪽", "수": "북쪽"}
_LUCK_COLOR_HINT = {
    "목": "청록·녹색 소품",
    "화": "연한 화색 포인트",
    "토": "베이지·황토 톤",
    "금": "백색·금속 액세서리",
    "수": "남색·검정 포인트",
}

# 일간 → 子時 천간 인덱스(0~9)
_DAY_ZI_STEM_IDX = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8}

_HOUR_GUIDES: Tuple[Tuple[str, str, str], ...] = (
    ("子", "23~01", "휴식·수면의 시간"),
    ("丑", "01~03", "조용히 마무리하기 좋은 시간"),
    ("寅", "03~05", "새벽 아이디어·기획에 유리"),
    ("卯", "05~07", "하루를 시작하기 좋은 시간"),
    ("辰", "07~09", "대인관계·약속 확인에 유의"),
    ("巳", "09~11", "집중력이 높아지기 쉬운 시간"),
    ("午", "11~13", "계약·미팅 타이밍(상황 따라 주의)"),
    ("未", "13~15", "오후 슬럼프·소화 리듬 유의"),
    ("申", "15~17", "실행·추진력을 쓰기 좋은 시간"),
    ("酉", "17~19", "정리·마감·회수에 유리"),
    ("戌", "19~21", "대면·식사 등 인간관계 시간"),
    ("亥", "21~23", "휴식·명상·다음날 계획"),
)


def _hour_stem_from_day_gan(day_gan: str, hour_zhi: str) -> str:
    zi0 = _DAY_ZI_STEM_IDX[day_gan]
    bi = gj.BRANCHES.index(hour_zhi)
    return gj.STEMS[(zi0 + bi) % 10]


def _clip(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _preview_emoji(tier: str) -> str:
    if tier == "좋은날":
        return "💚"
    if tier == "나쁜날":
        return "🔴"
    return "⚪"


def _hour_grade_word(score: float) -> str:
    if score >= 54:
        return "길"
    if score <= 43:
        return "흉"
    return "보통"


def _hour_slot_scores(
    day_master: str,
    pillars: dict,
    today_gan: str,
    today_zhi: str,
    day_score_base: int,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    blend = (day_score_base - 50) * 0.12

    for hz, tr, theme in _HOUR_GUIDES:
        hg = _hour_stem_from_day_gan(today_gan, hz)
        sip_h = sp.classify_sipsin(day_master, hg)

        h_score = 50.0 + blend
        if sw.branch_chong(today_zhi, hz):
            h_score -= 17
        if sw.branch_liu_he(today_zhi, hz):
            h_score += 12
        if sw.branch_hai(today_zhi, hz):
            h_score -= 7
        if sw.branch_po(today_zhi, hz):
            h_score -= 6

        for pk in PILLAR_KEYS:
            nz = pillars[pk]["zhi"]
            if sw.branch_chong(hz, nz):
                h_score -= 5
            if sw.branch_liu_he(hz, nz):
                h_score += 4
            if sw.branch_hai(hz, nz):
                h_score -= 3

        if sip_h in ("편인", "정인", "비견"):
            h_score += 5
        if sip_h in ("편관", "정관"):
            h_score -= 4
        if sip_h in ("편재", "정재"):
            h_score += 4
        if sip_h in ("식신", "상관"):
            h_score += 3

        grade = _hour_grade_word(h_score)
        line = theme
        if hz == "午":
            line = (
                "계약·미팅을 밀기 좋은 편입니다."
                if grade == "길"
                else ("계약·미팅은 조건 재확인·문서 검토를 권합니다." if grade == "흉" else theme + " 중간 타이밍으로 상황 보고 결정하세요.")
            )
        note = f"{hz}시({tr}) {grade} — {line}"

        out.append(
            {
                "시지": hz,
                "시간대": tr,
                "시주간지": hg + hz,
                "시간천간십신": sip_h,
                "테마": theme,
                "길흉": grade,
                "점수참고": round(h_score, 1),
                "한줄": note,
            }
        )
    return out


def _stem_day_notes(day_master: str, today_gan: str, pillars: dict) -> List[str]:
    notes: List[str] = []
    if today_gan != day_master:
        fs = frozenset((day_master, today_gan))
        if fs in CHEON_GAN_HAP_RESULT:
            elem = CHEON_GAN_HAP_RESULT[fs]
            notes.append(f"원국 일간과 오늘 일간 천간합 성향({elem})")
    lab = {"year": "년", "month": "월", "day": "일", "hour": "시"}
    for pk in PILLAR_KEYS:
        pg = pillars[pk]["gan"]
        if sw.stem_chong(today_gan, pg):
            notes.append(f"{lab[pk]}주 천간과 오늘 일간 천간충")
    return notes


def _today_detail_block(row: Dict[str, Any], day_master: str, pillars: dict) -> Dict[str, Any]:
    nat = row["원국과의관계"]
    bits = []
    for k in ("충", "파", "해", "형", "육합"):
        rows = nat.get(k) or []
        if rows:
            bits.append(f"{k} {len(rows)}건")
    rel_line = " · ".join(bits) if bits else "충파해형합 다발 패턴은 없습니다."
    sip_disp = ("비견(일간과 동일)"
                if row["일간대금일간십신"] == "일간"
                else row["일간대금일간십신"])
    story = (
        f"오늘 일진 {row['간지']}({row['간지한글']})은 원국 사주와 {rel_line} "
        f"일간 기준 십신은 「{sip_disp}」, 종합은 「{row['길흉등급']}」로 보입니다."
    )
    stem_notes = _stem_day_notes(day_master, row["일간"], pillars)
    return {
        "간지": row["간지"],
        "간지한글": row["간지한글"],
        "원국_충파해형합_요약": row["원국관계요약문자열"],
        "원국관계_설명": rel_line,
        "천간_원국_메모": stem_notes,
        "오늘의_십신": row["일간대금일간십신"],
        "길흉등급": row["길흉등급"],
        "길흉평가문장": row["한줄판정"],
        "내러티브": story.strip(),
    }


def _today_action_kit(day_master: str, pillars: dict, row: Dict[str, Any]) -> Dict[str, Any]:
    dm_el = gj.element_of_stem(day_master)
    luck_el = RESOURCE_MAP.get(dm_el, dm_el)
    direction = _DIRECTION_COMFORT.get(luck_el, "익숙한 방향")
    color = _LUCK_COLOR_HINT.get(luck_el, "차분한 단색")

    gi = gj.stem_index(day_master)
    zi = gj.BRANCHES.index(pillars["day"]["zhi"])
    tg_i = gj.stem_index(row["일간"])
    tz_i = gj.BRANCHES.index(row["일지"])
    nums = sorted({((gi + 1) % 9) + 1, ((zi + 3) % 9) + 1, ((tg_i + tz_i) % 9) + 1})

    good: List[str] = ["짧은 산책", "물 마시기·스트레칭", "우선순위 3개만 적기"]
    bad: List[str] = ["충동 카드결제", "과음·야근 연속"]
    if row["길흉등급"] == "좋은날":
        good.extend(["중요 미팅·제안", "학습·창작 착수"])
    elif row["길흉등급"] == "나쁜날":
        bad.extend(["대형 계약 서명", "수술·이사 일정(급하지 않다면 조정)"])
        good.insert(0, "수면 확보·건강 우선")
    else:
        good.append("연락·정리 위주 업무")

    spec = row.get("특별흉") or {}
    if spec.get("일지충"):
        bad.append("배우자·동료와 각 세워 두기")
    if spec.get("백호살"):
        bad.append("날카로운 도구·교통 급가속 주의")

    return {
        "하면_좋은_일": good[:8],
        "피해야_할_일": bad[:8],
        "행운_방향": direction,
        "행운_색상": color,
        "행운_숫자": nums,
    }


def _calendar_markers(row: Dict[str, Any]) -> Dict[str, Any]:
    sg = row.get("특별길") or {}
    sb = row.get("특별흉") or {}
    good_tags: List[str] = []
    bad_tags: List[str] = []
    if sg.get("천을귀인"):
        good_tags.append("⭐천을귀인")
    if sg.get("삼합완성"):
        good_tags.append("⭐삼합")
    if sg.get("일간천간합"):
        good_tags.append("⭐천간합")
    if sb.get("일지충"):
        bad_tags.append("⚠충")
    if sb.get("백호살"):
        bad_tags.append("⚠백호")
    if sb.get("공망"):
        bad_tags.append("⚠공망")
    return {"길표시": good_tags, "흉경고": bad_tags}


def _xing_pair(a: str, b: str) -> Optional[str]:
    if a == b and a in gj.XING_ZI_BRANCHES:
        return "자형"
    pair = {a, b}
    if pair <= gj.XING_SAN_INSAM and len(pair) == 2:
        return "인사신 삼형"
    if pair <= gj.XING_SAN_GOJI and len(pair) == 2:
        return "축술미 삼형"
    if pair == gj.XING_SANG_JAMYO:
        return "자묘 상형"
    return None


def daily_pillar_for_date(year: int, month: int, day: int) -> Dict[str, Any]:
    """양력 연·월·일의 일간·일지(일진)."""
    gi, zi = sc._day_gan_zhi_indices(year, month, day)
    gan = gj.STEMS[gi]
    zhi = gj.BRANCHES[zi]
    pillar = gan + zhi
    wd = date(year, month, day).weekday()
    return {
        "연": year,
        "월": month,
        "일": day,
        "요일번호": wd,
        "요일한글": _WDAY_KR[wd],
        "양력문자열": f"{year:04d}-{month:02d}-{day:02d}",
        "간지": pillar,
        "일간": gan,
        "일지": zhi,
        "간지한글": gj.pillar_label_kr(gan, zhi),
        "일간오행": gj.element_of_stem(gan),
        "일지오행": gj.element_of_branch(zhi),
        "낭음": gj.nayin_for_pillar(pillar),
    }


def _native_day_relations(today_zhi: str, pillars: dict) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {"충": [], "파": [], "해": [], "형": [], "육합": []}
    for pk in PILLAR_KEYS:
        nz = pillars[pk]["zhi"]
        pos = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}[pk]
        lab = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}[pk]
        body = ZHI_BODY.get(nz, "")
        if sw.branch_chong(today_zhi, nz):
            out["충"].append({"궁": pk, "주": lab, "위치": pos, "글자": f"{today_zhi}{nz}", "신체": body})
        if sw.branch_po(today_zhi, nz):
            out["파"].append({"궁": pk, "주": lab, "위치": pos, "글자": f"{today_zhi}×{nz}", "신체": body})
        if sw.branch_hai(today_zhi, nz):
            out["해"].append({"궁": pk, "주": lab, "위치": pos, "글자": f"{today_zhi}×{nz}", "신체": body})
        xt = _xing_pair(today_zhi, nz)
        if xt:
            out["형"].append({"궁": pk, "주": lab, "위치": pos, "유형": xt, "글자": f"{today_zhi}{nz}", "신체": body})
        if sw.branch_liu_he(today_zhi, nz):
            out["육합"].append({"궁": pk, "주": lab, "위치": pos, "글자": f"{today_zhi}{nz}", "신체": body})
    return out


def _native_zhis(pillars: dict) -> Set[str]:
    return {pillars[pk]["zhi"] for pk in PILLAR_KEYS}


def _sanhap_completion_day(native_zhis: Set[str], today_zhi: str) -> Tuple[bool, Optional[str]]:
    """원국에 삼합 중 두 지만 깔린 날, 오늘 일지가 나머지 한 지를 채울 때만 참."""
    for tri, label in gj.SAN_HE_GROUPS:
        if today_zhi not in tri:
            continue
        if len(tri & native_zhis) != 2:
            continue
        if tri <= native_zhis | {today_zhi}:
            return True, label
    return False, None


def _stem_hap_with_dm(dm: str, today_gan: str) -> bool:
    if dm == today_gan:
        return False
    return frozenset((dm, today_gan)) in CHEON_GAN_HAP_RESULT


def _baekho_hit(native_year_zhi: str, today_zhi: str) -> bool:
    bh = sn._baekho_zhi(native_year_zhi)  # type: ignore[attr-defined]
    if not bh:
        return False
    return today_zhi == bh or sw.branch_chong(today_zhi, bh)


def _kongwang_hit(native_day_pillar: str, today_zhi: str) -> bool:
    k1, k2 = sn._xunkong_for_pillar(native_day_pillar)  # type: ignore[attr-defined]
    return today_zhi in {k1, k2}


def analyze_ilwoon_day(
    day_master: str,
    pillars: dict,
    year: int,
    month: int,
    day: int,
    *,
    extended: bool = False,
) -> Dict[str, Any]:
    """
    특정 양력 일자 일운 분석.

    ``pillars``, ``day_master``는 원국 사주.
    ``extended=True``이면 오늘 한정 확장 필드(시간대별·추천행동·상세 블록)를 포함합니다.
    """
    dp = daily_pillar_for_date(year, month, day)
    tg, tz = dp["일간"], dp["일지"]
    nat_rel = _native_day_relations(tz, pillars)
    nzhs = _native_zhis(pillars)

    ce_ok = tz in sn._cheoneul(day_master)  # type: ignore[attr-defined]
    san_ok, san_label = _sanhap_completion_day(nzhs, tz)
    hap_ok = _stem_hap_with_dm(day_master, tg)
    day_chong = sw.branch_chong(tz, pillars["day"]["zhi"])
    bh_ok = _baekho_hit(pillars["year"]["zhi"], tz)
    kong_ok = _kongwang_hit(pillars["day"]["pillar"], tz)

    sip_today_gan = sp.classify_sipsin(day_master, tg)

    score = 50
    if ce_ok:
        score += 14
    if san_ok:
        score += 12
    if hap_ok:
        score += 10
    if nat_rel["육합"]:
        score += 6
    if day_chong:
        score -= 20
    if bh_ok:
        score -= 14
    if kong_ok:
        score -= 12
    score -= 6 * len(nat_rel["충"])
    score -= 4 * len(nat_rel["파"])
    score -= 4 * len(nat_rel["해"])
    score -= 5 * len(nat_rel["형"])

    special_good = {"천을귀인": ce_ok, "삼합완성": san_ok, "일간천간합": hap_ok}
    special_bad = {"일지충": day_chong, "백호살": bh_ok, "공망": kong_ok}

    if score >= 62:
        tier, color = "좋은날", COLOR_GOOD
    elif score <= 38:
        tier, color = "나쁜날", COLOR_BAD
    else:
        tier, color = "보통", COLOR_NEUTRAL

    bits = []
    if ce_ok:
        bits.append("천을귀인 지지")
    if san_ok:
        bits.append(f"{san_label} 삼합 성취")
    if hap_ok:
        bits.append("일간 천간합")
    if day_chong:
        bits.append("일지충")
    if bh_ok:
        bits.append("백호 연계")
    if kong_ok:
        bits.append("일주 공망 지지")

    # "일간"은 dm==tg(비견) 케이스의 내부 마커 → 사용자에게 보이는 레이블은 "비견(일간과 동일)"
    sip_label = "비견(일간과 동일)" if sip_today_gan == "일간" else sip_today_gan

    if tier == "좋은날":
        verdict = "길한 편 — " + (" · ".join(bits) if bits else "충형 부담 적음.")
    elif tier == "나쁜날":
        verdict = "각별 주의 — " + (" · ".join(bits) if bits else "충·형 부담 확인.")
    else:
        verdict = "무난 — 일진 십신 " + sip_label + (" · " + " · ".join(bits) if bits else "")

    markers_payload = {"특별길": special_good, "특별흉": special_bad}
    row: Dict[str, Any] = {
        **dp,
        "원국과의관계": nat_rel,
        "원국관계요약문자열": _relations_summary(nat_rel),
        "일간대금일간십신": sip_today_gan,
        "점수참고": score,
        "길흉등급": tier,
        "표시색": color,
        "표시색한글": {"green": "초록", "red": "빨강", "white": "흰색"}[color],
        "한줄판정": verdict.strip(),
        "특별길": special_good,
        "특별흉": special_bad,
        "달력_표시": _calendar_markers(markers_payload),
    }
    if extended:
        row["오늘_일진_상세"] = _today_detail_block(row, day_master, pillars)
        row["시간대별_운세"] = _hour_slot_scores(day_master, pillars, tg, tz, score)
        row["오늘_추천행동"] = _today_action_kit(day_master, pillars, row)
    return row


def _relations_summary(rel: Dict[str, List[Any]]) -> str:
    parts = []
    for key in ("충", "파", "해", "형", "육합"):
        rows = rel.get(key) or []
        if rows:
            parts.append(f"{key}{len(rows)}")
    return " · ".join(parts) if parts else "충파해형합 특이 없음"


def ilwoon_week_pack(
    day_master: str,
    pillars: dict,
    *,
    reference_date: Optional[date] = None,
) -> Dict[str, Any]:
    """월요일 시작으로 이번 주 7일 일운."""
    ref = reference_date or date.today()
    monday = ref - timedelta(days=ref.weekday())
    days = [
        analyze_ilwoon_day(day_master, pillars, *(monday + timedelta(days=i)).timetuple()[:3])
        for i in range(7)
    ]
    for d in days:
        d["미리보기"] = {
            "이모지등급": _preview_emoji(d["길흉등급"]),
            "핵심한마디": _clip(d["한줄판정"], 52),
        }
    return {
        "기준주_월요일": monday.isoformat(),
        "기준일": ref.isoformat(),
        "일자별": days,
        "출력_주간표텍스트": _format_week_ascii(days),
    }


def _format_week_ascii(rows: List[Dict[str, Any]]) -> str:
    lines = ["일진 주간표 (월~일):"]
    sym = {"green": "[길]", "red": "[흉]", "white": "[보통]"}
    for r in rows:
        lines.append(
            f"  {r['양력문자열']}({r['요일한글']}) {r['간지']} {sym[r['표시색']]} — {r['원국관계요약문자열']}"
        )
    return "\n".join(lines)


def ilwoon_month_pack(
    day_master: str,
    pillars: dict,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """해당 월 전체 일진·달력 격자·특별 길일·흉일 목록."""
    last = calendar.monthrange(year, month)[1]
    flat = [analyze_ilwoon_day(day_master, pillars, year, month, d) for d in range(1, last + 1)]

    good_dates: List[str] = []
    bad_dates: List[str] = []
    cheoneul_dates: List[str] = []
    san_dates: List[str] = []
    hap_dates: List[str] = []
    day_chong_dates: List[str] = []
    baekho_dates: List[str] = []
    kong_dates: List[str] = []

    for r in flat:
        iso = r["양력문자열"]
        if r["표시색"] == COLOR_GOOD:
            good_dates.append(iso)
        elif r["표시색"] == COLOR_BAD:
            bad_dates.append(iso)
        if r["특별길"]["천을귀인"]:
            cheoneul_dates.append(iso)
        if r["특별길"]["삼합완성"]:
            san_dates.append(iso)
        if r["특별길"]["일간천간합"]:
            hap_dates.append(iso)
        if r["특별흉"]["일지충"]:
            day_chong_dates.append(iso)
        if r["특별흉"]["백호살"]:
            baekho_dates.append(iso)
        if r["특별흉"]["공망"]:
            kong_dates.append(iso)

    grid = _month_calendar_grid_from_flat(year, month, flat)

    return {
        "연": year,
        "월": month,
        "말일": last,
        "일별전체": flat,
        "달력": grid,
        "좋은날목록": good_dates,
        "나쁜날목록": bad_dates,
        "특별길일": {
            "천을귀인일": cheoneul_dates,
            "삼합완성일": san_dates,
            "일간천간합일": hap_dates,
        },
        "특별흉일": {
            "일지충일": day_chong_dates,
            "백호살일": baekho_dates,
            "공망일": kong_dates,
        },
        "달력_ASCII": _format_month_ascii(grid),
    }


def _month_calendar_grid_from_flat(year: int, month: int, flat: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    by_dom = {r["일"]: r for r in flat}
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    grid: List[List[Dict[str, Any]]] = []
    for week in cal.monthdatescalendar(year, month):
        row: List[Dict[str, Any]] = []
        for dt in week:
            if dt.month != month:
                row.append({"패딩": True, "날짜": dt.isoformat(), "월": dt.month})
                continue
            cell = dict(by_dom[dt.day])
            cell["패딩"] = False
            row.append(cell)
        grid.append(row)
    return grid


_EMO = {"green": "🟩", "red": "🟥", "white": "⬜"}


def _format_month_ascii(grid: List[List[Dict[str, Any]]]) -> str:
    header = "월   화   수   목   금   토   일"
    lines = [header]
    for week in grid:
        cells = []
        for c in week:
            if c.get("패딩"):
                cells.append(" · ")
            else:
                dom = int(c["일"])
                cells.append(f"{_EMO[c['표시색']]}{dom:02d}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def ilwoon_snapshot_pack(
    day_master: str,
    pillars: dict,
    *,
    reference_date: Optional[date] = None,
) -> Dict[str, Any]:
    """오늘·이번 주·이번 달 묶음 (리포트용). 오늘은 시간대별·추천행동 확장 포함."""
    ref = reference_date or date.today()
    today = analyze_ilwoon_day(day_master, pillars, ref.year, ref.month, ref.day, extended=True)
    week = ilwoon_week_pack(day_master, pillars, reference_date=ref)
    month = ilwoon_month_pack(day_master, pillars, ref.year, ref.month)
    return {
        "기준일": ref.isoformat(),
        "오늘": today,
        "이번주": week,
        "이번달": month,
        "안내": "달력: 초록=길일 성향, 빨강=흉일 성향, 흰색=보통. ⭐=천을·삼합·천간합 등 특별 길일, ⚠=충·백호·공망 (규칙 기반 참고).",
    }
