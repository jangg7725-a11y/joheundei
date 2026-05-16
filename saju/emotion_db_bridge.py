# -*- coding: utf-8 -*-
"""운테임 emotion_db (DB1~6) → 감정·관계 문장 보강."""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import narrative_loader as nl
from . import ohaeng as oh

_OHENG_HANJA = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}
_HANJA_OHENG = {v: k for k, v in _OHENG_HANJA.items()}


def _stable_seed(*parts: Any) -> int:
    raw = "|".join(str(p) for p in parts)
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)


def _rng(*parts: Any) -> random.Random:
    return random.Random(_stable_seed(*parts))


def _to_hanja_oheng(kr: str) -> str:
    k = str(kr).strip()
    return _OHENG_HANJA.get(k, k)


def _oheng_mode(counts: Dict[str, int], element: str) -> str:
    """과다 / 부족 / 균형."""
    if not element or not counts:
        return "균형"
    vals = [int(counts.get(k, 0) or 0) for k in ("목", "화", "토", "금", "수")]
    total = sum(vals) or 1
    v = int(counts.get(element, 0) or 0)
    avg = total / 5.0
    if v >= max(3, avg + 1.2):
        return "과다"
    if v <= 0 or v < avg - 0.8:
        return "부족"
    return "균형"


def _pick_oheng_target(counts: Dict[str, int]) -> Tuple[str, str]:
    dom = oh.dominant_weak_elements(counts)
    strong = dom.get("strong") or []
    weak = dom.get("weak") or []
    if strong:
        el = str(strong[0])
        return el, _oheng_mode(counts, el)
    if weak:
        el = str(weak[0])
        return el, "부족"
    if counts:
        el = max(counts.items(), key=lambda x: x[1])[0]
        return str(el), _oheng_mode(counts, el)
    return "", "균형"


def _pick_from_oheng_pool(
    section: Dict[str, Any],
    element: str,
    mode: str,
    field: str,
    rng: random.Random,
) -> str:
    hanja = _to_hanja_oheng(element)
    block = (section or {}).get(hanja) or {}
    if not isinstance(block, dict):
        return ""
    mode_block = block.get(mode) or block.get("과다") or block.get("부족") or {}
    if isinstance(mode_block, dict):
        return nl.pick_from_pool(mode_block.get(field) or mode_block, rng)
    return nl.pick_from_pool(mode_block, rng)


def _pack_db2_emotion(counts: Dict[str, int], day_master: str) -> Dict[str, str]:
    db = nl.load_emotion_db("DB2_emotion_sentences")
    if not db:
        return {}
    el, mode = _pick_oheng_target(counts)
    if mode == "균형":
        mode = "과다"
    rng = _rng("db2", day_master, el, mode)
    section = db.get("오행_감정문장") or {}
    return {
        "대상_오행": el,
        "패턴": mode,
        "공감": _pick_from_oheng_pool(section, el, mode, "공감_문장", rng),
        "자기이해": _pick_from_oheng_pool(section, el, mode, "자기이해_문장", rng),
    }


def _pack_db4_comfort(counts: Dict[str, int], day_master: str) -> str:
    db = nl.load_emotion_db("DB4_comfort_sentences")
    if not db:
        return ""
    el, mode = _pick_oheng_target(counts)
    if mode == "균형":
        mode = "부족"
    rng = _rng("db4", day_master, el, mode)
    section = (db.get("위로_문장") or {}).get("오행별") or {}
    hanja = _to_hanja_oheng(el)
    block = (section.get(hanja) or {}).get(mode) or (section.get(hanja) or {}).get("과다")
    return nl.pick_from_pool(block, rng)


def _pack_db5_report(day_master: str) -> Dict[str, str]:
    db = nl.load_emotion_db("DB5_report_sentences")
    if not db:
        return {}
    dm = str(day_master).strip()[:1]
    entry = (db.get("일간별_서술") or {}).get(dm) or {}
    if not isinstance(entry, dict):
        return {}
    return {
        "핵심": str(entry.get("핵심") or "").strip(),
        "관계": str(entry.get("관계") or "").strip(),
        "강점": str(entry.get("강점") or "").strip(),
    }


def _cheon_gan_hap_key(rel_full: Optional[Dict[str, Any]]) -> str:
    if not rel_full:
        return ""
    for row in rel_full.get("천간합") or rel_full.get("relations") or []:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("관계") or row.get("type") or "")
        if "합" not in rel:
            continue
        g1 = str(row.get("글자1") or row.get("gan1") or row.get("a") or "")
        g2 = str(row.get("글자2") or row.get("gan2") or row.get("b") or "")
        if g1 and g2:
            return f"{g1}{g2}합"
    detail = rel_full.get("관계_상세_전체") or []
    for row in detail:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("관계") or "")
        if "천간합" in rel or ("합" in rel and "천간" in str(row.get("분류", ""))):
            gz = str(row.get("글자") or "")
            if len(gz) >= 2:
                return f"{gz[0]}{gz[1]}합"
    return ""


def _pack_db3_relation(rel_full: Optional[Dict[str, Any]], day_master: str) -> List[str]:
    db = nl.load_emotion_db("DB3_relation_sentences")
    if not db:
        return []
    rng = _rng("db3", day_master)
    lines: List[str] = []
    hap_key = _cheon_gan_hap_key(rel_full)
    cheon = (db.get("합_패턴") or {}).get("천간합") or {}
    if hap_key and hap_key in cheon:
        entry = cheon[hap_key]
        if isinstance(entry, dict):
            lines.append(nl.pick_from_pool(entry.get("공감_문장"), rng))
            adv = entry.get("연애_조언") or entry.get("직장_조언")
            if adv:
                lines.append(str(adv).strip())
    if not lines:
        common = (db.get("합_패턴") or {}).get("공통_특성") or ""
        if common:
            lines.append(str(common).strip())
    return [x for x in lines if x]


def build_emotion_supplement(
    *,
    day_master: str,
    counts: Dict[str, int],
    rel_full: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """emotion_db DB2~6 기반 감정·관계 문장 묶음."""
    db2 = _pack_db2_emotion(counts, day_master)
    db5 = _pack_db5_report(day_master)
    relation_lines = _pack_db3_relation(rel_full, day_master)
    comfort = _pack_db4_comfort(counts, day_master)

    blocks: List[str] = []
    if db2.get("공감"):
        blocks.append(f"💬 {db2['공감']}")
    if db2.get("자기이해"):
        blocks.append(f"🪞 {db2['자기이해']}")
    if comfort:
        blocks.append(f"💚 {comfort}")
    if db5.get("관계"):
        blocks.append(db5["관계"])
    blocks.extend(relation_lines[:2])

    display = "\n\n".join(blocks)
    return {
        "_source": "unteim_emotion_db",
        "_files_loaded": len(nl.list_emotion_files()),
        "오행_감정": db2,
        "위로": comfort,
        "일간_리포트": db5,
        "관계_문장": relation_lines,
        "표시_텍스트": display,
        "한줄_보강": db2.get("공감") or db5.get("핵심") or "",
    }


def merge_relation_with_emotion(relation: Dict[str, Any], emotion: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(relation)
    extra = list(out.get("문장_목록") or [])
    for ln in emotion.get("관계_문장") or []:
        if ln and ln not in extra:
            extra.append(ln)
    rep = (emotion.get("일간_리포트") or {}).get("관계")
    if rep and rep not in extra:
        extra.append(rep)
    if extra:
        out["문장_목록"] = extra[:4]
        out["unteim_감정_보강"] = emotion.get("표시_텍스트") or ""
    return out
