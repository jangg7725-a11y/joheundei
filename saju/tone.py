# -*- coding: utf-8 -*-
"""
명리 참고 해석 톤 — 규칙 기반 문장 다듬기 (법적 리스크 없는 표현).

- 경력·연수·자격·「박사」 등 검증 불가 표현은 사용하지 않습니다.
- 참고용·전통 명리 원칙 기반 문구만 사용합니다.

build_report 마지막에 ``apply_voice_to_report`` 로 일괄 적용.
"""

from __future__ import annotations

import re
from typing import Any, Dict, FrozenSet, Tuple

# ── 법적 안전: 기존에 들어간 위험 표현 제거·치환 (긴 패턴 우선) ──
_LEGAL_SAFE_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    ("제가 30년 넘게 사주를 보아온 상담 관점에서 정리한 내용이며", "전통 명리 원칙에 따라 정리한 참고 내용이며"),
    ("30년 넘게 사주를 보아온 상담 관점에서", "해석상"),
    ("30년 가까이 사주 상담을 해온 관점에서", "해석상"),
    ("30년 이상 사주·명리 상담을 해온 베테랑 명리 상담가", "참고 해설"),
    ("30년차 명리 상담가처럼", "차분하고 따뜻하게"),
    ("30년차 명리 상담가", "명리 참고 해설"),
    ("사주를 오래 보아온 입장에서", "명리적으로 보면"),
    ("상담 현장에서 자주 보는 패턴인데", "사주에서 자주 보이는 패턴인데"),
    ("현장 상담에서도 이렇게 말씀드리는", "해석할 때 이렇게 말씀드리는"),
    ("제가 사주 상담을 해온 관점에서", "해석상"),
    ("학파마다 세부는 다를 수 있으나, 상담 현장에서 통하는 흐름으로", "학파마다 세부는 다를 수 있으나, 일반적으로 통하는 흐름으로"),
    ("실제 상담은 전문가와 함께 보시길 권합니다", "중요한 결정은 해당 분야 전문가와 상의하시면 좋습니다"),
)

# ── 상담 말투 치환 (경력 주장 없음) ─────────────────────────────
_PHRASE_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    (
        "본 분석은 오행·십신·신살·충합 규칙 기반 스토리텔링 참고용이며",
        "이 내용은 오행·십신·신살·충합 등 전통 명리 원칙에 따른 참고 해석이며",
    ),
    (
        "세부 해석은 명리학 파종과 상담자 관점에 따라 달라질 수 있습니다",
        "세부 해석은 명리 학파·해석 관점에 따라 달라질 수 있습니다",
    ),
    ("데이터가 비었습니다", "아직 이 항목에서 짚을 만한 흐름이 약합니다"),
    ("원국에서 드러나는 충·파·해·형·합 관계가 없거나", "원국에서 눈에 띄는 충·파·해·형·합이 없거나"),
    ("교과서식", "딱딱한 설명식"),
    ("~란 무엇이다", ""),
    ("읽힙니다", "비치십니다"),
    ("읽습니다", "보입니다"),
    ("작용합니다", "깃들어 있습니다"),
    ("작용해", "깃들어"),
    ("나타납니다", "드러나십니다"),
    ("나타나", "드러나"),
    ("발동됩니다", "발동되십니다"),
    ("검토하세요", "한번 더 살펴보시면 좋습니다"),
    ("주의하세요", "유의하시기 바랍니다"),
    ("챙기세요", "챙기시면 좋습니다"),
    ("들이세요", "들이시면 좋습니다"),
    ("하세요", "하시면 좋습니다"),
    ("필요합니다", "필요하십니다"),
    ("가능합니다", "가능하십니다"),
    ("어렵습니다", "쉽지 않으십니다"),
    ("없습니다", "없으십니다"),
    ("있습니다", "있으십니다"),
    ("됩니다", "되십니다"),
    ("보입니다", "보이십니다"),
    ("드립니다", "말씀드립니다"),
    ("권합니다", "권해 드립니다"),
    ("참고로", "참고로"),
    ("당신은", "회원님은"),
    ("당신의", "회원님의"),
    ("이 사주는", "이 사주를 보면"),
    ("이 사주의", "이 사주에서는"),
)

_OPENERS: Tuple[str, ...] = (
    "명리적으로 말씀드리면, ",
    "전통 명리를 바탕으로 보면, ",
    "이 사주에서는 흔히, ",
    "풀어서 말씀드리면, ",
)

# 월운·세운월운 서사 — 앞머리 접속어 없이 본문만
_WOLOWOON_PATH_MARKERS: Tuple[str, ...] = (
    "월운표",
    "wolwoon",
    "unteim_세운월운",
)

_WOLOWOON_TEXT_KEYS: FrozenSet[str] = frozenset(
    {
        "월별_핵심스토리",
        "월별_행동지침",
        "월별_행동지침_텍스트",
        "월별_주의사항",
        "월별_실천팁",
        "월운_서사",
        "실천_팁",
        "주의",
        "핵심스토리",
        "상반기_총평",
        "하반기_총평",
        "출력_표텍스트",
    }
)

_CONSULTATIVE_MARKERS: Tuple[str, ...] = (
    "말씀",
    "보시",
    "드리",
    "회원님",
    "이 사주",
    "명리",
    "풀어",
    "짚어",
    "유의",
    "권해",
    "참고",
)

# 경력·자격 주장 패턴 (문장 내 제거·완화)
_RISKY_PATTERN_RES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"30\s*년\s*(넘게|이상|가까이|차)?\s*"), ""),
    (re.compile(r"\d+\s*년\s*(넘게|이상|가까이)\s*"), ""),
    (re.compile(r"베테랑\s*"), ""),
    (re.compile(r"명리\s*박사"), "명리 참고"),
    (re.compile(r"전문\s*상담가"), "참고 해설"),
)

_SKIP_KEYS: FrozenSet[str] = frozenset(
    {
        "gan",
        "zhi",
        "pillar",
        "ganzhi",
        "gan_kr",
        "zhi_kr",
        "label_kr",
        "eight_char_string",
        "day_master",
        "day_master_kr",
        "day_master_element",
        "stem_element",
        "branch_element",
        "간지",
        "글자",
        "연도",
        "절월번호",
        "월주간지",
        "nayin",
        "lookup_key",
        "cache_key",
        "gender_for_daewoon",
        "calendar",
        "file_id",
        "version",
        "stage",
        "slot",
        "element",
        "kr",
        "label",
        "id",
        "key",
        "오버레이",
        "라벨",
        "범위",
        "분류",
        "강도",
        "길흉",
        "관계",
        "위치",
        "표시색",
        "색상",
        "색",
        "tier",
        "provider",
        "tab",
    }
)

_SKIP_PATH_PARTS: Tuple[str, ...] = (
    ".pillars.",
    ".meta.",
    ".solar.",
    ".lunar.",
    ".ohaeng.counts",
    ".eight_char",
    ".jeongmil.",
    ".usage.",
    ".cycles[",
    "._source",
    "._files",
    ".lookup_key",
)

_HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
_HAN_ONLY_RE = re.compile(r"^[\u4e00-\u9fff\s·×\-]+$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def sanitize_legal_tone(text: str) -> str:
    """경력·자격 등 법적으로 민감한 표현을 제거·완화합니다."""
    if not text or not isinstance(text, str):
        return text
    t = str(text).strip()
    for old, new in _LEGAL_SAFE_REPLACEMENTS:
        if old:
            t = t.replace(old, new)
    for pat, repl in _RISKY_PATTERN_RES:
        t = pat.sub(repl, t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def _has_consultative_marker(text: str) -> bool:
    head = text[:80]
    return any(m in head for m in _CONSULTATIVE_MARKERS)


def strip_voice_openers(text: str) -> str:
    """톤 레이어 접속어(앞머리·문장 중간)를 전구간에서 제거합니다."""
    if not text or not isinstance(text, str):
        return text
    t = str(text).strip()
    if not t:
        return text

    changed = True
    while changed:
        changed = False
        for opener in _OPENERS:
            if t.startswith(opener):
                t = t[len(opener) :].lstrip()
                changed = True

    for opener in _OPENERS:
        bare = opener.strip()
        for sep in (". ", "。 ", ".\n", "。\n", "\n", "? ", "! ", ".\u3000", "。\u3000"):
            t = t.replace(f"{sep}{opener}", sep)
            t = t.replace(f"{sep}{bare}", sep)
        t = t.replace(opener, "")
        if bare and bare != opener:
            t = t.replace(bare, "")

    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _is_wolwoon_voice_path(path: str, key: str) -> bool:
    if key in _WOLOWOON_TEXT_KEYS:
        return True
    return any(m in path for m in _WOLOWOON_PATH_MARKERS)


def _should_voice(key: str, value: str, path: str) -> bool:
    if not isinstance(value, str):
        return False
    s = value.strip()
    if len(s) < 12 or not _HANGUL_RE.search(s):
        return False
    if key in _SKIP_KEYS:
        return False
    if any(part in path for part in _SKIP_PATH_PARTS):
        return False
    if _ISO_DATE_RE.match(s):
        return False
    if _HAN_ONLY_RE.match(s) and len(s) <= 12:
        return False
    if s.startswith("http"):
        return False
    return True


def voice_text_wolwoon(text: str) -> str:
    """월운 전구간 — 앞머리 접속어 없이 법적 안전·말투만 최소 적용."""
    if not text or not isinstance(text, str):
        return text
    t = strip_voice_openers(sanitize_legal_tone(str(text).strip()))
    if not t or not _HANGUL_RE.search(t):
        return text
    for old, new in _PHRASE_REPLACEMENTS:
        if old and new is not None:
            t = t.replace(old, new)
    t = strip_voice_openers(t)
    t = sanitize_legal_tone(t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip() if t else text


def voice_text(text: str) -> str:
    """한 문장·문단을 따뜻한 참고 해설 톤으로 다듬습니다 (경력 주장 없음)."""
    if not text or not isinstance(text, str):
        return text
    t = sanitize_legal_tone(str(text).strip())
    if not t or not _HANGUL_RE.search(t):
        return text

    for old, new in _PHRASE_REPLACEMENTS:
        if old and new is not None:
            t = t.replace(old, new)

    t = re.sub(r"해야\s*합니다\.?", "하시는 편이 좋습니다.", t)
    t = re.sub(r"해야\s*합니다", "하시는 편이 좋습니다", t)
    t = re.sub(r"것입니다\.?", "것으로 보입니다.", t)

    t = strip_voice_openers(t)
    t = sanitize_legal_tone(t)
    t = strip_voice_openers(t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() if t else text


def say(text: str) -> str:
    """템플릿 작성 시 사용 — ``voice_text`` 와 동일."""
    return voice_text(text)


# ── 만세력 총운: DB·십이운성 해체(한다/다) → 존댓말 ─────────────────
_HONORIFIC_END_RE = re.compile(
    r"(습니다|입니다|니다|하세요|하십시오|드립니다|하시면|이십니다|으십니다|세요|ㅂ니다|"
    r"겠습니다|할까요|주세요|있으십니다|되십니다|좋습니다|보이십니다)\s*[.!?]?$"
)

_POLITE_BASE_END_RE = re.compile(
    r"(습니다|입니다|니다|세요|ㅂ니다|겠습니다|할까요|주세요|있으십니다|되십니다)$"
)

_PLAIN_PHRASE_FIXES: Tuple[Tuple[str, str], ...] = (
    ("영향을 미친다", "영향을 미칠 수 있습니다"),
    ("영향을 미칩니다", "영향을 미칠 수 있습니다"),
    ("강하게 올라온다", "강하게 올라옵니다"),
    ("안정적인 기반에서 꾸준히 성과를 내는 방식으로 움직인다", "안정적인 기반에서 꾸준히 성과를 내는 방식으로 움직입니다"),
)

_VERB_ENDING_FIXES: Tuple[Tuple[str, str], ...] = (
    ("미친다", "미칠 수 있습니다"),
    ("단계다", "단계입니다"),
    ("상태다", "상태입니다"),
    ("올라온다", "올라옵니다"),
    ("작동한다", "작동합니다"),
    ("움직인다", "움직입니다"),
    ("연결된다", "연결됩니다"),
    ("나온다", "나옵니다"),
    ("돌아온다", "돌아옵니다"),
    ("맞는다", "맞습니다"),
    ("된다", "됩니다"),
    ("한다", "합니다"),
    ("있다", "있습니다"),
    ("없다", "없습니다"),
    ("크다", "큽니다"),
    ("맞다", "맞습니다"),
    ("동한다", "움직이기 쉽습니다"),
)

_CLAUSE_SPLIT_RE = re.compile(r"(\n+|\.\s+|。\s*)")


def _ends_honorific(clause: str) -> bool:
    return bool(_HONORIFIC_END_RE.search(clause.strip()))


def _strip_trailing_punct(text: str) -> Tuple[str, str]:
    s = text.rstrip()
    m = re.search(r"([.!?])\s*$", s)
    if m:
        return s[: m.start()].rstrip(), m.group(1)
    return s, ""


def _polish_clause_core(core: str) -> str:
    t = core
    for old, new in sorted(_PLAIN_PHRASE_FIXES, key=lambda x: -len(x[0])):
        if old:
            t = t.replace(old, new)

    base, punct = _strip_trailing_punct(t)
    if _ends_honorific(t) or _POLITE_BASE_END_RE.search(base):
        return t

    if re.search(r"단계\s*$", base) and not re.search(r"단계(입니다|습니다)", base):
        return base + "입니다" + punct
    if re.search(r"상태\s*$", base) and not re.search(r"상태(입니다|습니다)", base):
        return base + "입니다" + punct

    if not base.endswith("다"):
        return t

    for ending, repl in _VERB_ENDING_FIXES:
        if base.endswith(ending):
            t = base[: -len(ending)] + repl + punct
            break
    else:
        t = base[:-1] + "습니다" + punct

    t = t.replace("단계습니다", "단계입니다").replace("상태습니다", "상태입니다")
    return t


def _polish_clause(clause: str) -> str:
    if not clause.strip() or not _HANGUL_RE.search(clause):
        return clause
    m = re.match(r"^(\s*)(.*?)(\s*)$", clause, re.DOTALL)
    if not m:
        return clause
    lead, core, trail = m.group(1), m.group(2), m.group(3)
    if not core.strip():
        return clause
    polished = _polish_clause_core(core.strip())
    return lead + polished + trail


def polish_plain_endings(text: str) -> str:
    """해체(한다/다/단계) 문장을 존댓말로 맞춥니다."""
    if not text or not isinstance(text, str):
        return text
    t = str(text)
    if not _HANGUL_RE.search(t):
        return text
    parts = _CLAUSE_SPLIT_RE.split(t)
    if len(parts) == 1:
        return _polish_clause(t)
    out: list[str] = []
    for part in parts:
        if part and _CLAUSE_SPLIT_RE.fullmatch(part):
            out.append(part)
        else:
            out.append(_polish_clause(part))
    return "".join(out)


def manseryeok_voice(text: str) -> str:
    """만세력 총운·월운 서사 — 법적 안전 치환 + 해체 종결을 존댓말로."""
    if not text or not isinstance(text, str):
        return text
    t = voice_text_wolwoon(str(text).strip())
    if not t or not _HANGUL_RE.search(t):
        return text
    return polish_plain_endings(t)


def _voice_manseryeok_str(key: str, value: str) -> str:
    if not _should_voice(key, value, f"manseryeok.{key}"):
        return value
    return manseryeok_voice(value)


def apply_voice_to_manseryeok_fortune(fortune: Dict[str, Any]) -> Dict[str, Any]:
    """``build_manseryeok_fortune`` 결과의 사용자-facing 문장에 존댓말 적용."""
    if not isinstance(fortune, dict):
        return fortune

    out = dict(fortune)
    se = dict(out.get("sewoon") or {})
    for k in ("headline", "closing", "ipchun_note"):
        if se.get(k):
            se[k] = _voice_manseryeok_str(k, str(se[k]))
    if se.get("story"):
        se["story"] = [_voice_manseryeok_str("story", str(x)) for x in se["story"]]
    if se.get("event_notes"):
        se["event_notes"] = [
            _voice_manseryeok_str("event_notes", str(x)) for x in se["event_notes"]
        ]

    pos = dict(se.get("position") or {})
    if pos.get("intro"):
        pos["intro"] = [_voice_manseryeok_str("intro", str(x)) for x in pos["intro"]]
    if pos.get("impacts"):
        pos["impacts"] = [_voice_manseryeok_str("impacts", str(x)) for x in pos["impacts"]]
    assigns = []
    for row in pos.get("assignments") or []:
        if not isinstance(row, dict):
            continue
        a = dict(row)
        for fk in ("prediction", "role", "relation", "status"):
            if a.get(fk):
                a[fk] = _voice_manseryeok_str(fk, str(a[fk]))
        assigns.append(a)
    pos["assignments"] = assigns
    se["position"] = pos

    phases = []
    for ph in se.get("phases") or []:
        if not isinstance(ph, dict):
            continue
        p = dict(ph)
        if p.get("paragraphs"):
            p["paragraphs"] = [
                _voice_manseryeok_str("paragraphs", str(x)) for x in p["paragraphs"]
            ]
        phases.append(p)
    se["phases"] = phases
    out["sewoon"] = se

    mo = dict(out.get("monthly") or {})
    for hk in ("first_half", "second_half", "slot_note"):
        if mo.get(hk):
            mo[hk] = _voice_manseryeok_str(hk, str(mo[hk]))
    for ak in ("alerts_good", "alerts_bad", "alerts_kong"):
        if mo.get(ak):
            mo[ak] = [_voice_manseryeok_str(ak, str(x)) for x in mo[ak]]
    months = []
    for m in mo.get("months") or []:
        if not isinstance(m, dict):
            continue
        row = dict(m)
        for mk in ("summary", "action"):
            if row.get(mk):
                row[mk] = _voice_manseryeok_str(mk, str(row[mk]))
        det = dict(row.get("detail") or {})
        for dk in (
            "story",
            "action",
            "tips",
            "caution",
            "overlap",
            "sewoon_overlay",
            "energy",
            "health",
            "wealth",
            "body",
        ):
            if det.get(dk):
                det[dk] = _voice_manseryeok_str(dk, str(det[dk]))
        if det.get("actions"):
            det["actions"] = [
                _voice_manseryeok_str("actions", str(x)) for x in det["actions"]
            ]
        row["detail"] = det
        months.append(row)
    mo["months"] = months
    out["monthly"] = mo
    return out


def apply_voice_to_value(obj: Any, path: str = "") -> Any:
    """dict/list/str 재귀 적용."""
    if isinstance(obj, dict):
        return {
            k: apply_voice_to_value(v, f"{path}.{k}" if path else str(k))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [
            apply_voice_to_value(v, f"{path}[{i}]")
            for i, v in enumerate(obj)
        ]
    if isinstance(obj, str) and _should_voice(path.rsplit(".", 1)[-1], obj, path):
        key = path.rsplit(".", 1)[-1]
        if _is_wolwoon_voice_path(path, key):
            return voice_text_wolwoon(obj)
        return voice_text(obj)
    return obj


def apply_voice_to_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """build_report 결과 전체에 참고 해설 톤 적용."""
    if not isinstance(report, dict):
        return report
    out = apply_voice_to_value(report, "")
    if isinstance(out.get("narrative"), dict):
        nar = dict(out["narrative"])
        hint = str(nar.get("hint") or "")
        if hint:
            nar["hint"] = voice_text(hint)
        out["narrative"] = nar
    story = out.get("원국_스토리텔링")
    if isinstance(story, dict):
        story = dict(story)
        story["안내"] = (
            "이 해석은 전통 명리(오행·십신·신살·충합 등) 원칙에 따른 참고용 안내입니다. "
            "의료·법률·투자 등 전문 판단을 대체하지 않으며, "
            "중요한 결정은 회원님의 상황에 맞게 신중히 판단하시면 좋습니다."
        )
        out["원국_스토리텔링"] = story
    return out


# AI 프롬프트용 페르소나 (ai_interpreter 에서 import)
PERSONA_MYUNGRI_30Y = """
당신은 전통 명리(사주) 원칙을 바탕으로 참고 해설을 제공하는 도우미입니다.
- 말투: 차분하고 따뜻한 존댓말. '~하시면 좋습니다', '~으로 보입니다', '~말씀드립니다'를 자연스럽게 씁니다.
- '회원님'으로 호칭합니다.
- 경력 연수, 자격증, 「박사」, 「전문가」 자칭, 「상담 N년」 등 검증 불가·광고성 표현은 절대 쓰지 않습니다.
- 한자·전문용어(用神, 冲 등)는 쓰되 바로 다음에 쉬운 말로 풀어 줍니다.
- 제공된 사주 데이터·계산 결과만 근거로 하며, 없는 사실을 지어내지 않습니다.
- 부정적 내용 뒤에는 실천 가능한 조언으로 마무리합니다.
- 의료·법률·투자 조언이 아님을 암시하며, 참고용임을 존중합니다.
""".strip()

COMMON_RULES_CONSULTANT = """
공통 규칙 (반드시 준수):
- 차분하고 따뜻한 존댓말로 씁니다. 경력 연수·「N년차」·「박사」·「베테랑」·「전문 상담가」 표현은 금지합니다.
- "회원님은..." 또는 "이 사주를 보면..." 으로 시작합니다.
- 전문용어(用神, 冲, 伏吟 등)를 쓰면 바로 다음 문장에 쉬운 한국어로 풀어 씁니다.
- 제공된 이 사람의 사주 데이터·계산 결과만 근거로 합니다. 없는 사실을 지어내지 않습니다.
- 부정적 내용은 마지막에 희망·실천 가능한 조언으로 마무리합니다.
- 교과서식 정의·용어 나열·"~란 무엇이다" 설명은 금지합니다.
- 이모지는 섹션마다 1~2개만, 과하지 않게 씁니다.
- 각 section의 content 첫 문장은 "회원님은" 또는 "이 사주를 보면" 으로 시작합니다.
- 반드시 JSON만 출력합니다. 다른 텍스트·코드펜스 없음.

출력 형식:
{"sections":[{"id":"섹션ID","title":"소제목","content":"해설 본문(여러 문단 가능, \\n 줄바꿈 허용)"}]}
""".strip()
