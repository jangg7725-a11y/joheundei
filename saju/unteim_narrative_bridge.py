# -*- coding: utf-8 -*-
"""운테임 narrative DB → 좋은데이 build_report 보강 문장."""

from __future__ import annotations

import hashlib
import random
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

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


def _pack_hap_chung_narrative(rel_full: Optional[Dict[str, Any]], day_master: str) -> str:
    db = nl.load_narrative_db("hap_chung_pattern_db")
    if not db or not rel_full:
        return ""
    rng = _rng("hap", day_master)
    parts: List[str] = []
    for rel_key, label in (
        ("원국_충", "충"),
        ("원국_합", "합"),
        ("원국_형", "형"),
        ("원국_파", "파"),
        ("원국_해", "해"),
    ):
        rows = rel_full.get(rel_key) or []
        if not rows:
            continue
        bucket = {
            "원국_충": "chung",
            "원국_합": "hap",
            "원국_형": "hyeong",
            "원국_파": "pa",
            "원국_해": "hae",
        }.get(rel_key, "chung")
        items = (db.get(bucket) or {}).get("items") or []
        if not isinstance(items, list):
            continue
        row = rows[0] if isinstance(rows[0], dict) else {}
        gz = str(row.get("글자", ""))
        picked = None
        for it in items:
            if not isinstance(it, dict):
                continue
            pair = it.get("pair") or []
            if gz and len(gz) >= 2 and all(ch in gz for ch in pair if isinstance(pair, list)):
                picked = it
                break
        if not picked and items:
            picked = rng.choice([x for x in items if isinstance(x, dict)] or [{}])
        if picked:
            parts.append(
                f"【{label} · {picked.get('label_ko', gz)}】{picked.get('core_dynamic', '')}\n"
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


def _pack_shinsal_psychology(sinsal: Optional[Dict[str, Any]], day_master: str) -> str:
    db = nl.load_narrative_db("shinsal_psychology_db")
    if not db or not sinsal:
        return ""
    patterns = db.get("shinsal_patterns") or {}
    rows = sinsal.get("신살_목록") or []
    rng = _rng("ss_psy", day_master)
    parts: List[str] = []
    for row in rows[:4]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("신살") or "").strip()
        if not name:
            continue
        entry = patterns.get(name) or patterns.get(name.replace("살", ""))
        if not entry:
            continue
        prof = entry.get("psychological_profile") or {}
        parts.append(
            f"【{name}】{entry.get('core_theme', '')}\n"
            f"{prof.get('dominant_trait', '')}\n"
            f"{nl.pick_from_pool(prof.get('behavior_pattern'), rng)}"
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
        "합충_서사": _pack_hap_chung_narrative(rel_full, day_master),
        "십이운성_서사": _pack_twelve_narrative(day_master, sibiunsung),
        "공망_서사": _pack_kongmang_narrative(pillars, day_master),
        "힐링_메시지": _pack_healing_message(day_master, yong),
        "신살_심리": _pack_shinsal_psychology(sinsal, day_master),
        "대운_세운_서사": _pack_daewoon_narrative(daewoon_cycles or (), yong, day_master),
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
        out["unteim_보강"] = _join_text(lines)
    return out


def merge_wealth_boost_display(wealth: Dict[str, Any]) -> Dict[str, Any]:
    """unteim_보강을 UI용 문자열로 통일."""
    out = dict(wealth)
    raw = out.get("unteim_보강")
    if isinstance(raw, list):
        out["unteim_보강"] = _join_text([str(x) for x in raw])
    elif raw is None:
        out["unteim_보강"] = ""
    else:
        out["unteim_보강"] = str(raw).strip()
    return out


def career_boost_text(unteim: Dict[str, Any]) -> str:
    job = unteim.get("직업") or {}
    return _join_text(job.get("문장_목록") or [job.get("한줄_보강", "")])


def personality_boost_text(unteim: Dict[str, Any]) -> str:
    return str(unteim.get("일간_심리") or "").strip()
