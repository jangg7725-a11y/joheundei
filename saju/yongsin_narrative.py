# -*- coding: utf-8 -*-
"""용신 탭 맞춤 스토리·생활·직업 서사."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from . import ganji as gj
from . import sipsin as sp
from .yongsin import CONTROL_MAP, GENERATE_MAP, RESOURCE_MAP, _all_target_gans

EL_HANJA = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}

VERDICT_STORY: Dict[str, str] = {
    "신강": (
        "당신의 사주는 신강(身强) 구조입니다. "
        "일간의 기운이 주변보다 강해 "
        "추진력과 독립심이 뛰어나지만 "
        "때로 고집스럽고 타협이 어려울 수 있습니다. "
        "강한 기운을 적절히 발산·활용하는 것이 핵심입니다"
    ),
    "신약": (
        "당신의 사주는 신약(身弱) 구조입니다. "
        "주변 기운에 일간이 눌린 상태로 "
        "섬세하고 공감 능력이 뛰어나지만 "
        "혼자서는 지치기 쉬운 구조입니다. "
        "좋은 조력자를 만날 때 놀라운 능력을 발휘합니다"
    ),
    "중화": (
        "당신의 사주는 중화(中和)에 가까운 구조입니다. "
        "균형 잡힌 에너지로 다양한 상황에 잘 적응하고 "
        "극단적인 면이 적어 대인관계가 원만합니다"
    ),
}

YONG_STORY: Dict[str, Dict[str, str]] = {
    "목": {
        "의미": "성장·도전·새로운 시작의 에너지",
        "작용": (
            "목 기운이 들어오는 시기에 "
            "당신의 운이 살아납니다. "
            "봄철(3~5월)과 甲乙년에 "
            "활력이 올라가고 기회가 찾아옵니다"
        ),
        "생활": (
            "초록색·파란색 계열을 가까이 하고 "
            "동쪽 방향 활동을 늘리면 에너지가 보충됩니다. "
            "나무·식물을 가까이 두는 것도 도움이 됩니다"
        ),
        "피할것": "기신 기운이 강한 시기에는 새로운 시작보다 현재 자리를 지키는 것이 현명합니다",
    },
    "화": {
        "의미": "열정·표현·인연·활동의 에너지",
        "작용": (
            "화 기운이 들어오는 시기에 "
            "당신의 운이 살아납니다. "
            "여름철(6~8월)과 丙丁년에 "
            "에너지가 최고조에 달합니다"
        ),
        "생활": (
            "빨간색·주황색·핑크 계열을 가까이 하고 "
            "남쪽 방향 활동을 늘리세요. "
            "따뜻한 환경과 햇빛이 당신에게 활력을 줍니다"
        ),
        "피할것": "기신 기운이 강한 시기에는 감정적 결정과 충동적 지출을 주의하세요",
    },
    "토": {
        "의미": "안정·신뢰·중심을 잡는 에너지",
        "작용": (
            "토 기운이 들어오는 시기에 "
            "당신의 운이 살아납니다. "
            "환절기(3·6·9·12월)와 戊己년에 "
            "안정감이 올라가고 재물이 쌓입니다"
        ),
        "생활": (
            "노란색·갈색·황토색 계열을 가까이 하고 "
            "중앙·안정된 환경에서 활동하세요. "
            "흙·자연과 가까운 활동이 에너지를 보충합니다"
        ),
        "피할것": "기신 기운이 강한 시기에는 변화보다 현상 유지를 선택하세요",
    },
    "금": {
        "의미": "결단·추진·원칙·실행의 에너지",
        "작용": (
            "금 기운이 들어오는 시기에 "
            "당신의 운이 살아납니다. "
            "가을철(9~11월)과 庚辛년에 "
            "실행력이 최고조에 달합니다"
        ),
        "생활": (
            "흰색·은색·금색 계열을 가까이 하고 "
            "서쪽 방향 활동을 늘리세요. "
            "금속 소품을 활용하는 것도 도움이 됩니다"
        ),
        "피할것": "기신 기운이 강한 시기에는 강경한 태도보다 유연한 접근이 유리합니다",
    },
    "수": {
        "의미": "지혜·유연·감성·직관의 에너지",
        "작용": (
            "수 기운이 들어오는 시기에 "
            "당신의 운이 살아납니다. "
            "겨울철(12~2월)과 壬癸년에 "
            "직관과 지혜가 최고조에 달합니다"
        ),
        "생활": (
            "검은색·파란색·남색 계열을 가까이 하고 "
            "북쪽 방향 활동을 늘리세요. "
            "물·수영·목욕이 에너지를 순환시킵니다"
        ),
        "피할것": "기신 기운이 강한 시기에는 우유부단함을 주의하고 핵심 하나에 집중하세요",
    },
}

HEE_STORY: Dict[str, str] = {
    "목": "목 기운도 당신에게 도움이 됩니다. 성장·학습 활동에서 시너지가 납니다",
    "화": "화 기운도 당신에게 도움이 됩니다. 표현·인연 활동에서 시너지가 납니다",
    "토": "토 기운도 당신에게 안정을 줍니다. 현실적 활동에서 시너지가 납니다",
    "금": "금 기운도 당신에게 도움이 됩니다. 실행·결단 활동에서 시너지가 납니다",
    "수": "수 기운도 당신에게 도움이 됩니다. 지혜·감성 활동에서 시너지가 납니다",
}

GI_STORY: Dict[str, str] = {
    "목": (
        "목 기운이 강해지는 봄철·甲乙년에는 "
        "새로운 시작보다 현재를 지키는 전략이 유리합니다. "
        "간·담·눈·근육 건강을 챙기세요"
    ),
    "화": (
        "화 기운이 강해지는 여름철·丙丁년에는 "
        "과열·충동을 주의하세요. "
        "심장·혈압·혈관 건강을 챙기세요"
    ),
    "토": (
        "토 기운이 강해지는 환절기·戊己년에는 "
        "고집보다 유연성을 의식적으로 발휘하세요. "
        "위장·비장·피부 건강을 챙기세요"
    ),
    "금": (
        "금 기운이 강해지는 가을철·庚辛년에는 "
        "강경한 태도가 오히려 손해를 부를 수 있습니다. "
        "폐·대장·피부 건강을 챙기세요"
    ),
    "수": (
        "수 기운이 강해지는 겨울철·壬癸년에는 "
        "방향 설정에 집중하고 흐릿한 목표를 정리하세요. "
        "신장·방광·부인과 건강을 챙기세요"
    ),
}

LIFESTYLE: Dict[str, Dict[str, Any]] = {
    "화": {
        "색상": {
            "좋은색": "빨강·주황·핑크·산호색",
            "이유": "화 기운을 보충해 활력과 열정을 높입니다",
            "피할색": "검정·진한 파랑",
            "피할이유": "기신 수 기운을 강화해 에너지를 낮출 수 있습니다",
        },
        "방위": {
            "좋은방향": "남쪽",
            "이유": "화 기운이 강한 남쪽에서 에너지를 충전하세요",
            "생활팁": "책상을 남향으로 배치하거나 남쪽 창가에서 일하면 도움됩니다",
        },
        "음식": "따뜻하고 매운 음식, 빨간 음식(토마토·딸기·고추)",
        "운동": "달리기·춤·격렬한 유산소 운동으로 화 에너지를 발산하세요",
        "힐링": "햇볕 쬐기, 불 캠핑, 따뜻한 목욕",
    },
    "목": {
        "색상": {
            "좋은색": "초록·연두·청록색",
            "이유": "목 기운을 보충해 성장과 도전 에너지를 높입니다",
            "피할색": "흰색·은색",
            "피할이유": "기신 금 기운을 강화할 수 있습니다",
        },
        "방위": {
            "좋은방향": "동쪽",
            "이유": "목 기운이 강한 동쪽에서 새로운 아이디어가 옵니다",
            "생활팁": "동쪽 창가에 식물을 두거나 아침 햇살을 맞으세요",
        },
        "음식": "신맛 음식, 녹색 채소(시금치·브로콜리·케일)",
        "운동": "요가·스트레칭·하이킹으로 목 에너지를 순환하세요",
        "힐링": "숲 산책, 정원 가꾸기, 식물 키우기",
    },
    "토": {
        "색상": {
            "좋은색": "노랑·황토·베이지·카멜색",
            "이유": "토 기운을 보충해 안정과 신뢰 에너지를 높입니다",
            "피할색": "파랑·초록",
            "피할이유": "기신 목·수 기운을 강화할 수 있습니다",
        },
        "방위": {
            "좋은방향": "중앙·대각선",
            "이유": "토는 중앙의 기운으로 안정된 공간에서 힘을 발휘합니다",
            "생활팁": "집 중앙을 정리정돈하고 황토색 소품을 활용하세요",
        },
        "음식": "단맛 음식, 뿌리채소(고구마·감자·당근)",
        "운동": "걷기·가벼운 조깅·태극권으로 토 에너지를 쌓으세요",
        "힐링": "흙 만지기, 도자기, 텃밭 가꾸기",
    },
    "금": {
        "색상": {
            "좋은색": "흰색·은색·금색·회색",
            "이유": "금 기운을 보충해 결단력과 추진력을 높입니다",
            "피할색": "빨강·주황",
            "피할이유": "기신 화 기운을 강화할 수 있습니다",
        },
        "방위": {
            "좋은방향": "서쪽",
            "이유": "금 기운이 강한 서쪽에서 결단과 실행력이 올라갑니다",
            "생활팁": "서쪽 방향 활동을 늘리고 금속 소품을 활용하세요",
        },
        "음식": "매운맛·고소한 음식, 흰 음식(두부·마늘·생강)",
        "운동": "웨이트·격투기·수영으로 금 에너지를 단련하세요",
        "힐링": "금속 공예, 악기 연주, 정리정돈",
    },
    "수": {
        "색상": {
            "좋은색": "검정·진한파랑·남색",
            "이유": "수 기운을 보충해 지혜와 유연성을 높입니다",
            "피할색": "노랑·황토",
            "피할이유": "기신 토 기운을 강화할 수 있습니다",
        },
        "방위": {
            "좋은방향": "북쪽",
            "이유": "수 기운이 강한 북쪽에서 직관과 지혜가 올라갑니다",
            "생활팁": "북쪽에 책상이나 명상 공간을 두면 도움됩니다",
        },
        "음식": "짠맛·해산물, 검은 음식(검은콩·흑미·블루베리)",
        "운동": "수영·요가·명상으로 수 에너지를 순환하세요",
        "힐링": "목욕·족욕·바다·강변 산책",
    },
}

YONG_CAREER: Dict[str, Dict[str, Any]] = {
    "화": {
        "top3": [
            {
                "직군": "방송·미디어·콘텐츠",
                "이유": (
                    "화 기운의 빛과 열정이 "
                    "표현·전달하는 일에서 자연스럽게 발휘됩니다. "
                    "카메라 앞이든 뒤든 "
                    "에너지가 살아나는 분야입니다"
                ),
            },
            {
                "직군": "요식업·서비스·호스피탈리티",
                "이유": (
                    "사람을 따뜻하게 맞이하고 "
                    "기운을 불어넣는 화 에너지가 "
                    "서비스업에서 강점이 됩니다"
                ),
            },
            {
                "직군": "교육·강의·코칭",
                "이유": (
                    "열정과 표현력으로 "
                    "사람의 마음에 불을 지피는 일이 "
                    "천직에 가깝습니다"
                ),
            },
        ],
        "avoid": (
            "기신 계열 업종은 에너지 소진이 크고 "
            "성과 대비 보람이 적을 수 있습니다. "
            "특히 차갑고 경직된 환경은 "
            "당신의 열정을 꺼뜨릴 수 있습니다"
        ),
    },
    "목": {
        "top3": [
            {
                "직군": "교육·출판·컨텐츠 기획",
                "이유": "목 기운의 성장·개척 에너지가 새로운 것을 만들고 가르치는 일에서 빛납니다",
            },
            {
                "직군": "의료·헬스케어·웰니스",
                "이유": "생명력과 회복의 기운이 건강·치유 분야에서 강점이 됩니다",
            },
            {
                "직군": "환경·농업·원예",
                "이유": "자연과 성장을 다루는 분야에서 목 에너지가 자연스럽게 발휘됩니다",
            },
        ],
        "avoid": (
            "기신 계열은 성장 에너지가 막히는 환경입니다. "
            "딱딱하고 변화 없는 조직은 "
            "당신의 도전 욕구를 꺾을 수 있습니다"
        ),
    },
    "토": {
        "top3": [
            {
                "직군": "부동산·건설·인프라",
                "이유": "토 기운의 안정·실질 에너지가 실물 자산을 다루는 분야에서 강점이 됩니다",
            },
            {
                "직군": "금융·보험·자산관리",
                "이유": "신뢰와 안정이 기반인 금융 분야에서 토 기운의 묵직함이 신뢰를 만듭니다",
            },
            {
                "직군": "의료·복지·사회서비스",
                "이유": "포용과 보살핌의 토 에너지가 사람을 돕는 분야에서 빛납니다",
            },
        ],
        "avoid": (
            "기신 계열은 안정 에너지가 흔들리는 환경입니다. "
            "변동이 심한 투기·단기 거래는 "
            "당신의 스트레스를 키웁니다"
        ),
    },
    "금": {
        "top3": [
            {
                "직군": "법률·군경·행정",
                "이유": "원칙과 결단의 금 에너지가 규범을 다루는 분야에서 강점이 됩니다",
            },
            {
                "직군": "기술·제조·엔지니어링",
                "이유": "정밀함과 추진력의 금 에너지가 기술 분야에서 탁월한 실력을 만듭니다",
            },
            {
                "직군": "금융·투자·트레이딩",
                "이유": "결단력과 실행력의 금 에너지가 빠른 판단이 필요한 금융 분야에 맞습니다",
            },
        ],
        "avoid": (
            "기신 계열은 결단 에너지가 막히는 환경입니다. "
            "우유부단함이 요구되는 환경은 "
            "당신을 소진시킵니다"
        ),
    },
    "수": {
        "top3": [
            {
                "직군": "무역·유통·물류",
                "이유": "유연하게 흐르는 수 에너지가 경계를 넘나드는 무역·유통에 맞습니다",
            },
            {
                "직군": "철학·상담·심리",
                "이유": "깊은 통찰과 공감의 수 에너지가 마음을 다루는 분야에서 빛납니다",
            },
            {
                "직군": "IT·데이터·연구",
                "이유": "지혜와 분석력의 수 에너지가 데이터·연구 분야에서 강점이 됩니다",
            },
        ],
        "avoid": (
            "기신 계열은 수 에너지가 막히는 환경입니다. "
            "경직된 규정 중심 환경은 "
            "당신의 유연성을 꺾을 수 있습니다"
        ),
    },
}


def count_sipsin_categories(day_master: str, pillars: dict) -> Tuple[int, int, int]:
    ss = rex = guan = 0
    for gan in _all_target_gans(pillars):
        if gan == day_master:
            continue
        name = sp.classify_sipsin(day_master, gan)
        if name in ("식신", "상관"):
            ss += 1
        elif name in ("편재", "정재"):
            rex += 1
        elif name in ("편관", "정관"):
            guan += 1
    return ss, rex, guan


def _primary_gi(gi_el: str, gisin: List[str]) -> str:
    if gi_el:
        return gi_el
    return gisin[0] if gisin else ""


def build_yongsin_story(
    day_master: str,
    yong_el: str,
    hee_el: List[str],
    gi_el: str,
    verdict: str,
    female: bool,
    counts: dict,
) -> Dict[str, Any]:
    _ = day_master, female, counts
    yong_data = dict(YONG_STORY.get(yong_el, {}))
    gi_primary = gi_el
    if yong_data.get("피할것"):
        yong_data["피할것"] = yong_data["피할것"].replace("기신", f"기신 {gi_primary}" if gi_primary else "기신")

    hee_stories = [HEE_STORY[h] for h in hee_el if HEE_STORY.get(h)]
    gi_story = GI_STORY.get(gi_primary, "")

    return {
        "신강약_스토리": VERDICT_STORY.get(verdict, VERDICT_STORY["중화"]),
        "용신_의미": yong_data.get("의미", ""),
        "용신_작용": yong_data.get("작용", ""),
        "용신_생활": yong_data.get("생활", ""),
        "희신_스토리": hee_stories,
        "기신_스토리": gi_story,
        "피할것": yong_data.get("피할것", ""),
    }


def build_yongsin_career(
    yong_el: str,
    gi_el: str,
    day_master: str,
    female: bool,
    ss_n: int,
    rex_n: int,
    guan_n: int,
) -> Dict[str, Any]:
    _ = day_master, female, guan_n
    career_data = dict(YONG_CAREER.get(yong_el, {}))
    top3 = [dict(x) for x in career_data.get("top3", [])]
    avoid = str(career_data.get("avoid", ""))
    if gi_el and "기신" in avoid:
        avoid = avoid.replace("기신 계열", f"기신 {gi_el} 계열", 1)

    if ss_n >= 4:
        top3.append(
            {
                "직군": "크리에이터·1인기업·강사",
                "이유": (
                    f"식상이 {ss_n}개로 강해 "
                    "표현·창작·가르치는 일에서 "
                    "타고난 능력이 발휘됩니다"
                ),
            }
        )
    if rex_n >= 4:
        top3.append(
            {
                "직군": "영업·사업·투자",
                "이유": (
                    f"재성이 {rex_n}개로 강해 "
                    "거래와 협상에서 "
                    "타고난 감각이 있습니다"
                ),
            }
        )

    work_style = (
        "독립·창업이 잘 맞는 구조입니다"
        if yong_el in ("화", "목") and ss_n >= 3
        else "조직 내 전문가로 커리어를 쌓는 것이 안정적입니다"
    )

    return {
        "추천_직군": top3[:5],
        "피할_직군": avoid,
        "근무형태": work_style,
    }


def build_yongsin_lifestyle(
    yong_el: str,
    gi_el: str,
    day_master: str,
) -> Dict[str, str]:
    _ = day_master, gi_el
    ls = LIFESTYLE.get(yong_el, {})
    color = ls.get("색상") or {}
    direction = ls.get("방위") or {}
    return {
        "색상_좋음": color.get("좋은색", ""),
        "색상_이유": color.get("이유", ""),
        "색상_피함": color.get("피할색", ""),
        "색상_피함_이유": color.get("피할이유", ""),
        "방위": direction.get("좋은방향", ""),
        "방위_이유": direction.get("이유", ""),
        "방위_팁": direction.get("생활팁", ""),
        "음식": ls.get("음식", ""),
        "운동": ls.get("운동", ""),
        "힐링": ls.get("힐링", ""),
    }


def build_yongsin_summary(
    verdict: str,
    yong_el: str,
    day_master: str,
    female: bool,
) -> str:
    _ = female
    kr = gj.STEM_KR[gj.stem_index(day_master)] if day_master else ""
    label = f"{day_master}({kr})" if kr else day_master
    return (
        f"{label}일간 {verdict} 사주로 "
        f"용신은 {yong_el}입니다. "
        f"{yong_el} 기운이 강해지는 시기와 환경에서 "
        f"당신의 능력이 가장 잘 발휘됩니다. "
        f"일상에서 용신 방향을 의식적으로 가까이 하면 "
        f"운의 흐름이 자연스럽게 개선됩니다"
    )


def build_yongsin_year_hints(
    yong_el: str,
    hee_el: List[str],
    gi_el: str,
    sewoon_rows: Sequence[Dict[str, Any]],
    *,
    good_limit: int = 3,
    caution_limit: int = 2,
) -> Dict[str, List[Dict[str, str]]]:
    hee_set = set(hee_el or [])
    gi_set = {gi_el} if gi_el else set()
    good: List[Tuple[int, int, str, str]] = []
    caution: List[Tuple[int, int, str, str]] = []

    for row in sewoon_rows or ():
        try:
            year = int(row.get("연도"))
        except (TypeError, ValueError):
            continue
        gz = str(row.get("간지") or row.get("pillar") or "")
        if len(gz) < 2:
            continue
        stem_el = gj.element_of_stem(gz[0])
        branch_el = gj.element_of_branch(gz[1])
        elems = {stem_el, branch_el}

        score = 0
        if yong_el in elems:
            score += 3
        if elems & hee_set:
            score += 2
        if elems & gi_set:
            score -= 3

        tag_parts = []
        if yong_el in elems:
            tag_parts.append(f"용신 {yong_el}")
        if elems & hee_set:
            tag_parts.append(f"희신 {'·'.join(sorted(elems & hee_set))}")
        if elems & gi_set:
            tag_parts.append(f"기신 {'·'.join(sorted(elems & gi_set))}")
        tag = " · ".join(tag_parts) if tag_parts else f"{stem_el}·{branch_el} 기운"

        entry = (score, year, gz, tag)
        if score >= 3:
            good.append(entry)
        elif score <= -2:
            caution.append(entry)

    good.sort(key=lambda x: (-x[0], x[1]))
    caution.sort(key=lambda x: (x[0], x[1]))

    def pack(rows: List[Tuple[int, int, str, str]]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for _, y, gz, tag in rows:
            out.append(
                {
                    "연도": str(y),
                    "간지": gz,
                    "설명": f"{y}년 {gz} — {tag}",
                }
            )
        return out

    return {
        "좋은_해": pack(good[:good_limit]),
        "주의_해": pack(caution[:caution_limit]),
    }


def enrich_yongsin_report(
    rep: Dict[str, Any],
    *,
    day_master: str,
    pillars: Optional[dict],
    counts: Dict[str, int],
    female: bool,
    sewoon_nearby: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    yong_el = str(rep.get("용신_오행") or "")
    hee_el = list(rep.get("희신") or [])
    gisin = list(rep.get("기신") or [])
    gi_el = gisin[0] if gisin else ""
    verdict = str(rep.get("일간_강약") or "중화")

    ss_n = rex_n = guan_n = 0
    if pillars:
        ss_n, rex_n, guan_n = count_sipsin_categories(day_master, pillars)

    story = build_yongsin_story(
        day_master, yong_el, hee_el, gi_el, verdict, female, counts
    )
    rep.update(story)
    rep["lifestyle"] = build_yongsin_lifestyle(yong_el, gi_el, day_master)
    rep["직업추천"] = build_yongsin_career(
        yong_el, gi_el, day_master, female, ss_n, rex_n, guan_n
    )
    rep["요약_한줄"] = build_yongsin_summary(verdict, yong_el, day_master, female)
    rep["근거_스토리"] = rep["요약_한줄"]
    rep["용신_한자"] = EL_HANJA.get(yong_el, yong_el)

    if sewoon_nearby:
        rep["세운_힌트"] = build_yongsin_year_hints(
            yong_el, hee_el, gi_el, sewoon_nearby
        )

    clean_notes: List[str] = []
    for note in rep.get("notes") or []:
        if not isinstance(note, str):
            continue
        if " vs " in note and "계열" in note:
            continue
        if "%" in note or "비중 약" in note:
            continue
        clean_notes.append(note)
    rep["notes"] = clean_notes[:4]

    for drop_key in (
        "비겁인성_비율",
        "식재관_비율",
        "십신_비교_설명",
        "강약_점수",
        "한신",
        "구신",
    ):
        rep.pop(drop_key, None)

    detail = dict(rep.get("강약_상세") or {})
    for drop_detail in ("점수_해설", "점수_구간"):
        detail.pop(drop_detail, None)
    if isinstance(detail.get("산출_근거"), dict):
        internal = dict(detail["산출_근거"])
        detail["산출_근거"] = {
            k: v
            for k, v in internal.items()
            if k not in ("비겁인성_퍼센트", "식재관_퍼센트", "십신")
        }
    rep["강약_상세"] = detail

    return rep
