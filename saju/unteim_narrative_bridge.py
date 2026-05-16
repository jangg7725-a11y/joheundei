# -*- coding: utf-8 -*-
"""운테임 narrative DB → 좋은데이 build_report 보강 문장."""

from __future__ import annotations

import hashlib
import random
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import emotion_db_bridge as emb
from . import ganji as gj
from . import narrative_loader as nl
from . import ohaeng as oh

_PILLAR_LABEL = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}


def _stable_seed(*parts: Any) -> int:
    raw = "|".join(str(p) for p in parts)
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)


def _rng(*parts: Any) -> random.Random:
    return random.Random(_stable_seed(*parts))


def _map_key(db: Dict[str, Any], section: str, raw: str) -> Optional[str]:
    name = str(raw).strip()
    if not name:
        return None
    mapping = (db.get("engine_mapping") or {}).get(section) or {}
    if name in mapping:
        return str(mapping[name])
    if name in db.get(section.replace("_key_map", ""), {}):
        return name
    # engine_mapping key_map for daymaster
    kmap = (db.get("engine_mapping") or {}).get("key_map") or {}
    if name in kmap:
        return str(kmap[name])
    if name in db:
        return name
    return None


def _dominant_oheng(counts: Dict[str, int]) -> str:
    dom = oh.dominant_weak_elements(counts)
    strong = dom.get("strong") or []
    if strong:
        return str(strong[0])
    if counts:
        return max(counts.items(), key=lambda x: x[1])[0]
    return ""


def _weak_oheng(counts: Dict[str, int]) -> str:
    dom = oh.dominant_weak_elements(counts)
    weak = dom.get("weak") or []
    return str(weak[0]) if weak else ""


def _slots_from_entry(entry: Optional[Dict[str, Any]], rng: random.Random) -> Dict[str, str]:
    if not entry or not isinstance(entry, dict):
        return {}
    out: Dict[str, str] = {}
    for key in ("core_theme", "strength", "weakness", "advice", "monthly", "caution"):
        pool_key = f"{key}_pool" if f"{key}_pool" in entry else key
        if pool_key.endswith("_pool") or pool_key in entry:
            val = nl.pick_from_pool(entry.get(pool_key) or entry.get(key), rng)
            if val:
                out[key] = val
    for pk, pv in entry.items():
        if pk.endswith("_pool") and pk not in (
            "strength_pool",
            "weakness_pool",
            "advice_pool",
            "monthly_pool",
            "caution_pool",
        ):
            val = nl.pick_from_pool(pv, rng)
            if val:
                out[pk.replace("_pool", "")] = val
    return out


def _pack_money(day_master: str, counts: Dict[str, int], yong: Dict[str, Any]) -> Dict[str, Any]:
    db = nl.load_narrative_db("money_pattern_db")
    if not db:
        return {}
    rng = _rng("money", day_master, counts.get("목"), yong.get("용신_오행"))
    oheng = _dominant_oheng(counts)
    okey = _map_key(db, "oheng_key_map", oheng) or oheng
    gkey = _map_key(db, "key_map", day_master) or day_master
    o_slots = _slots_from_entry((db.get("oheng_money") or {}).get(okey), rng)
    g_slots = _slots_from_entry((db.get("daymaster_money") or {}).get(gkey), rng)
    advice = str(o_slots.get("advice") or "").strip()
    if "분석 기간에 마감을 정하세요" in advice:
        advice = str(o_slots.get("core_theme") or g_slots.get("money_trait") or "").strip()
    lines = [v for v in (advice, g_slots.get("money_trait"), o_slots.get("strength")) if v]
    lines = [ln for ln in lines if ln and "분석 기간에 마감을 정하세요" not in str(ln)]
    return {
        "오행_재물": o_slots,
        "일간_재물": g_slots,
        "한줄_보강": lines[0] if lines else "",
        "문장_목록": lines[:3],
    }


def _pack_health(day_master: str, counts: Dict[str, int]) -> Dict[str, Any]:
    db = nl.load_narrative_db("health_pattern_db")
    if not db:
        return {}
    rng = _rng("health", day_master, counts.get("화"))
    oheng = _weak_oheng(counts) or _dominant_oheng(counts)
    okey = _map_key(db, "oheng_key_map", oheng) or oheng
    gkey = _map_key(db, "key_map", day_master) or day_master
    o_slots = _slots_from_entry((db.get("oheng_health") or {}).get(okey), rng)
    g_slots = _slots_from_entry((db.get("daymaster_health") or {}).get(gkey), rng)
    lines = [v for v in (o_slots.get("advice"), g_slots.get("caution"), o_slots.get("core_theme")) if v]
    return {
        "오행_건강": o_slots,
        "일간_건강": g_slots,
        "한줄_보강": lines[0] if lines else "",
        "문장_목록": lines[:3],
    }


def _pack_relationship(counts: Dict[str, int], female: bool) -> Dict[str, Any]:
    db = nl.load_narrative_db("relationship_marriage_db")
    if not db:
        return {}
    rng = _rng("relation", female, counts.get("화"))
    oheng = _dominant_oheng(counts)
    okey = _map_key(db, "oheng_key_map", oheng) or oheng
    o_slots = _slots_from_entry((db.get("oheng_relation") or {}).get(okey), rng)
    love = db.get("love_flow") or {}
    love_line = ""
    if isinstance(love, dict) and love:
        lk = rng.choice(list(love.keys()))
        love_line = nl.pick_from_pool((love.get(lk) or {}).get("lines_pool"), rng)
    lines = [v for v in (o_slots.get("advice"), love_line, o_slots.get("core_theme")) if v]
    return {"오행_관계": o_slots, "한줄_보강": lines[0] if lines else "", "문장_목록": lines[:2]}


def _pack_career(day_master: str, counts: Dict[str, int]) -> Dict[str, Any]:
    db = nl.load_narrative_db("career_exam_db")
    voc = nl.load_narrative_db("vocation_narrative_db")
    rng = _rng("career", day_master)
    oheng = _dominant_oheng(counts)
    lines: List[str] = []
    if db:
        okey = _map_key(db, "oheng_key_map", oheng) or oheng
        o_slots = _slots_from_entry((db.get("oheng_career") or {}).get(okey), rng)
        lines.extend([o_slots.get("advice", ""), o_slots.get("core_theme", "")])
    if voc:
        gkey = _map_key(voc, "key_map", day_master) or day_master
        hint = (voc.get("daymaster_vocation_hint") or {}).get(gkey) or {}
        lines.append(nl.pick_from_pool(hint.get("lines_pool") or hint.get("hint_pool"), rng))
    lines = [x for x in lines if x]
    return {"한줄_보강": lines[0] if lines else "", "문장_목록": lines[:3]}


def _join_text(parts: Sequence[str]) -> str:
    return "\n\n".join(p for p in parts if p and str(p).strip())


def _format_daymaster_psych(dm_psy: Dict[str, Any]) -> str:
    if not dm_psy:
        return ""
    lines: List[str] = []
    if dm_psy.get("한줄_보강"):
        lines.append(str(dm_psy["한줄_보강"]))
    slots = dm_psy.get("슬롯") or {}
    if isinstance(slots, dict):
        for v in slots.values():
            s = str(v).strip()
            if s and s not in lines:
                lines.append(s)
    return _join_text(lines)


def _stage_entry(db: Dict[str, Any], stage_kr: str) -> Optional[Dict[str, Any]]:
    stages = db.get("stages") or {}
    for entry in stages.values():
        if isinstance(entry, dict) and entry.get("label_ko") == stage_kr:
            return entry
    return None


def _pack_twelve_narrative(
    day_master: str,
    sibiunsung: Optional[Dict[str, Any]],
) -> str:
    db = nl.load_narrative_db("twelve_fortunes_pattern_db")
    if not db or not sibiunsung:
        return ""
    parts: List[str] = []
    for pk in ("year", "month", "day", "hour"):
        sb = sibiunsung.get(pk) or {}
        st = str(sb.get("stage") or "").strip()
        if not st:
            continue
        entry = _stage_entry(db, st)
        if not entry:
            parts.append(f"【{_PILLAR_LABEL[pk]} · {st}】{sb.get('해설_통합') or sb.get('단계_해설') or ''}")
            continue
        rng = _rng("12f", pk, day_master, st)
        chunk = [
            f"【{_PILLAR_LABEL[pk]} · {st}】{entry.get('core_energy', '')}",
            nl.pick_from_pool(entry.get("behavior_pattern"), rng),
            nl.pick_from_pool(entry.get("reframe"), rng),
        ]
        parts.extend([c for c in chunk if c])
    return _join_text(parts)


def _pair_from_glyphs(glyphs: str) -> Optional[Tuple[str, str]]:
    g = str(glyphs or "").strip()
    if len(g) >= 2:
        return tuple(sorted((g[0], g[1])))
    return None


def _lookup_hap_item(items: List[Any], zhi_pair: Tuple[str, str]) -> Optional[Dict[str, Any]]:
    for it in items:
        if not isinstance(it, dict):
            continue
        pair = it.get("pair") or []
        if not isinstance(pair, list) or len(pair) < 2:
            continue
        if tuple(sorted((str(pair[0]), str(pair[1])))) == zhi_pair:
            return it
    return None


def _pack_hap_chung_narrative(
    rel_full: Optional[Dict[str, Any]],
    day_master: str,
    pillars: Optional[dict] = None,
) -> str:
    db = nl.load_narrative_db("hap_chung_pattern_db")
    if not db or not rel_full:
        return ""
    native_zhis: set = set()
    if pillars:
        native_zhis = {
            str(pillars[k]["zhi"]) for k in ("year", "month", "day", "hour") if k in pillars
        }
    rng = _rng("hap", day_master, tuple(sorted(native_zhis)))
    parts: List[str] = []
    bucket_map = {
        "원국_충": ("chung", "충"),
        "원국_합": ("hap", "합"),
        "원국_형": ("hyeong", "형"),
        "원국_파": ("pa", "파"),
        "원국_해": ("hae", "해"),
    }
    for rel_key, (bucket, label) in bucket_map.items():
        rows = rel_full.get(rel_key) or []
        if not rows:
            continue
        items = (db.get(bucket) or {}).get("items") or []
        if not isinstance(items, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            zpair = _pair_from_glyphs(str(row.get("글자", "")))
            if not zpair:
                continue
            if native_zhis and (zpair[0] not in native_zhis or zpair[1] not in native_zhis):
                continue
            picked = _lookup_hap_item(items, zpair)
            if not picked:
                continue
            parts.append(
                f"【{label} · {picked.get('label_ko', row.get('글자', ''))}】"
                f"{picked.get('core_dynamic', '')}\n"
                f"{nl.pick_from_pool(picked.get('relation_pattern'), rng)}"
            )
    return _join_text(parts)


def _pack_kongmang_narrative(pillars: dict, day_master: str) -> str:
    db = nl.load_narrative_db("kongmang_pattern_db")
    if not db:
        return ""
    rng = _rng("kong", day_master, pillars["day"]["pillar"])
    patterns = db.get("pillar_patterns") or {}
    dz = pillars["day"]["zhi"]
    entry = None
    for val in patterns.values():
        if isinstance(val, dict) and val.get("zhi") == dz:
            entry = val
            break
    if not entry and patterns:
        entry = rng.choice([v for v in patterns.values() if isinstance(v, dict)] or [{}])
    if not entry:
        return ""
    return _join_text(
        [
            entry.get("core_theme", ""),
            nl.pick_from_pool(entry.get("lines_pool") or entry.get("insight_pool"), rng),
            nl.pick_from_pool(entry.get("reframe_pool"), rng),
        ]
    )


def _pack_healing_message(day_master: str, yong: Dict[str, Any]) -> str:
    db = nl.load_narrative_db("healing_message_db")
    if not db:
        return ""
    rng = _rng("heal", day_master, yong.get("용신_오행"))
    situations = db.get("situations") or {}
    if not isinstance(situations, dict) or not situations:
        return ""
    sit = situations.get("steady_growth") or situations.get("burnout") or next(iter(situations.values()))
    if not isinstance(sit, dict):
        return ""
    line = nl.pick_from_pool(sit.get("integrated_pool"), rng)
    if not line:
        line = " ".join(
            filter(
                None,
                [
                    nl.pick_from_pool(sit.get("comfort_pool"), rng),
                    nl.pick_from_pool(sit.get("insight_pool"), rng),
                    nl.pick_from_pool(sit.get("action_pool"), rng),
                ],
            )
        )
    return line.strip()


_SHINSAL_DEEP_TARGETS = (
    "천을귀인",
    "문창귀인",
    "학당귀인",
    "복성귀인",
    "역마살",
    "백호살",
    "양인살",
    "원진살",
    "상문살",
)


def _pack_shinsal_psychology(sinsal: Optional[Dict[str, Any]], day_master: str) -> str:
    db = nl.load_narrative_db("shinsal_psychology_db")
    if not db or not sinsal:
        return ""
    patterns = db.get("shinsal_patterns") or {}
    key_map = (db.get("engine_mapping") or {}).get("key_map") or {}
    present = {
        str(row.get("신살") or "").strip()
        for row in (sinsal.get("신살_목록") or [])
        if isinstance(row, dict) and row.get("신살")
    }
    rng = _rng("ss_psy", day_master)
    parts: List[str] = []
    for name in _SHINSAL_DEEP_TARGETS:
        if name not in present:
            continue
        entry = patterns.get(name) or patterns.get(key_map.get(name.replace("살", ""), ""))
        if not entry:
            native_row = next(
                (
                    r
                    for r in (sinsal.get("신살_목록") or [])
                    if isinstance(r, dict) and r.get("신살") == name
                ),
                None,
            )
            note = (native_row or {}).get("해석", "")
            parts.append(
                f"【{name}】\n"
                f"- 핵심 특성: {note[:60] or name + ' 기운이 원국에 있습니다.'}\n"
                f"- 생활 패턴: 원국에 반복되는 {name} 테마를 의식하세요.\n"
                f"- 긍정 활용법: 신호를 알아차리고 방향을 조절하면 도움이 됩니다.\n"
                f"- 주의사항: 과하면 극단으로 치우칠 수 있으니 균형을 유지하세요."
            )
            continue
        prof = entry.get("psychological_profile") or {}
        beh = prof.get("behavior_pattern") or []
        life_lines = [nl.pick_from_pool(beh, rng)]
        if isinstance(beh, list) and len(beh) > 1:
            alt = nl.pick_from_pool([b for b in beh if b != life_lines[0]], rng)
            if alt:
                life_lines.append(alt)
        strength = entry.get("strength_context") or []
        pos = nl.pick_from_pool(strength, rng) if strength else ""
        caution = entry.get("caution") or nl.pick_from_pool(entry.get("friction_context"), rng)
        parts.append(
            f"【{name}】\n"
            f"- 핵심 특성: {entry.get('core_theme', prof.get('dominant_trait', ''))}\n"
            f"- 생활 패턴: {' '.join(life_lines)}\n"
            f"- 긍정 활용법: {pos}\n"
            f"- 주의사항: {caution}"
        )
    return _join_text(parts)


def _pack_daewoon_narrative(
    daewoon_cycles: Sequence[Dict[str, Any]],
    yong: Dict[str, Any],
    day_master: str,
) -> str:
    db = nl.load_narrative_db("daewoon_sewun_narrative_db")
    if not db:
        return ""
    cy = date.today().year
    cur = None
    for c in daewoon_cycles:
        try:
            sy = int(c.get("start_year"))
            ey = int(c.get("end_year"))
        except (TypeError, ValueError):
            continue
        if sy <= cy <= ey:
            cur = c
            break
    if not cur and daewoon_cycles:
        cur = daewoon_cycles[min(len(daewoon_cycles) // 2, len(daewoon_cycles) - 1)]
    rng = _rng("dw_narr", day_master, (cur or {}).get("ganzhi"), yong.get("용신_오행"))
    flow_types = db.get("flow_types") or {}
    ft_key = "rising_strong"
    if yong.get("일간_강약") == "신약":
        ft_key = "rest_recovery"
    flow = flow_types.get(ft_key) or next(iter(flow_types.values()), {})
    if not isinstance(flow, dict):
        return ""
    gz = (cur or {}).get("ganzhi") or ""
    header = f"【현재 대운 {gz}】{flow.get('core_message', '')}" if gz else str(flow.get("core_message", ""))
    return _join_text(
        [
            header,
            nl.pick_from_pool(flow.get("era_pool"), rng),
            nl.pick_from_pool(flow.get("action_pool"), rng),
            nl.pick_from_pool(flow.get("caution_pool"), rng),
        ]
    )


def _pack_daymaster_psychology(day_master: str) -> Dict[str, Any]:
    db = nl.load_narrative_db("daymaster_psychology_db")
    if not db:
        return {}
    rng = _rng("dm_psy", day_master)
    gkey = _map_key(db, "key_map", day_master) or day_master
    entry = (db.get("daymaster") or {}).get(gkey) or {}
    slots = entry.get("slots") if isinstance(entry.get("slots"), dict) else entry
    if isinstance(slots, dict):
        picked: Dict[str, str] = {}
        for k, v in slots.items():
            if not v:
                continue
            val = nl.pick_from_pool(v, rng)
            if val:
                picked[k] = val
        lines = [picked.get("surface"), picked.get("inner"), picked.get("advice")]
        lines = [x for x in lines if x]
        out: Dict[str, Any] = {"한줄_보강": lines[0] if lines else ""}
        if picked:
            out["슬롯"] = picked
        return out
    return {"한줄_보강": nl.pick_from_pool(entry.get("lines_pool"), rng)}


def _sewun_overlay_key(stars: Any) -> str:
    try:
        s = float(stars)
    except (TypeError, ValueError):
        s = 3.0
    if s >= 4:
        return "boost"
    if s <= 2:
        return "double_caution"
    if s >= 3:
        return "buffer"
    return "accelerate"


def build_unteim_timeline_supplement(
    *,
    day_master: str,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    sewoon_rows: Optional[Sequence[Dict[str, Any]]] = None,
    wol_pack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """세운·월운 탭용 운테임 서사 (연도별·절월별)."""
    dw_db = nl.load_narrative_db("daewoon_sewun_narrative_db")
    mon_db = nl.load_narrative_db("monthly_action_guide_db")
    overlays = (dw_db.get("sewun_overlays") or {}) if dw_db else {}
    oheng_strat = (mon_db.get("oheng_monthly_strategy") or {}) if mon_db else {}
    dm_tips = (mon_db.get("daymaster_monthly_tip") or {}) if mon_db else {}
    dm_key = str(day_master).strip()[:1]

    by_year: Dict[str, Dict[str, str]] = {}
    for row in sewoon_rows or ():
        if not isinstance(row, dict):
            continue
        try:
            yi = int(row.get("연도"))
        except (TypeError, ValueError):
            continue
        rng = _rng("sew_ov", day_master, yi, yong.get("용신_오행"))
        ok = _sewun_overlay_key(row.get("별점"))
        ov = overlays.get(ok) or {}
        hint = nl.pick_from_pool(ov.get("hint_pool"), rng) if isinstance(ov, dict) else ""
        story = str(row.get("세운_총평_한줄") or row.get("이해_총평_한마디") or "").strip()
        parts = [p for p in (hint, story) if p]
        by_year[str(yi)] = {
            "세운_서사": _join_text(parts),
            "오버레이": ok,
            "라벨": str(ov.get("label_ko") or ""),
        }

    by_month: Dict[str, Dict[str, str]] = {}
    for m in (wol_pack or {}).get("월별") or ():
        if not isinstance(m, dict):
            continue
        try:
            mn = int(m.get("절월번호"))
        except (TypeError, ValueError):
            continue
        gz = str(m.get("월주간지") or "")
        stem = gz[0] if gz else ""
        mel = gj.element_of_stem(stem) if stem else _dominant_oheng(counts)
        rng = _rng("wol_mon", day_master, mn, mel, wol_pack.get("세운연도"))
        strat_key = f"{mel}_강"
        strat = oheng_strat.get(strat_key) or {}
        action = nl.pick_from_pool(strat.get("action_pool") or strat.get("strategy_pool"), rng)
        caution = nl.pick_from_pool(strat.get("caution_pool"), rng)
        dm_entry = dm_tips.get(dm_key) or {}
        tip = nl.pick_from_pool(dm_entry.get("monthly_tip_pool"), rng)
        quote = str(m.get("월별_핵심스토리") or "").strip()
        parts = [p for p in (action, tip, caution, quote) if p]
        by_month[str(mn)] = {
            "월운_서사": _join_text(parts[:3]),
            "실천_팁": action,
            "주의": caution,
        }

    cy = int((wol_pack or {}).get("세운연도") or 0)
    year_line = ""
    if cy and str(cy) in by_year:
        year_line = by_year[str(cy)].get("세운_서사") or ""

    return {
        "_source": "unteim_timeline",
        "세운연도": cy,
        "연도별": by_year,
        "월별": by_month,
        "현재_세운_서사": year_line,
    }


_GAN_ALIAS: Dict[str, str] = {
    "甲": "甲", "갑": "甲", "乙": "乙", "을": "乙",
    "丙": "丙", "병": "丙", "丁": "丁", "정": "丁",
    "戊": "戊", "무": "戊", "己": "己", "기": "己",
    "庚": "庚", "경": "庚", "辛": "辛", "신": "辛",
    "壬": "壬", "임": "壬", "癸": "癸", "계": "癸",
}


def _normalize_gan(gan: Any) -> str:
    raw = str(gan).strip()
    if not raw:
        return ""
    if raw in _GAN_ALIAS:
        return _GAN_ALIAS[raw]
    return raw[:1] if raw else ""


def pack_compatibility_matrix(
    dm_a: Any,
    dm_b: Any,
    *,
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, Any]:
    """compatibility_matrix_db — 두 일간 조합 서사."""
    db = nl.load_narrative_db("compatibility_matrix_db")
    combos = (db.get("combinations") or {}) if db else {}
    my_g = _normalize_gan(dm_a)
    partner_g = _normalize_gan(dm_b)
    if not my_g or not partner_g or not combos:
        return {"found": False}

    seed = _stable_seed("gh_matrix", my_g, partner_g, label_a, label_b)
    rng = _rng(seed)
    k_fwd = f"{my_g}_{partner_g}"
    k_rev = f"{partner_g}_{my_g}"
    entry: Optional[Dict[str, Any]] = None
    used_rev = False
    lookup = ""
    if k_fwd in combos and isinstance(combos[k_fwd], dict):
        entry = combos[k_fwd]
        lookup = k_fwd
    elif k_rev in combos and isinstance(combos[k_rev], dict):
        entry = combos[k_rev]
        lookup = k_rev
        used_rev = True
    if not entry:
        return {"found": False}

    slots = {
        "found": True,
        "lookup_key": lookup,
        "used_reverse_lookup": used_rev,
        "label": entry.get("label") or lookup,
        "mingri_relation": entry.get("mingri_relation") or "",
        "core_dynamic": entry.get("core_dynamic") or "",
        "dynamic": nl.pick_from_pool(entry.get("dynamic_pool"), rng),
        "strength": nl.pick_from_pool(entry.get("strength_pool"), rng),
        "friction": nl.pick_from_pool(entry.get("friction_pool"), rng),
        "growth": nl.pick_from_pool(entry.get("growth_pool"), rng),
        "daily_hint": nl.pick_from_pool(entry.get("daily_hint_pool"), rng),
    }
    lines = [
        f"【{slots['label']}】{slots['core_dynamic']}".strip(),
        slots["dynamic"],
        f"강점: {slots['strength']}" if slots["strength"] else "",
        f"마찰·차이: {slots['friction']}" if slots["friction"] else "",
        f"함께 성장: {slots['growth']}" if slots["growth"] else "",
        f"일상 팁: {slots['daily_hint']}" if slots["daily_hint"] else "",
    ]
    slots["표시_텍스트"] = _join_text([x for x in lines if x])
    slots["A_라벨"] = label_a
    slots["B_라벨"] = label_b
    return slots


def build_unteim_story_supplement(
    *,
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    female: bool,
    rel_full: Optional[Dict[str, Any]] = None,
    sinsal: Optional[Dict[str, Any]] = None,
    sibiunsung: Optional[Dict[str, Any]] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """원국 스토리텔링에 붙일 운테임 DB 보강 묶음."""
    p4 = f"{pillars['year']['pillar']}-{pillars['month']['pillar']}-{pillars['day']['pillar']}-{pillars['hour']['pillar']}"
    money = _pack_money(day_master, counts, yong)
    health = _pack_health(day_master, counts)
    relation = _pack_relationship(counts, female)
    emotion = emb.build_emotion_supplement(
        day_master=day_master, counts=counts, rel_full=rel_full
    )
    if emotion.get("표시_텍스트"):
        relation = emb.merge_relation_with_emotion(relation, emotion)
    career = _pack_career(day_master, counts)
    dm_psy = _pack_daymaster_psychology(day_master)
    dm_text = _format_daymaster_psych(dm_psy)

    available = nl.list_narrative_files()
    return {
        "_source": "unteim_narrative",
        "_files_loaded": len(available),
        "재물": money,
        "건강": health,
        "관계": relation,
        "직업": career,
        "일간_심리": dm_text,
        "일간_심리_상세": dm_psy,
        "합충_서사": _pack_hap_chung_narrative(rel_full, day_master, pillars),
        "십이운성_서사": _pack_twelve_narrative(day_master, sibiunsung),
        "공망_서사": _pack_kongmang_narrative(pillars, day_master),
        "힐링_메시지": _pack_healing_message(day_master, yong),
        "신살_심리": _pack_shinsal_psychology(sinsal, day_master),
        "대운_세운_서사": _pack_daewoon_narrative(daewoon_cycles or (), yong, day_master),
        "감정_서사": emotion.get("표시_텍스트")
        or (emotion.get("일간_리포트") or {}).get("핵심")
        or emotion.get("한줄_보강")
        or "",
        "감정_상세": emotion,
        "meta": {
            "day_master": day_master,
            "gender": "여" if female else "남",
            "yong_el": yong.get("용신_오행"),
            "pillars": p4,
        },
    }


def merge_wealth_with_unteim(wealth: Dict[str, Any], unteim: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(wealth)
    money = unteim.get("재물") or {}
    raw_lines = money.get("문장_목록") or []
    lines = [
        ln
        for ln in raw_lines
        if ln and "분석 기간에 마감을 정하세요" not in str(ln)
    ]
    if lines:
        out["unteim_보강"] = lines
    elif money.get("한줄_보강"):
        out["unteim_보강"] = str(money["한줄_보강"]).strip()
    return out


def merge_health_with_unteim(health: Dict[str, Any], unteim: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(health)
    lines = (unteim.get("건강") or {}).get("문장_목록") or []
    if lines:
        advice = list(out.get("건강_유지_조언") or [])
        for ln in lines[:2]:
            if ln and ln not in advice:
                advice.append(ln)
        out["건강_유지_조언"] = advice
        out["unteim_보강"] = _join_text(lines)
    return out


def merge_wealth_boost_display(wealth: Dict[str, Any]) -> Dict[str, Any]:
    """unteim_보강을 UI용 문자열로 통일."""
    out = dict(wealth)
    raw = out.get("unteim_보강")
    if isinstance(raw, list):
        out["unteim_보강"] = _join_text([str(x) for x in raw])
    elif raw is None or (isinstance(raw, str) and not str(raw).strip()):
        out.pop("unteim_보강", None)
    else:
        out["unteim_보강"] = str(raw).strip()
    return out


def career_boost_text(unteim: Dict[str, Any]) -> str:
    job = unteim.get("직업") or {}
    return _join_text(job.get("문장_목록") or [job.get("한줄_보강", "")])


def personality_boost_text(unteim: Dict[str, Any]) -> str:
    return str(unteim.get("일간_심리") or "").strip()
