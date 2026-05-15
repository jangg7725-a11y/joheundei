# -*- coding: utf-8 -*-
"""
사주 맞춤 스토리텔링 해설 — Gemini(무료 한도) 또는 Claude.

환경 변수 (둘 중 하나):
  GEMINI_API_KEY — Google AI Studio 키 (권장·무료 한도)
  GEMINI_MODEL — 기본 gemini-2.0-flash
  ANTHROPIC_API_KEY — Anthropic (유료)
  SAJU_AI_PREMIUM=1 — 일일 제한 해제
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional, Tuple

from . import ai_cache
from . import ai_usage

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore[misc, assignment]

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]

DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
# 무료 한도: gemini-2.0-flash 보다 1.5-flash 가 넉넉한 경우가 많음
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MAX_TOKENS = int(os.getenv("SAJU_AI_GEMINI_MAX_TOKENS", "4096"))
MAX_TOKENS = int(os.getenv("SAJU_AI_MAX_TOKENS", "8192"))
GEMINI_PROMPT_LIMIT = int(os.getenv("SAJU_AI_PROMPT_LIMIT", "7000"))

AI_UNAVAILABLE_MESSAGE = "AI 해설 서비스 준비 중입니다"


def unavailable_response(**extra: Any) -> Dict[str, Any]:
    """API 키 없음·비활성 시 클라이언트·API 공통 응답."""
    body: Dict[str, Any] = {
        "ok": False,
        "enabled": False,
        "message": AI_UNAVAILABLE_MESSAGE,
        "fallback": True,
    }
    body.update(extra)
    return body


def _gemini_api_key() -> str:
    return (
        os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_API_KEY", "").strip()
    )


def is_ai_available() -> bool:
    return active_provider() is not None


def active_provider() -> Optional[str]:
    """gemini | anthropic | None"""
    if _gemini_api_key():
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    return None


def active_model_name() -> str:
    p = active_provider()
    if p == "gemini":
        return DEFAULT_GEMINI_MODEL
    if p == "anthropic":
        return DEFAULT_ANTHROPIC_MODEL
    return ""


# 하위 호환
DEFAULT_MODEL = DEFAULT_ANTHROPIC_MODEL

COMMON_RULES = """
공통 규칙 (반드시 준수):
- "당신은..." 또는 "이 사주는..." 으로 시작한다.
- 전문용어(用神, 冲, 伏吟 등)를 쓰면 바로 다음 문장에 쉬운 한국어로 풀어 쓴다.
- 아래에 제공된 이 사람의 사주 데이터·계산 결과만 근거로 한다. 없는 사실을 지어내지 않는다.
- 부정적 내용은 마지막에 희망·실천 가능한 조언으로 마무리한다.
- 교과서식 정의·용어 나열·"~란 무엇이다" 설명은 금지한다.
- 이모지를 섹션마다 1~3개 적절히 쓴다.
- 따뜻하고 공감하는 어조로, 마치 잘 아는 역술가가 이 사람에게 말하듯 쓴다.
- 각 section의 content 첫 문장은 반드시 "당신은" 또는 "이 사주는" 으로 시작한다.
- 반드시 JSON만 출력한다. 다른 텍스트·코드펜스 없음.

출력 형식:
{"sections":[{"id":"섹션ID","title":"소제목","content":"해설 본문(여러 문단 가능, \\n 줄바꿈 허용)"}]}
""".strip()

TAB_ALIASES = {
    "wonkuk": "wonkuk",
    "원국": "wonkuk",
    "0": "wonkuk",
    "hapchung": "hapchung",
    "합충": "hapchung",
    "1": "hapchung",
    "yongsin": "yongsin",
    "용신": "yongsin",
    "2": "yongsin",
    "daewoon": "daewoon",
    "daewoon_sewoon": "daewoon",
    "대운": "daewoon",
    "3": "daewoon",
    "jonghap": "jonghap",
    "종합": "jonghap",
    "4": "jonghap",
    "sinsal": "sinsal",
    "신살": "sinsal",
    "5": "sinsal",
}


def normalize_tab(tab: str) -> str:
    key = (tab or "").strip().lower()
    if key not in TAB_ALIASES:
        raise ValueError(f"알 수 없는 탭: {tab}")
    return TAB_ALIASES[key]


def _anthropic_client() -> Any:
    if Anthropic is None:
        raise RuntimeError("anthropic 패키지가 설치되지 않았습니다. pip install anthropic")
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 환경 변수를 설정해 주세요.")
    return Anthropic(api_key=api_key)


def _gemini_model_names() -> List[str]:
    primary = (os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip()
    fallbacks = ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-8b"]
    out: List[str] = []
    for name in [primary, *fallbacks]:
        if name and name not in out:
            out.append(name)
    return out


def _gemini_model(system: str, model_name: Optional[str] = None) -> Any:
    if genai is None:
        raise RuntimeError(
            "google-generativeai 패키지가 없습니다. pip install google-generativeai"
        )
    api_key = _gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경 변수를 설정해 주세요.")
    genai.configure(api_key=api_key)
    use_name = model_name or DEFAULT_GEMINI_MODEL
    return genai.GenerativeModel(
        use_name,
        system_instruction=system,
        generation_config={
            "max_output_tokens": GEMINI_MAX_TOKENS,
            "temperature": 0.75,
        },
    )


def _is_quota_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        "429" in str(exc)
        or "quota" in text
        or "resource_exhausted" in text
        or "rate limit" in text
        or "exceeded" in text
    )


def _friendly_api_error(exc: BaseException) -> str:
    if _is_quota_error(exc):
        return (
            "⏳ Gemini 무료 사용 한도에 잠시 걸렸습니다.\n\n"
            "• 15~30분 뒤 「🔄 다시 해설받기」를 눌러 보세요.\n"
            "• 탭을 여러 개 연속으로 열면 한도가 빨리 찹니다. 원국 하나씩 천천히 시도해 보세요.\n"
            "• Google AI Studio → 사용량·한도에서 남은량을 확인할 수 있습니다.\n\n"
            "지금은 아래 「데이터 보기 ▼」에 있는 기본 해설(규칙 기반)을 참고하실 수 있습니다. "
            "내일이면 무료 한도가 다시 채워지는 경우가 많습니다."
        )
    short = str(exc).strip()
    if len(short) > 280:
        short = short[:280] + "…"
    return f"AI 해설을 만들지 못했습니다.\n\n{short}"


def _compact(obj: Any, *, limit: int = GEMINI_PROMPT_LIMIT) -> str:
    text = json.dumps(obj, ensure_ascii=False, indent=None, default=str)
    if len(text) > limit:
        return text[:limit] + "…(이하 생략)"
    return text


def _parse_sections(raw: str) -> List[Dict[str, str]]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        sections = data.get("sections") if isinstance(data, dict) else None
        if isinstance(sections, list) and sections:
            out: List[Dict[str, str]] = []
            for s in sections:
                if not isinstance(s, dict):
                    continue
                out.append(
                    {
                        "id": str(s.get("id") or ""),
                        "title": str(s.get("title") or ""),
                        "content": str(s.get("content") or "").strip(),
                    }
                )
            if out:
                return out
    except json.JSONDecodeError:
        pass
    return [{"id": "full", "title": "맞춤 해설", "content": text}]


def _call_gemini(system: str, user: str) -> str:
    last_err: Optional[BaseException] = None
    for name in _gemini_model_names():
        try:
            model = _gemini_model(system, name)
            resp = model.generate_content(user)
            return str(getattr(resp, "text", None) or "")
        except Exception as e:
            last_err = e
            if not _is_quota_error(e):
                raise RuntimeError(_friendly_api_error(e)) from e
    raise RuntimeError(_friendly_api_error(last_err or RuntimeError("quota")))


def _call_llm(system: str, user: str) -> str:
    provider = active_provider()
    if provider == "gemini":
        return _call_gemini(system, user)
    if provider == "anthropic":
        client = _anthropic_client()
        msg = client.messages.create(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts: List[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                parts.append(getattr(block, "text", "") or "")
        return "".join(parts)
    raise RuntimeError(AI_UNAVAILABLE_MESSAGE)


def _stream_llm(system: str, user: str) -> Iterator[str]:
    provider = active_provider()
    if provider == "gemini":
        last_err: Optional[BaseException] = None
        for name in _gemini_model_names():
            try:
                model = _gemini_model(system, name)
                resp = model.generate_content(user, stream=True)
                for chunk in resp:
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
                return
            except Exception as e:
                last_err = e
                if not _is_quota_error(e):
                    raise RuntimeError(_friendly_api_error(e)) from e
        raise RuntimeError(_friendly_api_error(last_err or RuntimeError("quota")))
    if provider == "anthropic":
        client = _anthropic_client()
        with client.messages.stream(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text
        return
    raise RuntimeError(AI_UNAVAILABLE_MESSAGE)


def _base_context(saju_data: Dict[str, Any], user_name: Optional[str] = None) -> str:
    meta = saju_data.get("meta") or {}
    return _compact(
        {
            "이름": user_name or "",
            "성별": meta.get("gender_for_daewoon"),
            "양력": saju_data.get("solar"),
            "음력": saju_data.get("lunar"),
            "팔자": saju_data.get("eight_char_string"),
            "일간": saju_data.get("day_master"),
            "일간한글": saju_data.get("day_master_kr"),
            "일간오행": saju_data.get("day_master_element"),
            "기준세운연도": meta.get("sewoon_center_applied"),
            "기준월운연도": meta.get("wolwoon_center_applied"),
            "사주원국": saju_data.get("pillars"),
        }
    )


def _wonkuk_payload(saju_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "사주": saju_data.get("pillars"),
        "십신_천간": saju_data.get("sipsin_stems"),
        "십신_전체": saju_data.get("sipsin_full"),
        "지장간": saju_data.get("jijanggan"),
        "십이운성": saju_data.get("sibiunsung"),
        "오행": saju_data.get("ohaeng"),
        "합충요약": (saju_data.get("chung_pa_hae") or {}).get("관계_상세_전체"),
    }


def _hapchung_payload(saju_data: Dict[str, Any]) -> Dict[str, Any]:
    cp = saju_data.get("chung_pa_hae") or {}
    return {
        "관계_전체": cp.get("관계_상세_전체"),
        "원국_충": cp.get("원국_충"),
        "원국_파": cp.get("원국_파"),
        "원국_해": cp.get("원국_해"),
        "원국_형": cp.get("원국_형"),
        "원국_합": cp.get("원국_합"),
        "세운_대입": cp.get("세운_대입"),
        "복음": cp.get("복음"),
        "기준세운": saju_data.get("sewoon_nearby"),
        "세운심층_올해": _current_sewoon_row(saju_data),
    }


def _current_sewoon_row(saju_data: Dict[str, Any]) -> Any:
    center = (saju_data.get("meta") or {}).get("sewoon_center_applied")
    deep = saju_data.get("세운_심층") or {}
    for row in deep.get("연도별") or []:
        if row.get("연도") == center:
            return row
    for row in saju_data.get("sewoon") or []:
        if row.get("연도") == center:
            return row
    return None


def _yongsin_payload(saju_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "용신분석": saju_data.get("yongsin"),
        "오행": saju_data.get("ohaeng"),
    }


def _daewoon_payload(saju_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "대운": saju_data.get("daewoon"),
        "세운_근방": saju_data.get("sewoon_nearby"),
        "세운_심층": saju_data.get("세운_심층"),
        "월운표": saju_data.get("월운표"),
        "일운": saju_data.get("일운"),
        "타임라인": saju_data.get("통합_타임라인"),
        "올해세운": _current_sewoon_row(saju_data),
    }


def _jonghap_payload(saju_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "분석_카테고리": saju_data.get("분석_카테고리"),
        "원국_스토리텔링": saju_data.get("원국_스토리텔링"),
        "용신": saju_data.get("yongsin"),
        "합충핵심": (saju_data.get("chung_pa_hae") or {}).get("관계_상세_전체"),
        "신살요약": saju_data.get("sinsal"),
        "대운요약": (saju_data.get("daewoon") or {}).get("cycles"),
    }


def _sinsal_payload(saju_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"신살": saju_data.get("sinsal")}


_PAYLOAD_BUILDERS = {
    "wonkuk": _wonkuk_payload,
    "hapchung": _hapchung_payload,
    "yongsin": _yongsin_payload,
    "daewoon": _daewoon_payload,
    "jonghap": _jonghap_payload,
    "sinsal": _sinsal_payload,
}

TAB_SPECS: Dict[str, str] = {
    "wonkuk": """
【TAB 1 원국】 다음 섹션을 모두 JSON sections로 작성하라.

[1-1] id=1-1 title=사주 한줄 핵심 요약 — 팔자 전체 인생 톤을 시처럼 한 블록
[1-2] id=1-2 title=일간 성격 — 일간 오행·한글을 비유로 성격·강점·약점
[1-3] id=1-3 title=년주 · 초년과 부모 — 년주 간지·십신·충합 근거
[1-4] id=1-4 title=월주 · 청년과 직업 — 월주·직장·사회생활
[1-5] id=1-5 title=일주 · 본인과 배우자 — 일주·건강·가정
[1-6] id=1-6 title=시주 · 말년과 자녀 — 시주·말년·후배
[1-7] id=1-7 title=지장간 · 숨겨진 내면 — 지장gan 데이터만, 용어설명 금지
[1-8] id=1-8 title=오행 맞춤 해설 — 과다·결핍·신체 연결
""".strip(),
    "hapchung": """
【TAB 2 합충】 데이터에 있는 관계만 다룬다. 없는 충·파·해·합은 쓰지 않는다.

[2-1] id=2-1-chong title=충(沖) 맞춤 해설 — 각 충마다 인생 패턴·발동 시기·대처(✅ 포함)
[2-2] id=2-2-po title=파(破) 맞춤 해설
[2-3] id=2-3-hai title=해(害) 맞춤 해설
[2-4] id=2-4-hap title=합(合)·육합·천간합 — 발견된 합만
[2-5] id=2-5-sewoon title=올해·세운 대입 충파해 — 기준연도 세운과 원국 상호작용, 월별 주의 시기
""".strip(),
    "yongsin": """
【TAB 3 용신】

[3-1] id=3-1 title=신강·신약 — 점수·판단·생활 속 체감
[3-2] id=3-2 title=용신 — 구원 오행·언제 살아나는지
[3-3] id=3-3 title=희신
[3-4] id=3-4 title=기신 — 조심 시기·관계
[3-5] id=3-5 title=맞춤 직업·환경 — 용신·희신 오행 기반 추천·주의
[3-6] id=3-6 title=세운별 강약 흐름 — 세운_강약_해설 데이터 활용 요약
""".strip(),
    "daewoon": """
【TAB 4 대운·세운·월·일】

[4-1] id=4-1 title=대운 스토리 — cycles 각 대운마다 나이·간지·인생 테마
[4-2] id=4-2 title=올해 세운 상세 — 직업·재물·애정·건강·중요한 달(이모지)
[4-3] id=4-3 title=월운 스토리 — 월별 2~3문장, 단순 길흉 금지
[4-4] id=4-4 title=오늘 일운 — 일운 데이터 기준 하루 조언·좋은 시간대
""".strip(),
    "jonghap": """
【TAB 5 종합】 유명 역술가가 쓴 듯한 서사체.

[5-1] id=5-1 title=인생 전체 스토리 — 가장 먼저 눈에 들어오는 구조부터
[5-2] id=5-2 title=연애·결혼
[5-3] id=5-3 title=직업·재물
[5-4] id=5-4 title=건강
[5-5] id=5-5 title=대인관계
[5-6] id=5-6 title=이 사주의 핵심 메시지 — 희망적 마무리
""".strip(),
    "sinsal": """
【TAB 6 신살】 "역마살: 이동 많다" 식 한 줄 정의 금지. 이 사람 사주에 있는 신살만.

[6-1] id=6-1 title=보유 신살 맞춤 — 길신·특수살 각각 스토리
[6-2] id=6-2 title=흉살 맞춤 — 현대적 해석·주의 시기
[6-3] id=6-3 title=길신·귀인 — 희망적 활용법
""".strip(),
}


def _run_interpret(
    saju_data: Dict[str, Any],
    *,
    tab: str,
    section_spec: str,
    data_payload: Dict[str, Any],
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    tab_n = normalize_tab(tab)
    if not is_ai_available():
        return unavailable_response(tab=tab_n)
    cache_key = ai_cache.chart_cache_key(saju_data)
    if force_refresh:
        ai_cache.delete_cached(cache_key, tab_n)
    cached = None if force_refresh else ai_cache.get_cached(cache_key, tab_n)
    if cached and cached.get("sections"):
        return {
            "ok": True,
            "tab": tab_n,
            "sections": cached["sections"],
            "from_cache": True,
            "cache_key": cache_key,
            "usage": ai_usage.usage_status(cache_key, tier=tier),
        }

    allowed, msg = ai_usage.check_and_consume(cache_key, tier=tier, bypass_cache=True)
    if not allowed:
        return {"ok": False, "error": "daily_limit", "message": msg, "usage": ai_usage.usage_status(cache_key, tier=tier)}

    system = COMMON_RULES
    user = (
        f"{section_spec}\n\n"
        f"【이 사람 기본 정보】\n{_base_context(saju_data, user_name)}\n\n"
        f"【계산 데이터】\n{_compact(data_payload)}\n"
    )
    raw = _call_llm(system, user)
    sections = _parse_sections(raw)
    body = {"sections": sections, "raw": raw}
    ai_cache.set_cached(cache_key, tab_n, body)
    return {
        "ok": True,
        "tab": tab_n,
        "sections": sections,
        "from_cache": False,
        "cache_key": cache_key,
        "usage": ai_usage.usage_status(cache_key, tier=tier),
    }


def interpret_wonkuk_full(
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    return _run_interpret(
        saju_data,
        tab="wonkuk",
        section_spec=TAB_SPECS["wonkuk"],
        data_payload=_wonkuk_payload(saju_data),
        user_name=user_name,
        force_refresh=force_refresh,
        tier=tier,
    )


def interpret_hapchung_full(
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    return _run_interpret(
        saju_data,
        tab="hapchung",
        section_spec=TAB_SPECS["hapchung"],
        data_payload=_hapchung_payload(saju_data),
        user_name=user_name,
        force_refresh=force_refresh,
        tier=tier,
    )


def interpret_yongsin_full(
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    return _run_interpret(
        saju_data,
        tab="yongsin",
        section_spec=TAB_SPECS["yongsin"],
        data_payload=_yongsin_payload(saju_data),
        user_name=user_name,
        force_refresh=force_refresh,
        tier=tier,
    )


def interpret_daewoon_sewoon_full(
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    return _run_interpret(
        saju_data,
        tab="daewoon",
        section_spec=TAB_SPECS["daewoon"],
        data_payload=_daewoon_payload(saju_data),
        user_name=user_name,
        force_refresh=force_refresh,
        tier=tier,
    )


def interpret_jonghap_full(
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    return _run_interpret(
        saju_data,
        tab="jonghap",
        section_spec=TAB_SPECS["jonghap"],
        data_payload=_jonghap_payload(saju_data),
        user_name=user_name,
        force_refresh=force_refresh,
        tier=tier,
    )


def interpret_sinsal_full(
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    return _run_interpret(
        saju_data,
        tab="sinsal",
        section_spec=TAB_SPECS["sinsal"],
        data_payload=_sinsal_payload(saju_data),
        user_name=user_name,
        force_refresh=force_refresh,
        tier=tier,
    )


_INTERPRETERS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "wonkuk": interpret_wonkuk_full,
    "hapchung": interpret_hapchung_full,
    "yongsin": interpret_yongsin_full,
    "daewoon": interpret_daewoon_sewoon_full,
    "jonghap": interpret_jonghap_full,
    "sinsal": interpret_sinsal_full,
}


def interpret_tab(
    tab: str,
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Dict[str, Any]:
    tab_n = normalize_tab(tab)
    fn = _INTERPRETERS[tab_n]
    return fn(saju_data, user_name=user_name, force_refresh=force_refresh, tier=tier)


def stream_interpret_tab(
    tab: str,
    saju_data: Dict[str, Any],
    *,
    user_name: Optional[str] = None,
    force_refresh: bool = False,
    tier: str = "free",
) -> Generator[Dict[str, Any], None, None]:
    """SSE용 이벤트 생성 (실시간 Claude 스트리밍)."""
    tab_n = normalize_tab(tab)
    if not is_ai_available():
        yield {"type": "unavailable", **unavailable_response(tab=tab_n)}
        return
    cache_key = ai_cache.chart_cache_key(saju_data)

    if force_refresh:
        ai_cache.delete_cached(cache_key, tab_n)

    if not force_refresh:
        cached = ai_cache.get_cached(cache_key, tab_n)
        if cached and cached.get("sections"):
            yield {"type": "cached", "sections": cached["sections"]}
            yield {"type": "done", "from_cache": True, "usage": ai_usage.usage_status(cache_key, tier=tier)}
            return

    allowed, msg = ai_usage.check_and_consume(cache_key, tier=tier, bypass_cache=True)
    if not allowed:
        yield {"type": "error", "error": "daily_limit", "message": msg}
        return

    user = (
        f"{TAB_SPECS[tab_n]}\n\n"
        f"【이 사람 기본 정보】\n{_base_context(saju_data, user_name)}\n\n"
        f"【계산 데이터】\n{_compact(_PAYLOAD_BUILDERS[tab_n](saju_data))}\n"
    )

    status_msgs = [
        "🔮 사주를 읽고 있습니다...",
        "✨ 당신만의 해설을 작성 중입니다...",
        "📖 거의 다 됐습니다...",
    ]
    for i, sm in enumerate(status_msgs):
        if i == 0:
            yield {"type": "status", "message": sm}
        else:
            yield {"type": "status", "message": sm, "phase": i}

    buf: List[str] = []
    try:
        for chunk in _stream_llm(COMMON_RULES, user):
            buf.append(chunk)
            yield {"type": "delta", "text": chunk}
    except Exception as e:
        yield {"type": "error", "error": "api_error", "message": _friendly_api_error(e)}
        return

    raw = "".join(buf)
    sections = _parse_sections(raw)
    ai_cache.set_cached(cache_key, tab_n, {"sections": sections, "raw": raw})
    yield {
        "type": "done",
        "sections": sections,
        "from_cache": False,
        "usage": ai_usage.usage_status(cache_key, tier=tier),
    }
