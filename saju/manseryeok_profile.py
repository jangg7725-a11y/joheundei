# -*- coding: utf-8 -*-
"""만세력 단독 페이지 — 사주 계산 결과 → 문헌 매칭 파라미터."""

from __future__ import annotations

from typing import Any

from . import ganji as gj
from . import ilwoon as il
from . import jijanggan as jj
from . import manseryeok_fortune as mfort
from . import ohaeng as oh
from . import saju_calc as sc
from . import sibiunsung as sibi_mod
from . import sinsal as sn
from . import sipsin as sp
from . import yongsin as ys

PILLAR_KEYS = ("year", "month", "day", "hour")
PILLAR_LABEL = {"year": "년", "month": "월", "day": "일", "hour": "시"}
# 화면 배열: 좌→우 시·일·월·년 (우측이 년주, K사주마당 품 원국 탭과 동일)
WONGUK_DISPLAY_ORDER = ("hour", "day", "month", "year")

MATCH_SINSAL_NAMES = (
    "역마살",
    "도화살",
    "괴강살",
    "공망",
    "겁살",
    "원진살",
    "고과살",
    "태양도림",
    "삼재",
    "백호살",
    "양인살",
)

MATCH_GYEOK_SUFFIX = "격"

# 월간 십신이 식신일 때 카테고리 정렬·가중 (낮을수록 우선)
_CATEGORY_RANK_SIKSHIN = {
    "명리": 0,
    "역법": 1,
    "길흉": 2,
    "풍수": 3,
    "제례": 4,
    "기타": 5,
    "혼인": 9,
}


def score_manseryeok_item(
    item: dict[str, Any],
    match_params: dict[str, str],
) -> int:
    """문헌 1건 매칭 점수. 식신이면 혼인 감점·명리·역법 가점."""
    mc = item.get("match_conditions", {})
    mp = match_params
    score = 0

    if mp.get("shinsin") and mp["shinsin"] in mc.get("십신", []):
        score += 3
    if mp.get("sinsal") and mp["sinsal"] in mc.get("신살", []):
        score += 3
    if mp.get("gyeokguk") and mp["gyeokguk"] in mc.get("격국", []):
        score += 2
    if mp.get("ohaeng") and mp["ohaeng"] in mc.get("five_elements", []):
        score += 1

    if mp.get("shinsin") == "식신":
        cat = item.get("category") or ""
        if cat == "혼인":
            score -= 2
        elif cat in ("명리", "역법"):
            score += 2

    return score


def _match_sort_key(item: dict[str, Any], shinsin: str) -> tuple:
    """정렬: 점수 → (식신 시) 명리·역법 우선 → priority_rank."""
    cat = item.get("category") or ""
    if shinsin == "식신":
        cat_rank = _CATEGORY_RANK_SIKSHIN.get(cat, 6)
    else:
        cat_rank = 0
    pr = item.get("practical", {}).get("priority_rank", 0) or 0
    return (item.get("_match_score", 0), -cat_rank, pr)


def rank_manseryeok_matches(
    db: list[dict[str, Any]],
    match_params: dict[str, str],
    *,
    limit: int = 12,
) -> tuple[list[dict[str, Any]], int]:
    """전체 DB에서 매칭 점수·정렬 후 (상위 limit건, 전체 매칭 수)."""
    shinsin = match_params.get("shinsin") or ""
    scored: list[dict[str, Any]] = []
    for r in db:
        score = score_manseryeok_item(r, match_params)
        if score > 0:
            scored.append({**r, "_match_score": score})

    scored.sort(key=lambda x: _match_sort_key(x, shinsin), reverse=True)
    return scored[:limit], len(scored)


def extract_match_params(
    day_master: str,
    pillars: dict,
    *,
    gender: str,
    counts: dict[str, int],
    yong_block: dict[str, Any],
    sinsal_block: dict[str, Any],
    sip_stems: dict[str, Any],
) -> dict[str, str]:
    """만세력 saju-match API용 쿼리 값 추출."""
    month_sip = ""
    if isinstance(sip_stems.get("month"), dict):
        month_sip = str(sip_stems["month"].get("sipsin") or "")
    elif isinstance(sip_stems.get("month"), str):
        month_sip = sip_stems["month"]

    gyeokguk = f"{month_sip}{MATCH_GYEOK_SUFFIX}" if month_sip else ""

    sinsal_name = ""
    for row in sinsal_block.get("신살_목록") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("신살") or "")
        if name in MATCH_SINSAL_NAMES:
            sinsal_name = name
            break
    if not sinsal_name:
        for row in sinsal_block.get("신살_목록") or []:
            if isinstance(row, dict) and row.get("신살"):
                sinsal_name = str(row["신살"])
                break

    ohaeng = str(yong_block.get("용신_오행") or "")

    return {
        "shinsin": month_sip,
        "sinsal": sinsal_name,
        "gyeokguk": gyeokguk,
        "ohaeng": ohaeng,
    }


def _pillars_summary(pillars: dict) -> list[dict[str, str]]:
    rows = []
    for pk in PILLAR_KEYS:
        p = pillars[pk]
        rows.append(
            {
                "key": pk,
                "label": PILLAR_LABEL[pk],
                "pillar": p.get("pillar", ""),
                "label_kr": p.get("label_kr", ""),
                "nayin": p.get("nayin", ""),
            }
        )
    return rows


_WHERE_TO_PILLAR = (
    ("년지", "year"),
    ("월지", "month"),
    ("일지", "day"),
    ("시지", "hour"),
    ("년간", "year"),
    ("월간", "month"),
    ("일간", "day"),
    ("시간", "hour"),
    ("년주", "year"),
    ("월주", "month"),
    ("일주", "day"),
    ("시주", "hour"),
)


def _sinsal_by_pillar(rows: list) -> tuple[dict[str, list], list]:
    by_pk: dict[str, list] = {k: [] for k in PILLAR_KEYS}
    shared: list[dict[str, str]] = []
    for r in rows:
        if not isinstance(r, dict) or not r.get("신살"):
            continue
        where = str(r.get("위치") or "")
        hit: list[str] = []
        for lab, pk in _WHERE_TO_PILLAR:
            if lab in where and pk not in hit:
                hit.append(pk)
        item = {
            "신살": r.get("신살"),
            "길흉": r.get("길흉"),
            "글자": r.get("글자"),
            "위치": where,
        }
        if not hit:
            shared.append(item)
            continue
        for pk in hit:
            names = {x["신살"] for x in by_pk[pk]}
            if item["신살"] not in names:
                by_pk[pk].append(item)
    return by_pk, shared


def _merge_jijanggan_slots(
    hidden_block: dict,
    hidden_sipsin: dict,
    pk: str,
) -> list[dict[str, str]]:
    block = hidden_block.get(pk) or {}
    hidden = block.get("hidden") or []
    sp_list = hidden_sipsin.get(pk) or []
    if not isinstance(sp_list, list):
        sp_list = []
    out: list[dict[str, str]] = []
    for i, h in enumerate(hidden):
        if not isinstance(h, dict):
            continue
        sp = sp_list[i] if i < len(sp_list) else {}
        if not isinstance(sp, dict):
            sp = {}
        gan = h.get("gan") or sp.get("gan") or ""
        out.append(
            {
                "slot": h.get("slot") or "",
                "gan": gan,
                "kr": h.get("kr") or sp.get("gan_kr") or "",
                "element": h.get("element") or gj.element_of_stem(gan) if gan else "",
                "sipsin": sp.get("sipsin") or "",
            }
        )
    return out


def build_manseryeok_wonguk(
    *,
    pillars: dict,
    day_master: str,
    gender: str,
    counts: dict[str, int],
    sip_full: dict[str, Any],
    yong_block: dict[str, Any],
    sinsal_block: dict[str, Any],
) -> dict[str, Any]:
    """K사주마당 품 원국 탭과 동일 축(오행·십신·지장간·십이운성·신살) 요약."""
    female = sp.is_female_gender(gender)
    sip_stems = sip_full.get("천간") or {}
    sip_branches = sip_full.get("지지") or {}
    hidden_block = jj.all_hidden_for_pillars(pillars)
    hidden_sipsin = {
        k: (sip_branches.get(k) or {}).get("hidden") or [] for k in PILLAR_KEYS
    }
    hidden_block = jj.enrich_hidden_for_user(
        hidden_block, hidden_sipsin, female=female
    )
    sibi_block = sibi_mod.pillar_twelve_stages(day_master, pillars)
    sinsal_rows = sinsal_block.get("신살_목록") or []
    sinsal_by_pillar, sinsal_shared = _sinsal_by_pillar(sinsal_rows)

    yong_elem = str(yong_block.get("용신_오행") or "")
    hee_arr = list(yong_block.get("희신") or [])
    gi_arr = list(yong_block.get("기신") or [])

    pillar_detail: dict[str, Any] = {}
    for pk in PILLAR_KEYS:
        p = pillars[pk]
        gan = p["gan"]
        zhi = p["zhi"]
        stem = sip_stems.get(pk) or {}
        branch = sip_branches.get(pk) or {}
        sibi_row = sibi_block.get(pk) or {}
        stem_elem = gj.element_of_stem(gan)
        zhi_elem = gj.element_of_branch(zhi)
        sip_gan = str(stem.get("sipsin") or "")
        sip_role = ""
        if pk != "day" and stem_elem:
            if stem_elem == yong_elem:
                sip_role = "yong"
            elif stem_elem in hee_arr:
                sip_role = "hee"
            elif stem_elem in gi_arr:
                sip_role = "gi"
        hidden_main = ""
        hidden_items = branch.get("hidden") or []
        if hidden_items:
            hidden_main = str(hidden_items[0].get("sipsin") or "")
        pillar_detail[pk] = {
            "label": PILLAR_LABEL[pk],
            "gan": gan,
            "zhi": zhi,
            "gan_kr": p.get("gan_kr") or stem.get("gan_kr") or "",
            "zhi_kr": p.get("zhi_kr") or branch.get("zhi_kr") or "",
            "pillar": p.get("pillar", ""),
            "label_kr": p.get("label_kr", ""),
            "gan_element": stem_elem,
            "zhi_element": zhi_elem,
            "sip_gan": sip_gan,
            "sip_gan_role": sip_role,
            "sip_zhi_main": hidden_main,
            "sip_zhi_summary": branch.get("summary") or "",
            "sibi_stage": sibi_row.get("stage") or "",
            "sibi_meaning": sibi_row.get("meaning") or "",
            "jijanggan": _merge_jijanggan_slots(hidden_block, hidden_sipsin, pk),
            "sinsal": sinsal_by_pillar.get(pk) or [],
        }

    counts_surface = oh.count_elements_surface(pillars)
    return {
        "pillars": pillar_detail,
        "pillar_order": list(WONGUK_DISPLAY_ORDER),
        "ohaeng": {
            "counts": counts,
            "counts_surface": counts_surface,
            "summary_lines": oh.element_summary(counts),
            "dominant_weak": oh.dominant_weak_elements(counts),
        },
        "yongsin_ref": {
            "용신_오행": yong_elem,
            "희신": hee_arr,
            "기신": gi_arr,
        },
        "sinsal_all": [
            {
                "신살": r.get("신살"),
                "길흉": r.get("길흉"),
                "글자": r.get("글자"),
                "위치": r.get("위치"),
            }
            for r in sinsal_rows
            if isinstance(r, dict) and r.get("신살")
        ],
        "sinsal_shared": sinsal_shared,
    }


def compute_manseryeok_profile(
    *,
    calendar: str,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "male",
    lunar_leap: bool = False,
    ya_jasi: bool = False,
    hour_unknown: bool = False,
    user_name: str = "",
) -> dict[str, Any]:
    """생년월일시 → 원국 요약 + 매칭 파라미터 + 오늘 일운."""
    calc_hour = 12 if hour_unknown else hour
    calc_minute = 0 if hour_unknown else minute
    calc_ya = False if hour_unknown else ya_jasi

    birth = sc.BirthInput(
        calendar=calendar,
        year=year,
        month=month,
        day=day,
        hour=calc_hour,
        minute=calc_minute,
        lunar_leap=lunar_leap,
        gender=gender,
        ya_jasi=calc_ya,
    )
    raw = sc.compute_saju(birth)
    pillars = raw["pillars"]
    dm = raw["day_master"]
    counts = oh.count_elements(pillars, include_hidden=True)

    sip_full = sp.full_eight_char_sipsin(dm, pillars, gender)
    sip_stems = sip_full.get("천간") or {}
    yong_block = ys.suggest_useful_gods(
        counts, dm, pillars["month"]["zhi"], pillars=pillars
    )
    sinsal_block = sn.analyze_sinsal(dm, pillars, gender=gender)
    wonguk = build_manseryeok_wonguk(
        pillars=pillars,
        day_master=dm,
        gender=gender,
        counts=counts,
        sip_full=sip_full,
        yong_block=yong_block,
        sinsal_block=sinsal_block,
    )
    match_params = extract_match_params(
        dm,
        pillars,
        gender=gender,
        counts=counts,
        yong_block=yong_block,
        sinsal_block=sinsal_block,
        sip_stems=sip_stems,
    )

    il_pack = il.ilwoon_snapshot_pack(dm, pillars)
    today = il_pack.get("오늘") or {}
    fortune = mfort.build_manseryeok_fortune(
        dm, pillars, gender, counts, yong_block
    )

    return {
        "user_name": (user_name or "").strip(),
        "calendar_input": calendar,
        "solar": raw.get("solar"),
        "lunar": raw.get("lunar"),
        "is_leap_month": raw.get("is_leap_month"),
        "jieqi_embedded_year": raw.get("jieqi_embedded_year"),
        "day_master": dm,
        "day_master_kr": raw.get("day_master_kr"),
        "day_master_element": raw.get("day_master_element"),
        "pillars": _pillars_summary(pillars),
        "wonguk": wonguk,
        "eight_char_string": raw.get("eight_char_string"),
        "yongsin": {
            "용신_오행": yong_block.get("용신_오행"),
            "기신_오행": yong_block.get("기신_오행"),
            "판단_요약": yong_block.get("판단_요약"),
        },
        "match_params": match_params,
        "sinsal_highlights": [
            {
                "신살": r.get("신살"),
                "길흉": r.get("길흉"),
                "해석": (r.get("해석") or "")[:120],
            }
            for r in (sinsal_block.get("신살_목록") or [])[:6]
            if isinstance(r, dict)
        ],
        "ilwoon": il_pack,
        "fortune": fortune,
        "ilwoon_today": {
            "양력문자열": today.get("양력문자열"),
            "간지": today.get("간지"),
            "간지한글": today.get("간지한글"),
            "길흉등급": today.get("길흉등급"),
            "한줄판정": today.get("한줄판정"),
        },
        "birth_month_label": f"{month}월",
        "meta": {
            "hour_unknown": hour_unknown,
            "ya_jasi_applied": calc_ya,
        },
    }
