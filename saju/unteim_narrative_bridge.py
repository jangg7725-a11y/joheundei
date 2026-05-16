# -*- coding: utf-8 -*-
"""운테임 narrative DB → 좋은데이 build_report 보강 문장."""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional

from . import narrative_loader as nl
from . import ohaeng as oh


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
    flow_cases = db.get("money_flow_cases") or {}
    flow_line = ""
    if isinstance(flow_cases, dict):
        case_key = rng.choice(list(flow_cases.keys())) if flow_cases else ""
        if case_key:
            flow_line = nl.pick_from_pool((flow_cases.get(case_key) or {}).get("lines_pool"), rng)
    lines = [v for v in (o_slots.get("advice"), g_slots.get("core_theme"), flow_line) if v]
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


def _pack_daymaster_psychology(day_master: str) -> Dict[str, Any]:
    db = nl.load_narrative_db("daymaster_psychology_db")
    if not db:
        return {}
    rng = _rng("dm_psy", day_master)
    gkey = _map_key(db, "key_map", day_master) or day_master
    entry = (db.get("daymaster") or {}).get(gkey) or {}
    slots = entry.get("slots") if isinstance(entry.get("slots"), dict) else entry
    if isinstance(slots, dict):
        picked = {k: nl.pick_from_pool(v, rng) for k, v in slots.items() if v}
        lines = [picked.get("surface"), picked.get("inner"), picked.get("advice")]
        lines = [x for x in lines if x]
        return {"슬롯": picked, "한줄_보강": lines[0] if lines else ""}
    return {"한줄_보강": nl.pick_from_pool(entry.get("lines_pool"), rng)}


def build_unteim_story_supplement(
    *,
    day_master: str,
    pillars: dict,
    gender: str,
    counts: Dict[str, int],
    yong: Dict[str, Any],
    female: bool,
) -> Dict[str, Any]:
    """원국 스토리텔링에 붙일 운테임 DB 보강 묶음."""
    p4 = f"{pillars['year']['pillar']}-{pillars['month']['pillar']}-{pillars['day']['pillar']}-{pillars['hour']['pillar']}"
    money = _pack_money(day_master, counts, yong)
    health = _pack_health(day_master, counts)
    relation = _pack_relationship(counts, female)
    career = _pack_career(day_master, counts)
    dm_psy = _pack_daymaster_psychology(day_master)

    available = nl.list_narrative_files()
    return {
        "_source": "unteim_narrative",
        "_files_loaded": len(available),
        "재물": money,
        "건강": health,
        "관계": relation,
        "직업": career,
        "일간_심리": dm_psy,
        "meta": {
            "day_master": day_master,
            "gender": "여" if female else "남",
            "yong_el": yong.get("용신_오행"),
            "pillars": p4,
        },
    }


def merge_wealth_with_unteim(wealth: Dict[str, Any], unteim: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(wealth)
    line = (unteim.get("재물") or {}).get("한줄_보강") or ""
    if line:
        base = str(out.get("버는_방식", "")).strip()
        out["버는_방식"] = f"{base} {line}".strip() if base else line
        out["unteim_보강"] = (unteim.get("재물") or {}).get("문장_목록") or []
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
        out["unteim_보강"] = lines
    return out
