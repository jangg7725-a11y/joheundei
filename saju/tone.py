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
    ("30년 넘게 사주를 보아온 상담 관점에서", "전통 명리를 바탕으로"),
    ("30년 가까이 사주 상담을 해온 관점에서", "전통 명리를 바탕으로"),
    ("30년 이상 사주·명리 상담을 해온 베테랑 명리 상담가", "전통 명리를 바탕으로 해석하는 참고 도우미"),
    ("30년차 명리 상담가처럼", "차분하고 따뜻하게"),
    ("30년차 명리 상담가", "명리 참고 해설"),
    ("사주를 오래 보아온 입장에서", "명리적으로 보면"),
    ("상담 현장에서 자주 보는 패턴인데", "사주에서 자주 보이는 패턴인데"),
    ("현장 상담에서도 이렇게 말씀드리는", "해석할 때 이렇게 말씀드리는"),
    ("제가 사주 상담을 해온 관점에서", "전통 명리를 바탕으로"),
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

    if (
        len(t) >= 48
        and not _has_consultative_marker(t)
        and t[0] not in ("【", "▸", "※", "⚡", "🔵", "🟡", "🟢", "🔴", "💬", "🕳", "✅", "[")
        and not t.startswith("http")
    ):
        idx = sum(ord(c) for c in t[:40]) % len(_OPENERS)
        t = _OPENERS[idx] + t

    t = sanitize_legal_tone(t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() if t else text


def say(text: str) -> str:
    """템플릿 작성 시 사용 — ``voice_text`` 와 동일."""
    return voice_text(text)


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
