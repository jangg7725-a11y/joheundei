# -*- coding: utf-8 -*-
"""천간·지지·육십갑자·지장간·합충형파해 등 명식 기본 데이터."""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional, Tuple, TypedDict

# ---------------------------------------------------------------------------
# 1. 천간(天干) — 이름, 음양, 오행, 번호(1~10)
# ---------------------------------------------------------------------------

STEM_RECORDS: Tuple[Dict[str, Any], ...] = (
    {"name": "甲", "yin_yang": "양", "element": "목", "number": 1},
    {"name": "乙", "yin_yang": "음", "element": "목", "number": 2},
    {"name": "丙", "yin_yang": "양", "element": "화", "number": 3},
    {"name": "丁", "yin_yang": "음", "element": "화", "number": 4},
    {"name": "戊", "yin_yang": "양", "element": "토", "number": 5},
    {"name": "己", "yin_yang": "음", "element": "토", "number": 6},
    {"name": "庚", "yin_yang": "양", "element": "금", "number": 7},
    {"name": "辛", "yin_yang": "음", "element": "금", "number": 8},
    {"name": "壬", "yin_yang": "양", "element": "수", "number": 9},
    {"name": "癸", "yin_yang": "음", "element": "수", "number": 10},
)

STEMS: List[str] = [r["name"] for r in STEM_RECORDS]
STEM_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
STEM_ELEMENT = [r["element"] for r in STEM_RECORDS]
STEM_YIN_YANG = [r["yin_yang"] for r in STEM_RECORDS]

# ---------------------------------------------------------------------------
# 2. 지지(地支) — 이름, 음양, 오행, 번호, 계절, 월건(정월=인월), 시간대
# ---------------------------------------------------------------------------

BRANCH_RECORDS: Tuple[Dict[str, Any], ...] = (
    {
        "name": "子",
        "yin_yang": "양",
        "element": "수",
        "number": 1,
        "season": "겨울",
        "month_index": 11,
        "month_note": "동지월(十一月)",
        "time_range": "23:00–01:00",
    },
    {
        "name": "丑",
        "yin_yang": "음",
        "element": "토",
        "number": 2,
        "season": "겨울",
        "month_index": 12,
        "month_note": "납월(十二月)",
        "time_range": "01:00–03:00",
    },
    {
        "name": "寅",
        "yin_yang": "양",
        "element": "목",
        "number": 3,
        "season": "봄",
        "month_index": 1,
        "month_note": "정월(正月)",
        "time_range": "03:00–05:00",
    },
    {
        "name": "卯",
        "yin_yang": "음",
        "element": "목",
        "number": 4,
        "season": "봄",
        "month_index": 2,
        "month_note": "이월",
        "time_range": "05:00–07:00",
    },
    {
        "name": "辰",
        "yin_yang": "양",
        "element": "토",
        "number": 5,
        "season": "봄",
        "month_index": 3,
        "month_note": "삼월",
        "time_range": "07:00–09:00",
    },
    {
        "name": "巳",
        "yin_yang": "음",
        "element": "화",
        "number": 6,
        "season": "여름",
        "month_index": 4,
        "month_note": "사월",
        "time_range": "09:00–11:00",
    },
    {
        "name": "午",
        "yin_yang": "양",
        "element": "화",
        "number": 7,
        "season": "여름",
        "month_index": 5,
        "month_note": "오월",
        "time_range": "11:00–13:00",
    },
    {
        "name": "未",
        "yin_yang": "음",
        "element": "토",
        "number": 8,
        "season": "여름",
        "month_index": 6,
        "month_note": "유월",
        "time_range": "13:00–15:00",
    },
    {
        "name": "申",
        "yin_yang": "양",
        "element": "금",
        "number": 9,
        "season": "가을",
        "month_index": 7,
        "month_note": "칠월",
        "time_range": "15:00–17:00",
    },
    {
        "name": "酉",
        "yin_yang": "음",
        "element": "금",
        "number": 10,
        "season": "가을",
        "month_index": 8,
        "month_note": "팔월",
        "time_range": "17:00–19:00",
    },
    {
        "name": "戌",
        "yin_yang": "양",
        "element": "토",
        "number": 11,
        "season": "가을",
        "month_index": 9,
        "month_note": "구월",
        "time_range": "19:00–21:00",
    },
    {
        "name": "亥",
        "yin_yang": "음",
        "element": "수",
        "number": 12,
        "season": "겨울",
        "month_index": 10,
        "month_note": "시월",
        "time_range": "21:00–23:00",
    },
)

BRANCHES: List[str] = [r["name"] for r in BRANCH_RECORDS]
BRANCH_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
BRANCH_ELEMENT = [r["element"] for r in BRANCH_RECORDS]

# ---------------------------------------------------------------------------
# 3. 육십갑자 — 甲子 … 癸亥
# ---------------------------------------------------------------------------

JIA_ZI: List[str] = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]

NA_YIN = [
    "해중금", "해중금", "노대화", "노대화", "대림목", "대림목",
    "노변토", "노변토", "검봉금", "검봉금", "산두화", "산두화",
    "간유수", "간유수", "성두토", "성두토", "백랍금", "백랍금",
    "양류목", "양류목", "천상수", "천상수", "대역토", "대역토",
    "식등금", "식등금", "천간화", "천간화", "석류목", "석류목",
    "대해수", "대해수",
]

# ---------------------------------------------------------------------------
# 4. 지장간 — 지지별 여기·중기·정기 (비어 있으면 해당 기운 없음)
# ---------------------------------------------------------------------------

class JijangganTriple(TypedDict, total=False):
    여기: Optional[str]
    중기: Optional[str]
    정기: Optional[str]


JIJANGGAN_DETAIL: Dict[str, JijangganTriple] = {
    "子": {"여기": "壬", "중기": None, "정기": "癸"},
    "丑": {"여기": "辛", "중기": "癸", "정기": "己"},
    "寅": {"여기": "戊", "중기": "丙", "정기": "甲"},
    "卯": {"여기": None, "중기": None, "정기": "乙"},
    "辰": {"여기": "癸", "중기": "乙", "정기": "戊"},
    "巳": {"여기": "庚", "중기": "戊", "정기": "丙"},
    "午": {"여기": None, "중기": "己", "정기": "丁"},
    "未": {"여기": "乙", "중기": "丁", "정기": "己"},
    "申": {"여기": "戊", "중기": "壬", "정기": "庚"},
    "酉": {"여기": None, "중기": None, "정기": "辛"},
    "戌": {"여기": "丁", "중기": "辛", "정기": "戊"},
    "亥": {"여기": "甲", "중기": None, "정기": "壬"},
}

_JIJANG_ORDER_KEYS = ("정기", "중기", "여기")


def jijanggan_ordered(zhi: str) -> List[str]:
    """정기→중기→여기 순으로 토출되는 간 목록(실제 간만)."""
    triple = JIJANGGAN_DETAIL[zhi]
    return [triple[k] for k in _JIJANG_ORDER_KEYS if triple.get(k)]


# ---------------------------------------------------------------------------
# 5. 합(合)
# ---------------------------------------------------------------------------

CHEON_GAN_HAP: Tuple[Tuple[str, str], ...] = (
    ("甲", "己"),
    ("乙", "庚"),
    ("丙", "辛"),
    ("丁", "壬"),
    ("戊", "癸"),
)

SAN_HE_WATER: FrozenSet[str] = frozenset({"申", "子", "辰"})
SAN_HE_WOOD: FrozenSet[str] = frozenset({"亥", "卯", "未"})
SAN_HE_FIRE: FrozenSet[str] = frozenset({"寅", "午", "戌"})
SAN_HE_METAL: FrozenSet[str] = frozenset({"巳", "酉", "丑"})

SAN_HE_GROUPS: Tuple[Tuple[FrozenSet[str], str], ...] = (
    (SAN_HE_WATER, "수국"),
    (SAN_HE_WOOD, "목국"),
    (SAN_HE_FIRE, "화국"),
    (SAN_HE_METAL, "금국"),
)

LIU_HE: Tuple[Tuple[str, str], ...] = (
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
)

# ---------------------------------------------------------------------------
# 6. 충(沖)
# ---------------------------------------------------------------------------

CHONG_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
)

# ---------------------------------------------------------------------------
# 7. 파(破)
# ---------------------------------------------------------------------------

LIU_PO: Tuple[Tuple[str, str], ...] = (
    ("子", "酉"),
    ("午", "卯"),
    ("巳", "申"),
    ("寅", "亥"),
    ("辰", "丑"),
    ("戌", "未"),
)

# ---------------------------------------------------------------------------
# 8. 해(害)
# ---------------------------------------------------------------------------

LIU_HAI: Tuple[Tuple[str, str], ...] = (
    ("子", "未"),
    ("丑", "午"),
    ("寅", "巳"),
    ("卯", "辰"),
    ("申", "亥"),
    ("酉", "戌"),
)

# ---------------------------------------------------------------------------
# 9. 형(刑)
# ---------------------------------------------------------------------------

XING_SAN_INSAM: FrozenSet[str] = frozenset({"寅", "巳", "申"})
XING_SAN_GOJI: FrozenSet[str] = frozenset({"丑", "戌", "未"})
XING_SANG_JAMYO: FrozenSet[str] = frozenset({"子", "卯"})
XING_ZI_BRANCHES: FrozenSet[str] = frozenset({"辰", "午", "酉", "亥"})

SAN_XING_GROUPS = [
    set(XING_SAN_INSAM),
    set(XING_SAN_GOJI),
    set(XING_SANG_JAMYO),
]


def stem_index(gan: str) -> int:
    return STEMS.index(gan)


def branch_index(zhi: str) -> int:
    return BRANCHES.index(zhi)


def stem_record(gan: str) -> Dict[str, Any]:
    return STEM_RECORDS[stem_index(gan)]


def branch_record(zhi: str) -> Dict[str, Any]:
    return BRANCH_RECORDS[branch_index(zhi)]


def jiazi_index(pillar: str) -> int:
    if len(pillar) != 2:
        raise ValueError("기둥은 두 글자(간+지)여야 합니다.")
    return JIA_ZI.index(pillar)


def pillar_from_offset(month_pillar: str, offset: int) -> str:
    idx = jiazi_index(month_pillar)
    return JIA_ZI[(idx + offset) % 60]


def element_of_stem(gan: str) -> str:
    return STEM_ELEMENT[stem_index(gan)]


def element_of_branch(zhi: str) -> str:
    return BRANCH_ELEMENT[branch_index(zhi)]


def yin_yang_stem(gan: str) -> str:
    return STEM_YIN_YANG[stem_index(gan)]


def nayin_for_pillar(pillar: str) -> str:
    return NA_YIN[jiazi_index(pillar) // 2]


def pillar_label_kr(gan: str, zhi: str) -> str:
    return STEM_KR[stem_index(gan)] + BRANCH_KR[branch_index(zhi)]


def cheon_gan_hap_partner(gan: str) -> str:
    """천간합 상대 간."""
    for a, b in CHEON_GAN_HAP:
        if gan == a:
            return b
        if gan == b:
            return a
    raise ValueError(f"천간합에 없는 간입니다: {gan}")
