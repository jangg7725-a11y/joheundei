# -*- coding: utf-8 -*-
"""카드별 핵심 이미지 — temporal·core 생성용."""

from __future__ import annotations

from typing import Any

# 카드별 light/shadow 한 줄 (종합운 이미지 요약). 없으면 본문에서 추출.
CARD_CORE: dict[str, dict[str, str]] = {
    "01": {"light": "눈에 안 보여도 준비는 진행 중", "shadow": "준비만 하고 실행을 미루는 상태"},
    "02": {"light": "작은 시작이 큰 변화를 부른다", "shadow": "시작의 두려움으로 주저하는 상태"},
    "03": {"light": "뿌리 깊은 성장과 안정", "shadow": "고집으로 유연함이 줄어든 상태"},
    "04": {"light": "마음을 드러내 표현할 때", "shadow": "감정을 숨기며 답답한 상태"},
    "05": {"light": "노력의 결실을 거두는 때", "shadow": "성급함으로 결실을 놓칠 수 있음"},
    "06": {"light": "기반을 다지고 받쳐 주는 힘", "shadow": "뿌리에만 매달려 확장이 막힘"},
    "07": {"light": "변화의 바람이 불어온다", "shadow": "방향 없는 바람에 흔들리는 상태"},
    "08": {"light": "함께 자라는 공동체의 힘", "shadow": "숲에 갇혀 개별성을 잃은 상태"},
    "09": {"light": "촉촉한 기회와 회복", "shadow": "감정이 넘쳐 균형이 흔들림"},
    "10": {"light": "밝게 드러나는 활력", "shadow": "태양에 가려 그림자를 못 봄"},
    "11": {"light": "작은 빛이 어둠을 밝힌다", "shadow": "불안으로 빛이 흔들리는 상태"},
    "12": {"light": "열정이 타오르며 변화를 만든다", "shadow": "불꽃이 금방 꺼질 수 있음"},
    "13": {"light": "기쁨과 축하의 에너지", "shadow": "과한 기대로 실망이 따를 수 있음"},
    "14": {"light": "하루를 정리하는 따뜻한 마무리", "shadow": "노을처럼 무기력하게 기울어짐"},
    "15": {"light": "순간의 깨달음과 돌파", "shadow": "충격에 흔들려 균형이 깨짐"},
    "16": {"light": "은은한 직관과 감수성", "shadow": "막연한 불안이 커지는 밤"},
    "17": {"light": "따뜻한 연결과 위로", "shadow": "너무 익숙해 안주하는 상태"},
    "18": {"light": "길을 밝히는 안내", "shadow": "빛만 따라 실속을 놓침"},
    "19": {"light": "넓은 땅 위에 서는 안정", "shadow": "무거운 책임에 눌린 상태"},
    "20": {"light": "높은 곳에서 바라보는 시야", "shadow": "고지에서 고립된 느낌"},
    "21": {"light": "꾸준한 수확과 실속", "shadow": "반복에 지쳐 의미를 잃음"},
    "22": {"light": "대지의 보호와 치유", "shadow": "답답함에 갇혀 움직임이 줄음"},
    "23": {"light": "단단함으로 버티는 힘", "shadow": "굳어져 유연함이 떨어짐"},
    "24": {"light": "돌아가 쉬며 충전할 때", "shadow": "안주하며 바깥으로 나서기를 망설임"},
    "25": {"light": "막힌 곳을 잇는 연결", "shadow": "소통이 끊겨 고립된 상태"},
    "26": {"light": "방향이 보이고 길이 열린다", "shadow": "갈림길에서 헤매는 상태"},
    "27": {"light": "깊은 곳에서 고른 기운이 오른다", "shadow": "보이지 않는 걱정이 쌓인 상태"},
    "28": {"light": "결단과 정리의 칼날", "shadow": "날이 무뎌져 결단이 늦음"},
    "29": {"light": "숨은 가치가 드러난다", "shadow": "겉치레에만 매달림"},
    "30": {"light": "진실을 비추는 거울", "shadow": "자기비하로 시야가 흐려짐"},
    "31": {"light": "균형과 공정한 판단", "shadow": "저울이 기울어 편향된 상태"},
    "32": {"light": "변화를 알리는 울림", "shadow": "경고를 듣지 못한 상태"},
    "33": {"light": "막힌 문을 여는 열쇠", "shadow": "열쇠를 잃고 막막한 상태"},
    "34": {"light": "스스로를 지키는 방패", "shadow": "방어가 지나쳐 닫힌 상태"},
    "35": {"light": "멀리서 비추는 희망", "shadow": "빛만 보고 발밑을 놓침"},
    "36": {"light": "성취와 권위의 정점", "shadow": "부담감으로 무거워진 상태"},
    "37": {"light": "흐름을 타고 나아간다", "shadow": "물살에 휩쓸려 방향 상실"},
    "38": {"light": "넓은 포용과 깊은 감정", "shadow": "파도에 삼켜질 만큼 과함"},
    "39": {"light": "맑고 섬세한 회복", "shadow": "작은 자극에도 예민한 상태"},
    "40": {"light": "씻겨 내려가며 정화된다", "shadow": "우울하게 가라앉는 기분"},
    "41": {"light": "아직 보이지 않는 것을 탐색", "shadow": "안개 속에서 방향을 잃음"},
    "42": {"light": "멈춤 속 정리와 절제", "shadow": "얼어붙어 움직임이 막힘"},
    "43": {"light": "큰 변화의 파도가 온다", "shadow": "파도에 뒤집힐 수 있음"},
    "44": {"light": "맑은 근원에서 다시 채워진다", "shadow": "원천이 막혀 고갈된 느낌"},
    "45": {"light": "감정의 리듬과 직관", "shadow": "파도처럼 기복이 큰 상태"},
    "46": {"light": "곧게 뻗는 시작의 기운", "shadow": "너무 곧아 부러질 수 있음"},
    "47": {"light": "유연하게 휘어 맞춘다", "shadow": "휘어지기만 하고 중심이 흔들림"},
    "48": {"light": "밝게 드러나는 열정", "shadow": "타오르다 금방 지침"},
    "49": {"light": "은은하고 따뜻한 불빛", "shadow": "내면 불안으로 흔들림"},
    "50": {"light": "넓게 받쳐 주는 대지", "shadow": "무거워 움직이기 어려움"},
    "51": {"light": "실속 있게 다져 가는 힘", "shadow": "답답하게 막힌 상태"},
    "52": {"light": "날카롭게 정리하고 자른다", "shadow": "날이 과해 상처가 남음"},
    "53": {"light": "섬세하게 다듬어 완성한다", "shadow": "지나친 완벽주의로 멈춤"},
    "54": {"light": "깊고 넓게 흐르는 지혜", "shadow": "넘쳐 경계가 흐려짐"},
    "55": {"light": "맑고 가벼운 감각", "shadow": "얕아져 깊이가 부족함"},
    "56": {"light": "부딪힘 속에서 새 길이 열린다", "shadow": "불필요한 충돌을 피해야 함"},
    "57": {"light": "인연이 맞물리며 조화가 생긴다", "shadow": "억지로 맞추려다 어긋남"},
    "58": {"light": "나에게 꼭 맞는 보호와 도움", "shadow": "기대가 커져 실망이 따름"},
    "59": {"light": "비워야 채워지는 순환", "shadow": "공허함에 휩쓸린 상태"},
    "60": {"light": "큰 흐름이 전환되는 문턱", "shadow": "변화를 견디기 어려운 시점"},
}


def build_temporal(
    card_id: str,
    name: str,
    keywords: list[str],
    *,
    light: str,
    shadow: str,
) -> dict[str, dict[str, str]]:
    k0 = keywords[0] if keywords else name
    k1 = keywords[1] if len(keywords) > 1 else k0
    return {
        "past": {
            "upright": (
                f"그동안 「{name}」처럼 {k0}의 흐름으로 살아온 시간이 있었어요. "
                f"{light} 쪽으로 기억을 돌아보면 패턴이 보여요."
            ),
            "reverse": (
                f"그동안 「{name}」의 막힌 면으로, {shadow} 패턴이 남아 있을 수 있어요. "
                f"익숙함에 머물렀던 부분을 짚어 볼 때예요."
            ),
        },
        "present": {
            "upright": (
                f"지금은 「{name}」이 말하듯 {light} 흐름이 중심이에요. "
                f"「{k1}」의 기운을 의식하면 리듬이 맞춰져요."
            ),
            "reverse": (
                f"지금은 속도를 늦추고 조율이 먼저예요. "
                f"「{name}」의 막힌 면, {shadow} 쪽을 다듬으면 흐름이 다시 살아날 수 있어요."
            ),
        },
        "future": {
            "upright": (
                f"앞으로는 「{k0}」을 바탕으로 문이 열리는 쪽으로 읽혀요. "
                f"{light} 방향으로 한 걸음씩 가면 충분해요."
            ),
            "reverse": (
                f"앞으로는 막혀 있던 흐름을 풀면 다시 열릴 여지가 있어요. "
                f"무리한 돌파보다 정리한 뒤 「{name}」의 방향으로 천천히 재출발해 보세요."
            ),
        },
    }


def core_for_card(card_id: str, upright_general: str, reverse_general: str) -> dict[str, str]:
    preset = CARD_CORE.get(card_id)
    if preset:
        return {"light": preset["light"], "shadow": preset["shadow"]}
    from saju.data.tarot.text_polish import first_clause

    return {
        "light": first_clause(upright_general, max_len=48),
        "shadow": first_clause(reverse_general, max_len=48),
    }


def essence_bundle(
    card_id: str,
    name: str,
    keyword: str,
    upright_general: str,
    reverse_general: str,
) -> dict[str, Any]:
    from saju.data.tarot.text_polish import parse_keywords

    keywords = parse_keywords(keyword)
    core = core_for_card(card_id, upright_general, reverse_general)
    temporal = build_temporal(
        card_id, name, keywords, light=core["light"], shadow=core["shadow"]
    )
    return {
        "keywords": keywords,
        "core": core,
        "temporal": temporal,
    }
