# -*- coding: utf-8 -*-
"""
원국·세운·대운 기준 충·파·해·형·합·복음(伏吟) 분석.

출력 항목 공통 형식:
``{ "관계", "글자", "위치", "강도", "해석" }``
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import ganji as gj

PILLAR_KEYS: Tuple[str, ...] = ("year", "month", "day", "hour")
ZHI_LABEL = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
JU_LABEL = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
GAN_LABEL = {"year": "년간", "month": "월간", "day": "일간", "hour": "시간"}

ZHI_BODY = {
    "子": "하체·신장·귀",
    "丑": "복부·비장",
    "寅": "목·어깨·간담",
    "卯": "목·손발·간",
    "辰": "비장·피부",
    "巳": "화·면부·심장",
    "午": "화·안구·순환",
    "未": "비위·소화",
    "申": "금·대장·호흡",
    "酉": "금·폐·치아",
    "戌": "화개·관절",
    "亥": "수·머리·비복",
}

ZHI_YUKCHIN_SHORT = {
    "year": "조상·환경·대외",
    "month": "부모·직업·사회",
    "day": "배우자·본인·내실",
    "hour": "자녀·말년·아랫사람",
}

# 세운·복음·충·해 — 사용자가 바로 이해할 수 있는 쉬운 해석 문장
_PILLAR_PLAIN = {
    "year": "가문·유년기·대외 이미지",
    "month": "부모·직장·사회생활·수입 기반",
    "day": "본인·배우자·건강·가정 안정",
    "hour": "자녀·말년·후배·실행·결과",
}


def _fuyin_sewoon_note(pillar_key: str, ju_label: str, year: Optional[int]) -> str:
    yr = f"{year}년 " if year else "올해 "
    theme = _PILLAR_PLAIN.get(pillar_key, ju_label)
    return (
        f"{yr}운의 기운이 태어날 때의 「{ju_label}」와 글자가 똑같습니다(복음). "
        f"예전에 겪었던 {theme} 쪽 일이 비슷한 모양으로 다시 나오기 쉬운 해입니다. "
        f"완전히 새로운 변화라기보다, ‘전에도 한 번 겪은 숙제’를 다시 풀게 되는 느낌으로 보시면 됩니다."
    )


def _fuyin_zhi_repeat_note(pillar_key: str, zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, ZHI_LABEL.get(pillar_key, ""))
    body = ZHI_BODY.get(zhi, "해당 부위")
    return (
        f"올해 지지 「{zhi}」가 원국 {ZHI_LABEL.get(pillar_key, '')}와 같습니다. "
        f"{theme}·{body} 관련 이슈가 작년과 비슷하게 반복될 수 있으니, 같은 실수·갈등을 두 번 하지 않도록 정리하는 것이 좋습니다."
    )


def _fuyin_daewoon_note(pillar_key: str, ju_label: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, ju_label)
    return (
        f"지금 대운 간지가 원국 「{ju_label}」와 같습니다. "
        f"10년 동안 {theme} 주제가 크게 반복·확대되는 시기로, 익숙한 패턴을 알아차리면 손해를 줄일 수 있습니다."
    )


def _sewoon_chong_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    body = ZHI_BODY.get(nat_zhi, "몸의 해당 부위")
    return (
        f"올해 기운(지지 {sew_zhi})이 원국 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})와 정면으로 부딪칩니다(충). "
        f"{theme} 자리에서 이사·이직·관계 갈등·급한 결정·환경 변화가 생기기 쉽습니다. "
        f"몸으로는 {body} 쪽(통증·피로·검진) 신호가 나올 수 있으니 평소보다 챙기세요."
    )


def _sewoon_po_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    body = ZHI_BODY.get(nat_zhi, "몸")
    return (
        f"올해 {sew_zhi}가 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})를 ‘깨뜨리는’ 기운(파)입니다. "
        f"{theme}에서 약속·계약·신뢰·수입 구조가 흔들리거나 갑자기 바뀔 수 있습니다. "
        f"{body} 피로·스트레스도 함께 올라갈 수 있습니다."
    )


def _sewoon_hai_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    body = ZHI_BODY.get(nat_zhi, "몸")
    return (
        f"올해 {sew_zhi}가 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})를 서서히 찌르는 기운(해)입니다. "
        f"{theme}에서 말다툼·서운함·질투·뒤에서 오는 방해가 은근히 쌓일 수 있습니다. "
        f"몸은 {body} 쪽 만성 피로·소화 불편을 먼저 신호로 느끼는 경우가 많습니다."
    )


def _sewoon_liuhe_note(pillar_key: str, sew_zhi: str, nat_zhi: str) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    return (
        f"올해 지지 {sew_zhi}와 원국 {ZHI_LABEL.get(pillar_key, '')}({nat_zhi})가 서로 잘 맞는 조합(육합)입니다. "
        f"{theme}에서 도움·협력·인연·만남이 늘고 일이 순조롭게 이어지기 쉽습니다. "
        f"너무 편해서 방심하지 않도록, 약속·돈·관계는 그래도 한 번씩 확인하는 것이 좋습니다."
    )


def _sewoon_cheongan_hap_note(
    pillar_key: str,
    sew_gan: str,
    nat_gan: str,
    elem: str,
    sipsin_label: str,
) -> str:
    theme = _PILLAR_PLAIN.get(pillar_key, "")
    sip_hint = {
        "비견": "형제·동료·경쟁",
        "겁재": "지출·동업·경쟁",
        "식신": "표현·기술·자녀",
        "상관": "말·창작·변화",
        "편재": "부수입·사업",
        "정재": "월급·안정 수입",
        "편관": "압박·이동·규칙",
        "정관": "직장·책임·명예",
        "편인": "학습·이단적 생각",
        "정인": "어머니·보호·자격",
    }.get(sipsin_label, sipsin_label or "해당 주제")
    return (
        f"올해 천간 {sew_gan}이 원국 {GAN_LABEL.get(pillar_key, '')} {nat_gan}과 합쳐집니다(천간합). "
        f"{theme}에서 「{sip_hint}」 쪽 일이 한데 묶여 진행되기 쉽고, 합화 기운은 {elem} 방향으로 흐릅니다. "
        f"혼자 밀기보다 같이 하는 일·계약·관계에서 성과가 나오기 쉬운 신호입니다."
    )


def _native_chong_note(k1: str, k2: str) -> str:
    t1, t2 = _PILLAR_PLAIN.get(k1, ""), _PILLAR_PLAIN.get(k2, "")
    if "day" in (k1, k2):
        return (
            f"원국 안에서 두 지지가 서로 정면으로 부딪칩니다(충). "
            f"배우자·가정·건강({t1}·{t2}) 쪽에서 갈등·이사·환경 변화가 반복되기 쉽습니다."
        )
    if "month" in (k1, k2):
        return (
            f"원국 안에서 두 지지가 충입니다. "
            f"직장·부모·사회생활({t1}·{t2}) 자리에서 마찰·이직·급한 변화가 생기기 쉽습니다."
        )
    return (
        f"원국 안에서 두 지지가 충입니다. "
        f"{t1}·{t2} 관련 환경·인연에서 예기치 않은 변동을 조심하세요."
    )


def _native_hai_note(k1: str, k2: str) -> str:
    if "day" in (k1, k2):
        return (
            "원국 안에서 두 지지가 해(害)입니다. "
            "배우자·가정·일상에서 서운함·오해·말다툼이 쌓이기 쉬우니, 오해는 바로 풀어두는 것이 좋습니다."
        )
    if "month" in (k1, k2):
        return (
            "원국 안에서 두 지지가 해입니다. "
            "직장·상사·부모 문제가 겉으로 드러나지 않고 은근히 신경 쓰이는 형태가 많습니다."
        )
    return (
        "원국 안에서 두 지지가 해입니다. "
        "대외·자녀·말년 쪽에서 작은 방해·질투·근심이 쌓일 수 있습니다."
    )


def _native_po_note(k1: str, k2: str) -> str:
    if "day" in (k1, k2):
        return (
            "원국 안에서 두 지지가 파(破)입니다. "
            "결혼·계약·신뢰·가정 안정이 한 번 깨졌다가 다시 잡히는 패턴이 나오기 쉽습니다."
        )
    if "month" in (k1, k2):
        return (
            "원국 안에서 두 지지가 파입니다. "
            "직장·수입·사업 구조가 갑자기 바뀌거나 약속이 깨지는 일을 조심하세요."
        )
    return (
        "원국 안에서 두 지지가 파입니다. "
        "계획·환경·말년 준비가 중간에 틀어지지 않도록 백업을 두는 것이 좋습니다."
    )


def _native_liuhe_note(k1: str, k2: str, za: str, zb: str) -> str:
    t1, t2 = _PILLAR_PLAIN.get(k1, ""), _PILLAR_PLAIN.get(k2, "")
    return (
        f"원국 안에서 {za}와 {zb}가 육합(六合)으로 맞습니다. "
        f"{t1}·{t2} 쪽 인연이 자연스럽게 이어지고, 서로 도움이 되는 관계가 만들어지기 쉽습니다."
    )


def _native_cheongan_hap_note(k1: str, k2: str, elem: str) -> str:
    t1, t2 = _PILLAR_PLAIN.get(k1, ""), _PILLAR_PLAIN.get(k2, "")
    return (
        f"원국 천간이 천간합으로 묶입니다. "
        f"{t1}·{t2} 주제가 {elem} 기운 쪽으로 한데 흘러, 협력·인연·제도 안에서 끌려 들어가기 쉽습니다."
    )


CHEON_GAN_HAP_RESULT = {
    frozenset(("甲", "己")): "토",
    frozenset(("乙", "庚")): "금",
    frozenset(("丙", "辛")): "수",
    frozenset(("丁", "壬")): "목",
    frozenset(("戊", "癸")): "화",
}

SAN_HE_ELEMENT = {"목국": "목", "화국": "화", "토국": "토", "금국": "금", "수국": "수"}

CHUNG_REMEDY: Dict[str, Dict[str, str]] = {
    "子午": {
        "보완": (
            "🔵 水(子) 방향 보완: "
            "북쪽 방향 활동, 파란색·검은색 활용, "
            "신장·방광 정기 검진. "
            "🔴 火(午) 방향 조절: "
            "과열·흥분 시 잠시 멈추고 "
            "수분 섭취로 열기를 식히세요. "
            "충 발동 해에는 큰 결정 전 "
            "하룻밤 숙고 습관을 들이세요"
        )
    },
    "丑未": {
        "보완": (
            "🟡 土 균형: 중앙·안정 에너지 보완. "
            "노란색·황토색 활용, "
            "위장·비장 관리 우선. "
            "변화보다 현재 자리를 지키는 "
            "전략이 충 해소에 유리합니다"
        )
    },
    "寅申": {
        "보완": (
            "🟢 木(寅) 보완: 동쪽 방향, 초록색, "
            "간·담 스트레칭 운동. "
            "⚪ 金(申) 조절: 결단 전 "
            "감정 점검 루틴 추가. "
            "이동·변화가 잦은 충이므로 "
            "핵심 기반(주거·직장)만큼은 "
            "안정적으로 유지하세요"
        )
    },
    "卯酉": {
        "보완": (
            "🟢 木(卯) 보완: 봄철 야외 활동, "
            "초록 식물 가까이 두기, "
            "간·눈 피로 관리. "
            "⚪ 金(酉) 조절: 완벽주의 내려놓기, "
            "폐·대장 건강 체크. "
            "감성과 이성 사이 균형이 핵심입니다"
        )
    },
    "辰戌": {
        "보완": (
            "🟡 土 과다 충: 변화 수용 연습이 필요합니다. "
            "환절기 위장·피부 관리 우선. "
            "고집보다 유연성을 의식적으로 키우고 "
            "명상·마음챙김으로 내면 안정을 찾으세요"
        )
    },
    "巳亥": {
        "보완": (
            "🔴 火(巳) 보완: 남쪽 방향, 붉은색, "
            "심장·순환 관리. "
            "🔵 水(亥) 조절: 충동 전 "
            "3초 멈춤 습관. "
            "행동 전 한번 더 생각하는 루틴이 "
            "이 충의 최고 보완법입니다"
        )
    },
}

PA_REMEDY: Dict[str, str] = {
    "子酉": "子丑합 또는 酉辰합 인연을 통해 균열을 메울 수 있습니다. 문서·계약 시 제3자 확인 습관을 들이세요",
    "午卯": "午未합 인연이 완충 역할을 합니다. 감정 폭발 전 글쓰기·그림 등 창작 활동으로 해소하세요",
    "巳申": "巳酉합으로 보완 가능합니다. 열정과 현실 사이 균형을 주기적으로 점검하세요",
    "寅亥": "寅午합으로 보완됩니다. 시작은 크게 하되 마무리 루틴을 반드시 만드세요",
    "辰丑": "辰酉합으로 보완됩니다. 저축·자산 관리를 정기적으로 점검하세요",
    "戌未": "戌午합으로 보완됩니다. 인간관계에서 기대치를 미리 조율하는 대화가 중요합니다",
}

HAI_REMEDY: Dict[str, str] = {
    "子未": "子丑합으로 해 기운을 완화할 수 있습니다. 재물 관련 문서는 반드시 서면으로 남기세요",
    "丑午": "丑子합 또는 午未합으로 보완됩니다. 가족 간 금전 거래는 명확한 합의가 필요합니다",
    "寅巳": "寅亥합으로 보완됩니다. 경쟁자보다 나의 속도에 집중하는 것이 해소법입니다",
    "卯辰": "卯戌합으로 보완됩니다. 문서·계약 검토를 꼼꼼히 하는 습관이 필요합니다",
    "申亥": "申子합으로 보완됩니다. 이동 시 안전 확인을 한 번 더 하는 습관을 들이세요",
    "酉戌": "酉辰합으로 보완됩니다. 신뢰 관계를 천천히 쌓아가는 것이 최선입니다",
}

SAMHAP_MISSING: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {
    "子辰申": {
        "수국": {
            "없으면_辰": {
                "부족글자": "辰",
                "의미": "水 기운의 마무리·결실 글자가 없어 끝맺음이 아쉬운 구조입니다",
                "보완": (
                    "辰이 포함된 대운·세운이 오는 해에 "
                    "수 기운(재물·지혜·유연성)이 완성됩니다. "
                    "그 해를 놓치지 마세요. "
                    "평소에는 辰 방향(동남쪽) 활동과 "
                    "저축·마무리 습관으로 보완하세요"
                ),
            },
            "없으면_申": {
                "부족글자": "申",
                "의미": "水 기운의 시작·추진 글자가 없어 새로운 도전의 동력이 부족합니다",
                "보완": (
                    "申운이 오는 해(寅年 이후 申年)에 "
                    "새로운 시작의 기회가 옵니다. "
                    "평소 서쪽 방향 활동과 "
                    "금속 액세서리로 기운을 보완하세요"
                ),
            },
        }
    },
    "寅午戌": {
        "화국": {
            "없으면_戌": {
                "부족글자": "戌",
                "의미": "火 기운의 마무리 글자가 없어 열정이 결실로 이어지기 어렵습니다",
                "보완": (
                    "戌운이 오는 해에 화 기운이 완성됩니다. "
                    "평소 끝맺음 루틴과 "
                    "마무리 체크리스트를 만드세요"
                ),
            },
        }
    },
    "丑巳酉": {
        "금국": {
            "없으면_丑": {
                "부족글자": "丑",
                "의미": "金 기운의 저장·완성 글자가 없어 결단력이 끝까지 유지되기 어렵습니다",
                "보완": (
                    "丑운이 오는 해에 금 기운이 완성됩니다. "
                    "평소 저축 습관과 "
                    "마무리 실행력을 키우세요"
                ),
            },
        }
    },
    "卯未亥": {
        "목국": {
            "없으면_未": {
                "부족글자": "未",
                "의미": "木 기운의 결실 글자가 없어 성장이 완전한 결실로 맺기 어렵습니다",
                "보완": (
                    "未운이 오는 해에 목 기운이 완성됩니다. "
                    "평소 남서쪽 방향 활동과 "
                    "꾸준한 성장 기록을 남기세요"
                ),
            },
        }
    },
}

# 세운·복음 보완 (sewoon.py 세운 분석과 동기화)
SEWOON_CHUNG_REMEDY: Dict[str, str] = {
    "복음": (
        "⚡ 복음 보완법:\n"
        "같은 실수를 반복하지 않도록 "
        "작년 이슈를 먼저 정리하세요. "
        "새로운 시작보다 "
        "기존 관계·일의 완성에 집중하고 "
        "중요한 변화는 복음 해를 피해 "
        "다음 해로 미루는 것이 유리합니다"
    ),
    "반음": (
        "⚡ 반음 보완법:\n"
        "모든 것이 흔들리는 느낌이지만 "
        "핵심 기반(주거·직업·건강)만 "
        "지키면 반드시 회복됩니다. "
        "이 해에는 현금 비중을 높이고 "
        "큰 투자·이동은 자제하세요"
    ),
}

SEWOON_PILLAR_REMEDY: Dict[str, str] = {
    "년지충": (
        "🔵 년지충 보완법:\n"
        "부모·가문 관련 이슈가 생길 수 있습니다. "
        "가족 건강 검진을 미리 챙기고 "
        "조상·부모님께 연락을 자주 하세요. "
        "이 해에는 고향 방문이 도움이 됩니다"
    ),
    "월지충": (
        "🔵 월지충 보완법:\n"
        "직업·사회생활 변화가 생기기 쉽습니다. "
        "이직·전직을 고려 중이라면 "
        "충 해소 월(합이 오는 달)을 골라 실행하세요. "
        "계약·문서는 반드시 검토 후 진행하세요"
    ),
    "일지충": (
        "🔵 일지충 보완법:\n"
        "배우자·건강·주거 변화가 생기기 쉽습니다. "
        "부부 대화를 늘리고 "
        "건강 검진을 이 해 상반기 안에 받으세요. "
        "큰 이사·이별 결정은 충동적으로 하지 마세요"
    ),
    "시지충": (
        "🔵 시지충 보완법:\n"
        "자녀·말년 관련 걱정이 생기기 쉽습니다. "
        "자녀와 대화를 늘리고 "
        "노후 준비를 점검하는 계기로 삼으세요"
    ),
    "세운해": (
        "🟡 세운해 보완법:\n"
        "보이지 않는 방해가 쌓이는 해입니다. "
        "인간관계에서 오해가 생기면 "
        "빠르게 대화로 풀고 "
        "재물 관련 문서는 반드시 서면으로 남기세요"
    ),
}

_PILLAR_KEY_BY_ZHI_LABEL = {v: k for k, v in ZHI_LABEL.items()}


def _relation_row(
    kind: str,
    glyphs: str,
    where: str,
    strength: str,
    note: str,
    *,
    remedy: Optional[str] = None,
    missing_char: Optional[str] = None,
    missing_meaning: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "관계": kind,
        "글자": glyphs,
        "위치": where,
        "강도": strength,
        "해석": note,
    }
    if remedy:
        row["보완법"] = remedy
    if missing_char is not None:
        row["부족한_글자"] = missing_char
        if missing_meaning:
            row["부족한_글자_의미"] = missing_meaning
    return row


def _zhi_pair_key(glyphs: str) -> Optional[str]:
    branches = [c for c in glyphs if c in gj.BRANCHES]
    if len(branches) < 2:
        return None
    ordered = sorted(branches[:2], key=gj.branch_index)
    return ordered[0] + ordered[1]


def _chung_remedy_for(glyphs: str) -> str:
    key = _zhi_pair_key(glyphs)
    if not key:
        return ""
    entry = CHUNG_REMEDY.get(key)
    return entry.get("보완", "") if entry else ""


def _po_remedy_for(glyphs: str) -> str:
    key = _zhi_pair_key(glyphs)
    return PA_REMEDY.get(key or "", "")


def _hai_remedy_for(glyphs: str) -> str:
    key = _zhi_pair_key(glyphs)
    return HAI_REMEDY.get(key or "", "")


def _samhap_tri_key(tri: frozenset) -> str:
    return "".join(sorted(tri, key=lambda z: gj.branch_index(z)))


def _samhap_partial_info(
    nation: str, tri: frozenset, inside: Set[str]
) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """삼합(두지) — 부족 글자·의미·보완·갱신 해석."""
    missing = tri - inside
    if len(missing) != 1:
        elem = SAN_HE_ELEMENT.get(nation, "")
        ordered = "".join(sorted(inside, key=lambda z: gj.branch_index(z)))
        note = (
            f"{elem} 성향의 삼합({ordered})이 있으나 "
            f"마지막 글자 「{list(missing)[0]}」이 없어 "
            f"완전한 결실까지 변수가 있습니다"
        )
        return None, None, "", note
    miss = list(missing)[0]
    tri_key = _samhap_tri_key(tri)
    entry = (
        SAMHAP_MISSING.get(tri_key, {})
        .get(nation, {})
        .get(f"없으면_{miss}", {})
    )
    elem = SAN_HE_ELEMENT.get(nation, "")
    ordered = "".join(sorted(inside, key=lambda z: gj.branch_index(z)))
    meaning = entry.get("의미") or f"{elem} 삼합의 마무리 글자가 부족합니다"
    remedy = entry.get("보완", "")
    note = (
        f"{elem} 성향의 삼합({ordered})이 있으나 "
        f"마지막 글자 「{miss}」이 없어 "
        f"완전한 결실까지 변수가 있습니다"
    )
    return miss, meaning, remedy, note


def _sewoon_pillar_remedy(pillar_key: str) -> str:
    return SEWOON_PILLAR_REMEDY.get(f"{ZHI_LABEL[pillar_key]}충", "")


def _fan_yin_rows(pillars: dict, sewoon_pillar: str, sewoon_year: Optional[int]) -> List[Dict[str, Any]]:
    """세운 지지가 원국 네 지지와 모두 충일 때 반음 행."""
    if len(sewoon_pillar) < 2:
        return []
    sz = sewoon_pillar[1]
    ch_set = _chong_set()
    hits = [
        k
        for k in PILLAR_KEYS
        if tuple(sorted((sz, pillars[k]["zhi"]))) in ch_set
    ]
    if len(hits) < 4:
        return []
    yr = f"{sewoon_year}년 " if sewoon_year else ""
    return [
        _relation_row(
            "반음(세운)",
            sewoon_pillar,
            f"{yr}세운 지지 {sz}가 원국 네 지지와 모두 충",
            "높음",
            "세운 지지가 년·월·일·시 네 궁 모두와 정면 충돌하는 극단 패턴입니다.",
            remedy=SEWOON_CHUNG_REMEDY.get("반음", ""),
        )
    ]


def _pairs_positions(keys: Sequence[str]) -> List[Tuple[str, str]]:
    return [(keys[i], keys[j]) for i in range(len(keys)) for j in range(i + 1, len(keys))]


def _chong_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.CHONG_PAIRS}


def _hai_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.LIU_HAI}


def _po_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.LIU_PO}


def _liu_he_set() -> Set[Tuple[str, str]]:
    return {tuple(sorted(p)) for p in gj.LIU_HE}


def _strength(keys_involved: Iterable[str]) -> str:
    ks = set(keys_involved)
    if "day" in ks:
        return "높음"
    if "month" in ks:
        return "중"
    return "참고"


def _chong_position_note(k1: str, k2: str) -> str:
    return _native_chong_note(k1, k2)


def _hai_position_note(k1: str, k2: str) -> str:
    return _native_hai_note(k1, k2)


def _po_position_note(k1: str, k2: str) -> str:
    return _native_po_note(k1, k2)


def _xing_note(kind_zh: str, k1: str, k2: str) -> str:
    ks = {k1, k2}
    day_hit = "day" in ks
    base_map = {
        "인사신 삼형": "관재·구설·시비에 노출되기 쉬운 무은지형입니다.",
        "축술미 삼형": "고집·형벌·부상·수술 운이 겹치기 쉬운 고지형입니다.",
        "자묘 상형": "예의·관계 예민도가 높아 구설로 번지기 쉬운 무례지형입니다.",
        "자형": "동일 지지 반복으로 같은 부위 긴장·사고·수술 이슈가 반복될 수 있습니다.",
    }
    core = base_map.get(kind_zh, "형살로 긴장·외상·수술·관재 소지를 함께 봅니다.")
    if day_hit:
        return f"{core} 일지 관여 시 본인·배우자 건강·관계 직결 신호가 강합니다."
    if "month" in ks:
        return f"{core} 월지 관여 시 직업·관직 쪽 형평·규정 리스크를 의식합니다."
    return core


def _san_xing_type(a: str, b: str) -> Optional[str]:
    if a == b and a in gj.XING_ZI_BRANCHES:
        return "자형"
    pair = {a, b}
    if pair <= gj.XING_SAN_INSAM and len(pair) == 2:
        return "인사신 삼형"
    if pair <= gj.XING_SAN_GOJI and len(pair) == 2:
        return "축술미 삼형"
    if pair == gj.XING_SANG_JAMYO:
        return "자묘 상형"
    return None


def analyze_native_chong(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    ch_set = _chong_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in ch_set:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]} ({glyphs})"
        strength = _strength((k1, k2))
        note = _chong_position_note(k1, k2)
        out.append(
            _relation_row(
                "충",
                glyphs,
                where,
                strength,
                note,
                remedy=_chung_remedy_for(glyphs),
            )
        )
    return out


def analyze_native_po(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    po_set = _po_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in po_set:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]}"
        strength = _strength((k1, k2))
        out.append(
            _relation_row(
                "파",
                glyphs,
                where,
                strength,
                _po_position_note(k1, k2),
                remedy=_po_remedy_for(glyphs),
            )
        )
    return out


def analyze_native_hai(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    hai_set = _hai_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in hai_set:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]}"
        strength = _strength((k1, k2))
        out.append(
            _relation_row(
                "해",
                glyphs,
                where,
                strength,
                _hai_position_note(k1, k2),
                remedy=_hai_remedy_for(glyphs),
            )
        )
    return out


def analyze_native_xing(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        xt = _san_xing_type(za, zb)
        if not xt:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]}"
        strength = _strength((k1, k2))
        note = _xing_note(xt, k1, k2)
        label = "형"
        if xt == "자형":
            label = "자형"
        out.append(_relation_row(label, glyphs, where, strength, note))
    # 세 지지 삼형 완성 여부 (원국 네 지지 안에서 세 개 동시 존재)
    zset = set(zhis.values())
    if gj.XING_SAN_INSAM <= zset:
        out.append(
            _relation_row(
                "삼형완성",
                "寅巳申",
                "원국 지지에 삼형 삼각 완성",
                "높음",
                "무은지형이 동시에 깔려 관재·구설·급박한 사건 소지가 한층 커집니다.",
            )
        )
    if gj.XING_SAN_GOJI <= zset:
        out.append(
            _relation_row(
                "삼형완성",
                "丑戌未",
                "원국 지지에 고지형 삼각 완성",
                "높음",
                "형벌·부상·수술·토목 재해 등 신체·현실 충격을 함께 봅니다.",
            )
        )
    return out


def analyze_native_he(pillars: dict) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    gans = {k: pillars[k]["gan"] for k in PILLAR_KEYS}

    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        g1, g2 = gans[k1], gans[k2]
        fs = frozenset((g1, g2))
        if fs not in CHEON_GAN_HAP_RESULT:
            continue
        elem = CHEON_GAN_HAP_RESULT[fs]
        glyphs = f"{g1}{g2}"
        where = f"{GAN_LABEL[k1]}–{GAN_LABEL[k2]} 천간합"
        strength = _strength((k1, k2))
        out.append(
            _relation_row(
                "천간합",
                glyphs,
                where,
                strength,
                _native_cheongan_hap_note(k1, k2, elem),
            )
        )

    zhis = {k: pillars[k]["zhi"] for k in PILLAR_KEYS}
    lh = _liu_he_set()
    for k1, k2 in _pairs_positions(list(PILLAR_KEYS)):
        za, zb = zhis[k1], zhis[k2]
        if tuple(sorted((za, zb))) not in lh:
            continue
        glyphs = f"{za}{zb}"
        where = f"{ZHI_LABEL[k1]}–{ZHI_LABEL[k2]} 육합"
        strength = _strength((k1, k2))
        e1, e2 = gj.element_of_branch(za), gj.element_of_branch(zb)
        out.append(
            _relation_row(
                "육합",
                glyphs,
                where,
                strength,
                _native_liuhe_note(k1, k2, za, zb),
            )
        )

    zset = set(zhis.values())
    for tri, nation in gj.SAN_HE_GROUPS:
        elem = SAN_HE_ELEMENT[nation]
        inside = zset & tri
        if len(inside) == 3:
            glyphs = "".join(sorted(inside, key=lambda z: gj.branch_index(z)))
            out.append(
                _relation_row(
                    "삼합(완성)",
                    glyphs,
                    f"원국 {nation} 삼합 성립",
                    "높음",
                    f"삼합이 성사되어 {elem} 방향 기운이 크게 뭉칩니다 — 해당 업·인연·재물축을 집중적으로 봅니다.",
                )
            )
        elif len(inside) == 2:
            ordered = "".join(sorted(inside, key=lambda z: gj.branch_index(z)))
            miss, miss_mean, remedy, note = _samhap_partial_info(nation, tri, inside)
            out.append(
                _relation_row(
                    "삼합(두지)",
                    ordered,
                    f"{nation} 삼합 중 둘만 존재",
                    "중",
                    note,
                    remedy=remedy,
                    missing_char=miss,
                    missing_meaning=miss_mean,
                )
            )

    return out


def _pillar_string(p: dict) -> str:
    return p.get("pillar") or (p["gan"] + p["zhi"])


def analyze_fuyin(
    pillars: dict,
    *,
    sewoon_pillar: Optional[str] = None,
    sewoon_year: Optional[int] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[Dict[str, str]]:
    """세운·대운 간지가 원국 주와 동일할 때 복음 신호."""
    out: List[Dict[str, str]] = []
    nat = {k: _pillar_string(pillars[k]) for k in PILLAR_KEYS}

    if sewoon_pillar:
        for k in PILLAR_KEYS:
            if sewoon_pillar == nat[k]:
                lbl = JU_LABEL[k]
                yr = f"{sewoon_year}년 " if sewoon_year else ""
                out.append(
                    _relation_row(
                        "복음(세운)",
                        sewoon_pillar,
                        f"{yr}세운이 {lbl}와 동일",
                        "중",
                        _fuyin_sewoon_note(k, lbl, sewoon_year),
                        remedy=SEWOON_CHUNG_REMEDY.get("복음", ""),
                    )
                )
            sz = sewoon_pillar[1] if len(sewoon_pillar) >= 2 else ""
            if sz and sz == pillars[k]["zhi"] and sewoon_pillar != nat[k]:
                out.append(
                    _relation_row(
                        "복음(지중복)",
                        sz,
                        f"세운 지지={sz}가 {ZHI_LABEL[k]}와 동일",
                        "참고",
                        _fuyin_zhi_repeat_note(k, sz),
                    )
                )

    if daewoon_cycles:
        for c in daewoon_cycles:
            gz = c.get("ganzhi") if isinstance(c, dict) else None
            if not gz:
                continue
            for k in PILLAR_KEYS:
                if gz == nat[k]:
                    age = f"{c.get('start_age')}~{c.get('end_age')}세" if isinstance(c, dict) else ""
                    out.append(
                        _relation_row(
                            "복음(대운)",
                            gz,
                            f"대운 {age}·{JU_LABEL[k]}",
                            "중",
                            _fuyin_daewoon_note(k, JU_LABEL[k]),
                        )
                    )
    return out


def analyze_sewoon_injection(
    pillars: dict,
    sewoon_pillar: str,
    *,
    sewoon_year: Optional[int] = None,
    day_master: Optional[str] = None,
) -> List[Dict[str, str]]:
    """세운 간지·천간과 원국의 충·파·해·육합·천간합."""
    if len(sewoon_pillar) < 2:
        return []
    sg, sz = sewoon_pillar[0], sewoon_pillar[1]
    dm = day_master or pillars.get("day", {}).get("gan", "")
    yr_note = f"{sewoon_year}년 세운 " if sewoon_year else "세운 "
    out: List[Dict[str, str]] = []

    ch_set = _chong_set()
    po_set = _po_set()
    hai_set = _hai_set()
    he_set = _liu_he_set()

    for k in PILLAR_KEYS:
        nz = pillars[k]["zhi"]
        pair = tuple(sorted((sz, nz)))
        pos_lbl = ZHI_LABEL[k]

        if pair in ch_set:
            pillar_remedy = _sewoon_pillar_remedy(k)
            out.append(
                _relation_row(
                    "세운충",
                    f"{sz}×{nz}",
                    f"{yr_note}지지 {sz}가 {pos_lbl}({nz})와 충",
                    "중",
                    _sewoon_chong_note(k, sz, nz),
                    remedy=pillar_remedy or _chung_remedy_for(f"{sz}{nz}"),
                )
            )
        if pair in po_set:
            out.append(
                _relation_row(
                    "세운파",
                    f"{sz}×{nz}",
                    f"{yr_note}{sz}가 {pos_lbl} 파",
                    "중",
                    _sewoon_po_note(k, sz, nz),
                )
            )
        if pair in hai_set:
            out.append(
                _relation_row(
                    "세운해",
                    f"{sz}×{nz}",
                    f"{yr_note}{sz}가 {pos_lbl} 해",
                    "중",
                    _sewoon_hai_note(k, sz, nz),
                    remedy=SEWOON_PILLAR_REMEDY.get("세운해", "") or _hai_remedy_for(f"{sz}{nz}"),
                )
            )
        if pair in he_set:
            out.append(
                _relation_row(
                    "세운육합",
                    f"{sz}{nz}",
                    f"{yr_note}지지 {sz}와 {pos_lbl}({nz}) 육합",
                    "중",
                    _sewoon_liuhe_note(k, sz, nz),
                )
            )

    if dm and sg:
        try:
            from . import sipsin as sp

            for k in PILLAR_KEYS:
                pg = pillars[k]["gan"]
                if pg == dm:
                    continue
                fs = frozenset((sg, pg))
                if fs not in CHEON_GAN_HAP_RESULT:
                    continue
                elem = CHEON_GAN_HAP_RESULT[fs]
                sip = sp.classify_sipsin(dm, pg)
                out.append(
                    _relation_row(
                        "세운천간합",
                        f"{sg}{pg}",
                        f"{yr_note}천간 {sg}와 {GAN_LABEL[k]} {pg} 합",
                        "중",
                        _sewoon_cheongan_hap_note(k, sg, pg, elem, sip),
                    )
                )
        except ImportError:
            pass

    return out


def analyze_relations_full(
    pillars: dict,
    *,
    sewoon_pillar: Optional[str] = None,
    sewoon_year: Optional[int] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """원국 + 옵션 세운·대운 통합."""
    sections = {
        "원국_충": analyze_native_chong(pillars),
        "원국_파": analyze_native_po(pillars),
        "원국_해": analyze_native_hai(pillars),
        "원국_형": analyze_native_xing(pillars),
        "원국_합": analyze_native_he(pillars),
        "복음": analyze_fuyin(
            pillars,
            sewoon_pillar=sewoon_pillar,
            sewoon_year=sewoon_year,
            daewoon_cycles=daewoon_cycles,
        ),
        "세운_대입": []
        if not sewoon_pillar
        else analyze_sewoon_injection(
            pillars,
            sewoon_pillar,
            sewoon_year=sewoon_year,
            day_master=pillars.get("day", {}).get("gan"),
        ),
    }

    flat: List[Dict[str, Any]] = []
    for key in (
        "원국_충",
        "원국_파",
        "원국_해",
        "원국_형",
        "원국_합",
        "복음",
        "세운_대입",
    ):
        for row in sections[key]:
            row2 = dict(row)
            row2["분류"] = key
            flat.append(row2)

    if sewoon_pillar:
        fan_rows = _fan_yin_rows(pillars, sewoon_pillar, sewoon_year)
        for row in fan_rows:
            row2 = dict(row)
            row2["분류"] = "세운_대입"
            sections["세운_대입"].append(row2)
            flat.append(row2)
        sections["세운_복음충"] = list(sections["복음"]) + list(sections["세운_대입"])
    else:
        sections["세운_복음충"] = []

    sections["관계_상세_전체"] = flat
    return sections


def analyze_branch_relations(
    pillars: dict,
    *,
    sewoon_pillar: Optional[str] = None,
    sewoon_year: Optional[int] = None,
    daewoon_cycles: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    - ``관계_상세_전체``: 표준 행 목록
    - ``충``·``파``·``해``·``형``·``합``·``복음``·``세운_대입``: 한 줄 문자열 (기존 UI)
    """
    full = analyze_relations_full(
        pillars,
        sewoon_pillar=sewoon_pillar,
        sewoon_year=sewoon_year,
        daewoon_cycles=daewoon_cycles,
    )

    def _one_line(r: Dict[str, str]) -> str:
        return f"[{r['관계']}] {r['글자']} @ {r['위치']} ({r['강도']}) — {r['해석']}"

    return {
        "관계_상세_전체": full["관계_상세_전체"],
        "세운_복음충": full.get("세운_복음충", []),
        "충": [_one_line(r) for r in full["원국_충"]],
        "파": [_one_line(r) for r in full["원국_파"]],
        "해": [_one_line(r) for r in full["원국_해"]],
        "형": [_one_line(r) for r in full["원국_형"]],
        "합": [_one_line(r) for r in full["원국_합"]],
        "복음": [_one_line(r) for r in full["복음"]],
        "세운_대입": [_one_line(r) for r in full["세운_대입"]],
    }
