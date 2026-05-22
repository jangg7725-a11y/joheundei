# -*- coding: utf-8 -*-
"""만세력 UI용 한글 표기·카드/본문 표시 필드 생성."""

from __future__ import annotations

import re
from typing import Any

# 카테고리 탭 포켓 카드에서 숨길 입문 문구 (전역)
GENERIC_BEGINNER_SNIPPETS: frozenset[str] = frozenset(
    {
        "사주팔자의 기초 이론입니다. 천간·지지·오행의 관계를 이해하면 내 사주를 스스로 분석할 수 있습니다.",
        "포켓박스 사주팔자의 기초 이론입니다. 천간·지지·오행의 관계를 이해하면 내 사주를 스스로 분석할 수 있습니다.",
    }
)

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_PAREN_KR_RE = re.compile(r"^(.+?)\([^)]+\)$")

_STEM_KR = {
    "甲": "갑",
    "乙": "을",
    "丙": "병",
    "丁": "정",
    "戊": "무",
    "己": "기",
    "庚": "경",
    "辛": "신",
    "壬": "임",
    "癸": "계",
}
_BRANCH_KR = {
    "子": "자",
    "丑": "축",
    "寅": "인",
    "卯": "묘",
    "辰": "진",
    "巳": "사",
    "午": "오",
    "未": "미",
    "申": "신",
    "酉": "유",
    "戌": "술",
    "亥": "해",
}

# 도메인 한자 → 한글 (긴 키 우선 매칭)
_HANJA_PHRASES: dict[str, str] = {
    # 절기·역법
    "立春": "입춘",
    "雨水": "우수",
    "驚蟄": "경칩",
    "春分": "춘분",
    "淸明": "청명",
    "穀雨": "곡우",
    "立夏": "입하",
    "小滿": "소만",
    "芒種": "망종",
    "夏至": "하지",
    "小暑": "소서",
    "大暑": "대서",
    "立秋": "입추",
    "處暑": "처서",
    "白露": "백로",
    "秋分": "추분",
    "寒露": "한로",
    "立冬": "입동",
    "小雪": "소설",
    "大雪": "대설",
    "冬至": "동지",
    "小寒": "소한",
    "大寒": "대한",
    "太陽過宮表": "태양과궁표",
    "八節三奇法": "팔절삼기법",
    "太陽到臨": "태양도림",
    "三奇": "삼기",
    "天上三奇": "천상삼기",
    "人中三奇": "인중삼기",
    "地下三奇": "지하삼기",
    "六十甲子": "육십갑자",
    "六甲常識": "육갑상식",
    "節氣": "절기",
    "中氣": "중기",
    "歲殺": "세살",
    "月破": "월파",
    "日破": "일파",
    "時破": "시파",
    # 명리
    "三災入命": "삼재입명",
    "三災": "삼재",
    "入命": "입명",
    "月建法": "월건법",
    "月建": "월건",
    "時法": "시법",
    "六親": "육친",
    "十神": "십신",
    "造命擇日": "조명택일",
    "地支藏干": "지지장간",
    "比肩": "비견",
    "劫財": "겁재",
    "食神": "식신",
    "傷官": "상관",
    "偏財": "편재",
    "正財": "정재",
    "偏官": "편관",
    "正官": "정관",
    "偏印": "편인",
    "正印": "정인",
    "紫白九星": "자백구성",
    "九宮": "구궁",
    "八節": "팔절",
    "起法": "기법",
    "順行": "순행",
    "逆行": "역행",
    # 혼인
    "婚姻門": "혼인문",
    "生氣福德": "생기복덕",
    "生氣": "생기",
    "福德": "복덕",
    "天醫": "천의",
    "絶體": "절체",
    "遊魂": "유혼",
    "禍害": "화해",
    "絶命": "절명",
    "歸魂": "귀혼",
    "合婚開閉法": "합혼개폐법",
    "婚姻凶年": "혼인흉년",
    "殺夫大忌月": "살부대기월",
    "嫁聚月": "가취월",
    "嫁娶凶日": "가취흉일",
    "寡宿殺": "과숙살",
    "喪夫喪妻殺": "상부상처살",
    "男女宮合法": "남녀궁합법",
    "納音五行": "납음오행",
    "宮合": "궁합",
    # 길흉·신살
    "吉神": "길신",
    "凶神": "흉신",
    "五虎": "오호",
    "六蛇": "육사",
    "九虎": "구호",
    "九坎": "구감",
    "遊禍": "유화",
    "陰日": "음일",
    "重日": "중일",
    "陰錯": "음착",
    "天賊": "천적",
    "血池": "혈지",
    "威池": "위지",
    "行旅行者": "행려행자",
    "五孤": "오고",
    "復日": "복일",
    "四廢": "사폐",
    "四離": "사리",
    "天德": "천덕",
    "月德": "월덕",
    "天赦": "천사",
    "玉堂": "옥당",
    "母倉": "모창",
    "陰德": "음덕",
    # 풍수·제례
    "陽宅": "양택",
    "陰宅": "음택",
    "坐向": "좌향",
    "葬禮": "장례",
    "祭祀": "제사",
    "祭需": "제수",
    "附錄": "부록",
    "大韓民曆": "대한민력",
    "明文堂": "명문당",
    # 행사·용어
    "宜": "의",
    "忌": "기",
    "大吉": "대길",
    "小吉": "소길",
    "凶": "흉",
    "吉": "길",
    "用事": "용사",
    "土王": "토왕",
    "陽曆": "양력",
    "陰曆": "음력",
    "舊": "구",
    "附": "부",
    "目錄": "목차",
    "一覽表": "일람표",
    "開": "개",
    "閉": "폐",
    "年": "년",
    "月": "월",
    "日": "일",
    "時": "시",
    "法": "법",
    "表": "표",
    "門": "문",
    "生": "생",
    "死": "사",
    "男": "남",
    "女": "여",
    "東": "동",
    "西": "서",
    "南": "남",
    "北": "북",
    "方": "방",
    "火": "화",
    "水": "수",
    "木": "목",
    "金": "금",
    "土": "토",
    "官": "관",
    "財": "재",
    "印": "인",
    "殺": "살",
    "運": "운",
    "命": "명",
    "擇": "택",
    "婚": "혼",
    "嫁": "가",
    "娶": "취",
    "喪": "상",
    "祭": "제",
    "葬": "장",
    "墓": "묘",
    "龍": "룡",
    "星": "성",
    "氣": "기",
    "德": "덕",
    "福": "복",
    "禍": "화",
    "害": "해",
    "破": "파",
    "合": "합",
    "冲": "충",
    "刑": "형",
    "害": "해",
    "旺": "왕",
    "相": "상",
    "休": "휴",
    "囚": "수",
    "死": "사",
}

# 천간·지지·갑자
for _s, _sk in _STEM_KR.items():
    _HANJA_PHRASES[_s] = _sk
for _b, _bk in _BRANCH_KR.items():
    _HANJA_PHRASES[_b] = _bk
for _s, _sk in _STEM_KR.items():
    for _b, _bk in _BRANCH_KR.items():
        _HANJA_PHRASES[_s + _b] = _sk + _bk

_SORTED_HANJA_KEYS: tuple[str, ...] = tuple(
    sorted(_HANJA_PHRASES.keys(), key=len, reverse=True)
)


def _hanja_ratio(text: str) -> float:
    if not text:
        return 0.0
    cjk = len(_CJK_RE.findall(text))
    return cjk / max(len(text), 1)


def _korean_head_from_translation(text: str) -> str:
    """korean_translation 첫 줄에서 한글 제목 추출."""
    if not text:
        return ""
    parts: list[str] = []
    for line in text.split("\n"):
        head = line.split(":")[0].strip()
        if not head:
            continue
        m = _PAREN_KR_RE.match(head)
        parts.append(m.group(1).strip() if m else head)
        if len(parts) >= 3:
            break
    return " · ".join(parts)


def display_title(item: dict[str, Any]) -> str:
    """카드·모달 제목용 한글."""
    sub = (item.get("sub_category") or "").strip()
    chapter = (item.get("chapter") or "").strip()
    kt_head = _korean_head_from_translation(item.get("korean_translation") or "")

    if sub and _hanja_ratio(chapter) >= 0.25:
        return sub
    if kt_head and _hanja_ratio(chapter) >= 0.2:
        return kt_head
    if sub:
        return sub
    if chapter and _hanja_ratio(chapter) < 0.35:
        return chapter
    return annotate_text(chapter) if chapter else sub or "만세력 항목"


def display_chapter_hanja(item: dict[str, Any]) -> str:
    """제목 아래 보조 한자 표기(있을 때만)."""
    chapter = (item.get("chapter") or "").strip()
    title = display_title(item)
    if not chapter or chapter == title:
        return ""
    if _hanja_ratio(chapter) < 0.15:
        return ""
    return chapter


def card_description(item: dict[str, Any]) -> str:
    """포켓 카드 요약 — 반복 입문 문구 제외."""
    beg = (item.get("beginner_explanation") or "").strip()
    if beg in GENERIC_BEGINNER_SNIPPETS:
        beg = ""
    for raw in (
        beg,
        (item.get("modern_interpretation") or "").strip(),
        (item.get("korean_translation") or "").strip(),
    ):
        if raw and raw not in GENERIC_BEGINNER_SNIPPETS:
            return raw[:160] + ("…" if len(raw) > 160 else "")
    return ""


def modal_beginner(item: dict[str, Any]) -> str:
    beg = (item.get("beginner_explanation") or "").strip()
    if beg in GENERIC_BEGINNER_SNIPPETS:
        return ""
    return beg


def display_body_primary(item: dict[str, Any]) -> str:
    """모달 상단 한글 해석."""
    chunks: list[str] = []
    kt = (item.get("korean_translation") or "").strip()
    mi = (item.get("modern_interpretation") or "").strip()
    if kt:
        chunks.append(kt)
    if mi and mi not in chunks:
        chunks.append(mi)
    return "\n\n".join(chunks)


def annotate_text(text: str) -> str:
    """한자 옆에 한글 병기. 이미 (한글)이 있으면 중복 생략."""
    if not text:
        return ""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "(" and out and out[-1] == ")":
            # 이미 병기된 괄호 구간은 그대로 통과
            j = text.find(")", i)
            if j == -1:
                out.append(text[i:])
                break
            out.append(text[i : j + 1])
            i = j + 1
            continue

        matched = False
        for key in _SORTED_HANJA_KEYS:
            if not text.startswith(key, i):
                continue
            end = i + len(key)
            if end < n and text[end] == "(":
                out.append(key)
                i = end
                matched = True
                break
            hangul = _HANJA_PHRASES[key]
            out.append(f"{key}({hangul})")
            i = end
            matched = True
            break
        if not matched:
            out.append(text[i])
            i += 1
    return "".join(out)


def display_original(item: dict[str, Any]) -> str:
    """원문 본문 — 한글 병기."""
    raw = (item.get("original_text") or "").strip()
    if not raw:
        return ""
    return annotate_text(raw)


def enrich_item(item: dict[str, Any]) -> dict[str, Any]:
    """API/UI용 표시 필드 부여."""
    out = dict(item)
    out["display_title"] = display_title(item)
    out["display_chapter_hanja"] = display_chapter_hanja(item)
    out["display_card_desc"] = card_description(item)
    out["display_body_primary"] = display_body_primary(item)
    out["display_original"] = display_original(item)
    out["display_beginner"] = modal_beginner(item)
    return out
