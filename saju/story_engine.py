# -*- coding: utf-8 -*-
"""원국 스토리 — 성별(여명·남명)에 따라 문장 체계를 완전히 분리해 생성한다."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import ohaeng as oh
from . import sipsin as sp


_PAD_STRENGTH_POOL = (
    "생활 습관과 마음가짐을 함께 다듬으면 강점이 더 분명해지고, 무리한 비교보다 자신의 페이스를 지키는 것이 도움이 됩니다.",
    "작은 실천이 쌓이면 성과로 이어지는 타입이므로, 급하게 결론 내리기보다 꾸준함을 우선하세요.",
    "강점은 한 번에 드러나기보다 시간이 지나며 분명해지는 경우가 많습니다.",
)

_PAD_WEAKNESS_POOL = (
    "주변과의 호흡을 맞추면 부담이 줄고, 본인 페이스가 더 잘 살아납니다.",
    "무리한 확장보다 회복·정리 시간을 확보하면 단점이 덜 드러납니다.",
    "한 가지에 집중할 때 실수가 줄고, 에너지 소모도 완만해집니다.",
)

_PAD_NEUTRAL_POOL = _PAD_STRENGTH_POOL + _PAD_WEAKNESS_POOL


def _min_chars(
    text: str,
    min_len: int,
    tail: str = "",
    *,
    pool: tuple[str, ...] = _PAD_NEUTRAL_POOL,
    used_fillers: Optional[set[str]] = None,
) -> str:
    """짧은 문장은 성별·슬롯 태그 없이 중립 문장으로만 보강한다."""
    s = text.strip()
    if len(s) >= min_len:
        return s
    out = s
    seed = sum(ord(c) for c in s) % len(pool)
    fillers: List[str] = []
    for i in range(len(pool)):
        cand = pool[(seed + i) % len(pool)]
        if used_fillers is not None and cand in used_fillers:
            continue
        fillers.append(cand)
    if not fillers:
        fillers = list(pool)
    if tail.strip():
        fillers.insert(0, tail.strip())
    idx = 0
    while len(out) < min_len:
        filler = fillers[idx % len(fillers)]
        if used_fillers is not None:
            used_fillers.add(filler)
        out = f"{out} {filler}".strip()
        idx += 1
    return out


def _gi_el_str(yong: Dict[str, Any]) -> str:
    raw = yong.get("기신_오행")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    gl = yong.get("기신") or []
    return "·".join(str(x) for x in gl if x) or ""


_DM_NATURE: Dict[str, Dict[str, str]] = {
    "甲": {"상징": "곧게 뻗은 나무", "강점": "리더십과 개척정신", "약점": "고집과 융통성 부족"},
    "乙": {"상징": "부드러운 넝쿨", "강점": "뛰어난 적응력과 친화력", "약점": "우유부단과 의존성"},
    "丙": {"상징": "밝은 태양", "강점": "넘치는 긍정 에너지와 카리스마", "약점": "경솔함과 지속력 부족"},
    "丁": {"상징": "섬세한 촛불", "강점": "깊은 감수성과 직관력", "약점": "예민함과 감정 기복"},
    "戊": {"상징": "넓은 대지", "강점": "묵직한 신뢰감과 포용력", "약점": "변화 거부와 둔감함"},
    "己": {"상징": "기름진 논밭", "강점": "현실적 판단력과 실용성", "약점": "소심함과 소극적 태도"},
    "庚": {"상징": "단단한 바위", "강점": "강한 결단력과 의리", "약점": "냉정함과 타협 어려움"},
    "辛": {"상징": "빛나는 보석", "강점": "완벽한 마무리와 미적 감각", "약점": "예민함과 자존심"},
    "壬": {"상징": "큰 강물", "강점": "넓은 포용력과 지혜", "약점": "집중력 부족과 방랑기"},
    "癸": {"상징": "고요한 빗물", "강점": "예리한 직관과 감수성", "약점": "불안감과 의존성"},
}

# ── 직업 도출: 용신(환경) + 일간(방식) + 십신(역할) + 오행(특화) + 신살(재능) ──

YONG_DOMAIN: Dict[str, Dict[str, Any]] = {
    "목": {
        "환경": "성장·생명·교육·시작",
        "재료": "나무·종이·섬유·식물",
        "행위": "가르치고 키우고 시작하는 일",
        "구체": [
            "교육·보육·학원",
            "출판·인쇄",
            "목재·가구·인테리어",
            "농업·원예·조경",
            "의류·패션(섬유)",
            "환경·산림",
            "스타트업·신사업 개척",
        ],
    },
    "화": {
        "환경": "열·빛·에너지·표현",
        "재료": "불·전기·빛·열",
        "행위": "태우고 밝히고 드러내는 일",
        "구체": [
            "용접·금속가공·주조",
            "요리·제과·제빵",
            "전기·전자·에너지",
            "조명·반도체",
            "방송·연예·공연",
            "미용·헤어",
            "화학·석유·플라스틱",
        ],
    },
    "토": {
        "환경": "안정·신뢰·중개·보관",
        "재료": "흙·시멘트·부동산",
        "행위": "쌓고 중개하고 보호하는 일",
        "구체": [
            "건설·시공·토목",
            "부동산·공인중개",
            "의료·간호·복지",
            "금융·보험·저축은행",
            "창고·물류·유통",
            "농산물·식품유통",
            "행정·공무·사회서비스",
        ],
    },
    "금": {
        "환경": "원칙·정밀·결단·제련",
        "재료": "금속·기계·도구",
        "행위": "깎고 다듬고 판단하는 일",
        "구체": [
            "철강·제철·용광로",
            "기계·부품·제조",
            "법률·검찰·군경",
            "외과·치과·수술",
            "회계·감사·세무",
            "금융투자·트레이딩",
            "자동차·항공·방산",
        ],
    },
    "수": {
        "환경": "지식·유통·순환·감성",
        "재료": "물·정보·아이디어",
        "행위": "흘러가고 연결하고 분석하는 일",
        "구체": [
            "IT·소프트웨어·데이터",
            "무역·수출입",
            "철학·상담·심리치료",
            "예술·음악·문학",
            "수산·양식·수처리",
            "관광·여행·숙박",
            "연구·학문·분석",
        ],
    },
}

DM_WORK_STYLE: Dict[str, Dict[str, str]] = {
    "甲": {"스타일": "개척형·리더형", "강점": "새로운 것을 시작하고 이끄는 일", "직무": "창업가·사업기획·개발팀장·교장", "주의": "혼자 판단하고 밀어붙이는 독단 주의"},
    "乙": {"스타일": "보조형·협력형·적응형", "강점": "유연하게 맞추고 조율하는 일", "직무": "코디네이터·조율자·비서·상담사", "주의": "주도권 없이 끌려다니는 것 주의"},
    "丙": {"스타일": "표현형·리더형·발산형", "강점": "사람 앞에 서서 에너지를 전달하는 일", "직무": "강사·MC·세일즈·이벤트기획", "주의": "지속성 없이 화려함만 추구 주의"},
    "丁": {"스타일": "섬세형·전문형·집중형", "강점": "깊이 파고드는 전문 기술 일", "직무": "전문연구원·작가·아티스트·상담사", "주의": "예민함으로 인한 감정 소진 주의"},
    "戊": {"스타일": "안정형·관리형·포용형", "강점": "믿고 맡길 수 있는 중심 역할", "직무": "관리자·총무·운영팀장·부동산", "주의": "변화 거부로 인한 도태 주의"},
    "己": {"스타일": "실무형·섬세형·현실형", "강점": "꼼꼼하게 실무를 처리하는 일", "직무": "회계·행정·품질관리·영양사", "주의": "소극적 태도로 기회 놓치는 것 주의"},
    "庚": {"스타일": "결단형·원칙형·추진형", "강점": "명확한 기준으로 밀어붙이는 일", "직무": "법조인·군인·외과의·제조업 관리", "주의": "냉정함으로 인한 인간관계 마찰 주의"},
    "辛": {"스타일": "완성형·심미형·전문형", "강점": "높은 기준으로 완성도를 만드는 일", "직무": "디자이너·보석상·작가·성형외과", "주의": "완벽주의로 인한 시간 초과 주의"},
    "壬": {"스타일": "전략형·포용형·유연형", "강점": "큰 그림을 그리고 흐름을 읽는 일", "직무": "전략기획·무역·외교관·컨설턴트", "주의": "방향 없이 흘러다니는 것 주의"},
    "癸": {"스타일": "감성형·직관형·분석형", "강점": "보이지 않는 것을 감지하고 분석하는 일", "직무": "심리상담·예술가·연구원·정보분석", "주의": "불안감으로 인한 결정 회피 주의"},
}

OVER_SPEC: Dict[str, Dict[str, str]] = {
    "목": {"과다": "교육·환경·의료 분야에서 성장과 치유 에너지로 일할 때 최강", "결핍": "성장·도전 직무보다 안정 직무가 맞음"},
    "화": {"과다": "빛·열·에너지를 다루는 분야 특화. 용접·요리·방송·전기 등 화기(火氣) 직군", "결핍": "표현·홍보직보다 분석·연구직이 맞음"},
    "토": {"과다": "부동산·건설·중개·행정 등 실물·안정 분야에서 탁월", "결핍": "변화 빠른 직무보다 안정적 직무 선호"},
    "금": {"과다": "금속·기계·법률·수술 등 정밀·결단 직군 특화", "결핍": "결단 직무보다 감성·협력 직무가 맞음"},
    "수": {"과다": "IT·데이터·무역·예술 등 정보·감성 분야 특화", "결핍": "분석직보다 실행·현장직이 맞음"},
}

SINSAL_JOB: Dict[str, Dict[str, str]] = {
    "역마살": {"재능": "이동·해외·변화 직군", "직업": "무역사·외교관·여행업·드라이버·배달", "이유": "한곳에 있지 않고 움직일 때 에너지가 살아납니다"},
    "도화살": {"재능": "대인·예술·서비스 직군", "직업": "연예인·서비스업·미용·상담·영업", "이유": "사람을 끌어당기는 매력 에너지가 있습니다"},
    "천을귀인": {"재능": "귀인 연결·인맥 직군", "직업": "컨설턴트·중개인·외교·로비", "이유": "귀인을 만나고 연결하는 복이 있습니다"},
    "문창귀인": {"재능": "학문·글·시험 직군", "직업": "작가·교수·언론인·번역가·출판", "이유": "글과 학문에서 빛나는 재능입니다"},
    "학당귀인": {"재능": "교육·자격·전문직", "직업": "교사·강사·전문자격사·컨설턴트", "이유": "배움과 가르침에서 두각을 나타냅니다"},
    "복성귀인": {"재능": "복록·인연 직군", "직업": "복지·상담·인사·고객관리", "이유": "인연과 복이 실무로 이어지기 쉽습니다"},
    "백호살": {"재능": "칼·피·결단 직군", "직업": "외과의·군인·경찰·소방관·정육", "이유": "피·금속·결단적 상황 처리 능력이 있습니다"},
    "양인살": {"재능": "강력·결단·체력 직군", "직업": "운동선수·군인·외과·요리사(칼)", "이유": "강한 결단력과 체력적 에너지가 있습니다"},
    "괴강살": {"재능": "권위·지배·전문 직군", "직업": "CEO·법조인·군 지휘관·전문경영인", "이유": "강한 카리스마와 지배력이 있습니다"},
}

YONG_DM_COMBO: Dict[Tuple[str, str], List[Dict[str, str]]] = {
    ("화", "甲"): [
        {"직군": "방송·콘텐츠 기획자", "이유": "화 에너지로 표현하고 甲의 리더십으로 이끄는 콘텐츠 기획·PD 역할"},
        {"직군": "교육사업가", "이유": "화의 열정으로 가르치고 甲의 개척 정신으로 교육 사업을 만드는 일"},
    ],
    ("화", "乙"): [
        {"직군": "요리사·제과제빵", "이유": "화의 열(火氣)을 직접 다루는 요리 분야에서 乙의 섬세함이 빛남"},
        {"직군": "미용·헤어·뷰티", "이유": "화의 빛·열로 아름다움을 만드는 乙의 유연한 손길이 강점"},
    ],
    ("화", "丙"): [
        {"직군": "연예인·MC·강연가", "이유": "화×화의 이중 에너지로 무대 위에서 최고의 존재감을 발휘"},
        {"직군": "전기·에너지 관련 사업", "이유": "화 에너지를 실질적으로 다루는 丙의 추진력으로 에너지 분야 주도"},
    ],
    ("화", "丁"): [
        {"직군": "용접·금속가공", "이유": "정화(丁火)는 금속을 녹이고 가공하는 불로 용접·금형 분야 특화"},
        {"직군": "주얼리·귀금속 가공", "이유": "섬세한 丁火로 보석과 금속을 다루는 정밀 가공 직군에 강점"},
    ],
    ("화", "戊"): [
        {"직군": "요식업·식품제조", "이유": "화(火)로 요리하고 토(戊土)로 안정적 운영하는 식품업 최적"},
        {"직군": "에너지·화학 플랜트 관리", "이유": "火 에너지를 安定(戊)적으로 관리하는 설비·플랜트 운영 역할"},
    ],
    ("화", "己"): [
        {"직군": "영양사·푸드스타일리스트", "이유": "화(음식)를 己의 섬세함으로 다루는 영양·식품 전문직"},
        {"직군": "조명·인테리어 디자이너", "이유": "화(빛)를 己의 꼼꼼함으로 공간에 구현하는 인테리어 조명 분야"},
    ],
    ("화", "庚"): [
        {"직군": "제철·용광로·철강 산업", "이유": "화(火)로 금(庚金)을 제련하는 가장 직접적인 조합. 철강·금속 정련 특화"},
        {"직군": "열처리·소방·용접 기술자", "이유": "庚의 결단력으로 火를 제어하는 기술직. 열처리·소방시설 분야 강점"},
    ],
    ("화", "辛"): [
        {"직군": "보석·귀금속 세공", "이유": "화로 금속을 다루고 辛의 완벽함으로 보석을 완성하는 정밀 세공"},
        {"직군": "반도체·전자부품 정밀 제조", "이유": "辛金을 火로 정밀 가공하는 반도체·전자 제조 분야 특화"},
    ],
    ("화", "壬"): [
        {"직군": "발전소·에너지 기술 기획", "이유": "壬의 전략적 사고로 화(에너지)를 관리·기획하는 에너지 분야"},
        {"직군": "방송국 기술 감독·PD", "이유": "화(방송)를 壬의 넓은 시각으로 총괄하는 방송 기술 총감독"},
    ],
    ("화", "癸"): [
        {"직군": "심리상담·힐링 치료사", "이유": "癸水의 감성으로 화(열정·감정)를 치유하는 상담 분야 특화"},
        {"직군": "예술가·사진작가", "이유": "화(빛)를 癸의 감성으로 포착하는 사진·빛 예술 분야 강점"},
    ],
    ("금", "甲"): [
        {"직군": "법조인·검사·변호사", "이유": "금(원칙)을 甲의 추진력으로 실현하는 법률 분야 리더"},
        {"직군": "건설·토목 시공 CEO", "이유": "금(기계·도구)으로 甲의 개척 본능을 발휘하는 건설 사업"},
    ],
    ("금", "丁"): [
        {"직군": "외과의·치과의", "이유": "금(칼·메스)을 丁의 섬세함으로 다루는 수술 분야 최적"},
        {"직군": "침술사·한의사", "이유": "금(침)을 丁火의 섬세한 기운으로 치유하는 한의학 분야"},
    ],
    ("금", "庚"): [
        {"직군": "군인·무술인·경호원", "이유": "경금(庚金)이 용신인 庚 일간 — 금×금의 강력한 결단·무력 에너지"},
        {"직군": "기계·자동차 엔지니어", "이유": "금속을 금속으로 다루는 庚의 타고난 기계 감각"},
    ],
    ("목", "丙"): [
        {"직군": "교육사업·학원 운영", "이유": "목(교육·성장)을 丙의 카리스마로 이끄는 교육 사업 리더"},
        {"직군": "의료·재활 전문가", "이유": "목(생명·치유)을 丙의 열정으로 다루는 의료·재활 분야"},
    ],
    ("목", "壬"): [
        {"직군": "무역·수출입 전문가", "이유": "수생목(水生木)의 흐름으로 壬의 유통 감각이 목(상품) 분야에서 빛남"},
        {"직군": "IT 서비스 기획자", "이유": "목(성장·시작)을 壬의 전략으로 설계하는 IT 서비스 기획 특화"},
    ],
    ("수", "庚"): [
        {"직군": "데이터 분석·AI 개발자", "이유": "수(데이터·정보)를 庚의 정밀함으로 분석하는 IT 기술 특화"},
        {"직군": "금융·투자 분석가", "이유": "金生水(金生水)로 庚의 결단력이 수(금융·유통) 분야에서 발휘"},
    ],
    ("수", "癸"): [
        {"직군": "연구원·학자", "이유": "수×수의 깊은 탐구 에너지로 학문·연구 분야 최강"},
        {"직군": "심리·철학·상담 전문가", "이유": "癸의 직관이 수(지혜·심층)와 결합해 내면 탐구 직군 특화"},
    ],
    ("토", "戊"): [
        {"직군": "부동산 개발·시행사", "이유": "토×토의 이중 안정 에너지로 부동산 개발·토지 분야 특화"},
        {"직군": "건설·시공·토목 관리", "이유": "戊의 묵직함으로 토(건설) 분야를 안정적으로 운영"},
    ],
    ("토", "己"): [
        {"직군": "농업·식품·유통", "이유": "토(흙·땅)를 己의 섬세함으로 다루는 농업·식품 가공 특화"},
        {"직군": "의료·간호·복지", "이유": "己의 꼼꼼한 보살핌이 토(안정·치유) 에너지와 결합한 복지 분야"},
    ],
}

_CAREER_FALLBACK: Dict[str, List[Dict[str, str]]] = {
    "male": [
        {"직군": "전략기획", "이유": "사주 구조상 큰 그림을 그리는 역할이 장기적으로 유리합니다"},
        {"직군": "전문직", "이유": "깊이 있는 전문성을 쌓는 커리어가 안정적으로 이어집니다"},
    ],
    "female": [
        {"직군": "교육·상담", "이유": "사주 구조상 사람을 돕고 가르치는 역할이 잘 맞습니다"},
        {"직군": "전문직·컨설팅", "이유": "전문성을 쌓아 조언하는 역할에서 빛납니다"},
    ],
}

_GI_AVOID: Dict[str, List[str]] = {
    "목": ["목재·환경 계열은 기신 목 에너지를 강화해 에너지 소진·갈등이 잦아질 수 있습니다", "간·눈·근육 과부하 직무 주의"],
    "화": ["고열·장시간 노출 직무는 기신 화로 심혈관·혈압 악화 위험이 있습니다", "과도한 퍼포먼스·노출 직무 주의"],
    "토": ["변동성 극심한 부동산 투기·도박 계열 주의", "고집이 강해지는 관료적 조직 내 갈등 위험"],
    "금": ["기신 금 계열(법률·군경·금속) 직무는 냉정함 과잉으로 인간관계 마찰이 심화될 수 있습니다", "칼날·금속 환경에서 부상 주의"],
    "수": ["기신 수 계열(IT·무역·관광) 직무는 방향 상실·집중력 저하 위험이 있습니다", "감성 과잉으로 객관 판단이 어려운 직무 주의"],
}


def get_sipsin_job_function(sip_c: Counter[str]) -> List[Dict[str, str]]:
    functions: List[Dict[str, str]] = []
    ss_n = sip_c["식신"] + sip_c["상관"]
    if ss_n >= 5:
        functions.append({
            "역할": "기술 전문가·크리에이터",
            "이유": f"식상이 {ss_n}개로 매우 강해 기술·표현·창작으로 직접 결과물을 만드는 일",
            "구체": "유튜버·작가·기술자·강사·셰프",
        })
    elif ss_n >= 3:
        functions.append({
            "역할": "기획·표현 담당",
            "이유": f"식상이 {ss_n}개로 아이디어를 현실로 만드는 기획·표현직",
            "구체": "기획자·마케터·교사·요리사",
        })
    rex_n = sip_c["편재"] + sip_c["정재"]
    geb_n = sip_c["겁재"]
    if rex_n >= 5:
        functions.append({
            "역할": "영업·사업·거래 전문가",
            "이유": f"재성이 {rex_n}개로 강해 돈과 거래를 직접 다루는 일",
            "구체": "영업사원·무역상·사업가·투자자",
        })
    elif rex_n >= 3 and geb_n < rex_n:
        functions.append({
            "역할": "재무·회계·수익 관리",
            "이유": f"재성이 안정적으로 {rex_n}개 있어 재무 관리와 수익 창출 역할",
            "구체": "회계사·재무팀·세무사·펀드매니저",
        })
    guan_n = sip_c["정관"] + sip_c["편관"]
    if guan_n >= 5:
        functions.append({
            "역할": "관리자·리더·공공기관",
            "이유": f"관성이 {guan_n}개로 강해 조직 내 책임과 권한을 갖는 역할",
            "구체": "공무원·관리자·군경·CEO",
        })
    elif guan_n >= 3:
        functions.append({
            "역할": "조직 내 중간 관리",
            "이유": f"관성이 {guan_n}개로 팀을 이끌고 조율하는 역할",
            "구체": "팀장·부서장·프로젝트매니저",
        })
    ins_n = sip_c["편인"] + sip_c["정인"]
    if ins_n >= 5:
        functions.append({
            "역할": "학자·연구자·교육자",
            "이유": f"인성이 {ins_n}개로 강해 배우고 분석하고 전수하는 일",
            "구체": "교수·연구원·의사·작가·분석가",
        })
    elif ins_n >= 3:
        functions.append({
            "역할": "전문직·컨설턴트",
            "이유": f"인성이 {ins_n}개로 깊이 있는 전문성을 발휘하는 역할",
            "구체": "전문의·변호사·컨설턴트·강사",
        })
    bib_n = sip_c["비견"] + sip_c["겁재"]
    if bib_n >= 6:
        functions.append({
            "역할": "독립사업가·프리랜서",
            "이유": f"비겁이 {bib_n}개로 매우 강해 조직보다 독립적으로 일할 때 빛남",
            "구체": "자영업자·프리랜서·스포츠선수",
        })
    return functions


def get_ohaeng_job_spec(counts: Dict[str, int], yong_el: str) -> List[Dict[str, str]]:
    specs: List[Dict[str, str]] = []
    total = sum(counts.values()) or 1
    for el, cnt in counts.items():
        ratio = cnt / total
        spec = OVER_SPEC.get(el, {})
        if ratio >= 0.35:
            specs.append({"타입": f"{el} 과다 특화", "설명": spec.get("과다", ""), "비율": f"{ratio * 100:.0f}%"})
        elif cnt == 0:
            specs.append({"타입": f"{el} 결핍 주의", "설명": spec.get("결핍", "")})
    return specs


def _sinsal_names_from_block(sinsal: Dict[str, Any]) -> List[str]:
    rows = sinsal.get("신살_목록") or []
    out: List[str] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("신살") or "").strip()
        if name:
            out.append(name)
    return out


def get_sinsal_job_talent(sinsal_names: Sequence[str]) -> List[Dict[str, str]]:
    talents: List[Dict[str, str]] = []
    seen: set[str] = set()
    for raw in sinsal_names:
        for key in SINSAL_JOB:
            if key in raw and key not in seen:
                seen.add(key)
                talents.append({"신살": key, **SINSAL_JOB[key]})
                break
    return talents


def _synthesize_yong_dm_jobs(
    yong_el: str,
    dm: str,
    *,
    dominant_el: str,
    dominant_ratio: float,
    pillar_fp: str = "",
    female: bool = False,
) -> List[Dict[str, str]]:
    domain = YONG_DOMAIN.get(yong_el, {})
    style = DM_WORK_STYLE.get(dm, {})
    jobs: List[str] = list(domain.get("구체", []))
    if not jobs:
        return []
    h = sum(ord(c) for c in dm + yong_el + dominant_el + pillar_fp + ("F" if female else "M"))
    i0 = h % len(jobs)
    i1 = (h // 3 + len(dm)) % len(jobs)
    if i1 == i0 and len(jobs) > 1:
        i1 = (i1 + 1) % len(jobs)
    env = domain.get("환경", "")
    act = domain.get("행위", "")
    return [
        {
            "직군": jobs[i0],
            "이유": (
                f"{dm}일간 {style.get('스타일', '')}으로 {yong_el}({env}) 환경에서 "
                f"{act} 일이 맞습니다. {style.get('강점', '')}"
            ),
        },
        {
            "직군": jobs[i1],
            "이유": (
                f"오행 {dominant_el} 비중 {dominant_ratio * 100:.0f}%와 맞물려 "
                f"{jobs[i1]} 분야에서 {dm}의 {style.get('직무', '')} 역할이 빛납니다"
            ),
        },
    ]


def _match_yong_dm_jobs(
    yong_el: str,
    dm: str,
    *,
    dominant_el: str,
    dominant_ratio: float,
    pillar_fp: str = "",
    female: bool = False,
) -> List[Dict[str, str]]:
    key = (yong_el, dm)
    if key in YONG_DM_COMBO:
        jobs = [dict(x) for x in YONG_DM_COMBO[key]]
        flip = (sum(ord(c) for c in pillar_fp + ("F" if female else "M")) % 2) == 1
        if flip and len(jobs) >= 2:
            jobs = [jobs[1], jobs[0]]
        return jobs
    return _synthesize_yong_dm_jobs(
        yong_el,
        dm,
        dominant_el=dominant_el,
        dominant_ratio=dominant_ratio,
        pillar_fp=pillar_fp,
        female=female,
    )


def _get_avoid_jobs(gi_el: str) -> List[str]:
    avoids = _GI_AVOID.get(gi_el, [])
    if avoids:
        return list(avoids)
    return [f"기신 {gi_el} 계열 업종은 에너지 소진이 크니 용신 방향을 우선 고려하세요"]


def _get_work_type(
    *,
    verdict: str,
    ss_n: int,
    rex_n: int,
    guan_n: int,
    bib_n: int,
) -> List[str]:
    modes: List[str] = []
    if verdict == "신강" and rex_n >= 3:
        modes.append("사업·독립: 재성과 추진력으로 직접 수입을 만드는 구조가 유리합니다")
    if ss_n >= 4:
        modes.append("프리랜서·1인 창작: 표현·기술로 결과물 단가를 높이는 방식이 맞습니다")
    if guan_n >= 3 or verdict == "신약":
        modes.append("직장인: 조직 내 역할이 정해져 있을 때 안정적으로 성과가 납니다")
    if bib_n >= 6:
        modes.append("자영업·프리랜서: 비겁이 강해 조직보다 독립 경로가 맞습니다")
    if not modes:
        modes.append("전문직 축적 후 40대 이후 독립·컨설팅 전환이 균형적입니다")
    return modes


def _get_biz_fit(*, verdict: str, rex_n: int, geb_n: int, ss_n: int) -> str:
    if verdict == "신강" and rex_n >= 3 and geb_n < rex_n:
        return "재성·신강 구조로 단계적 창업·사업 확장 신호가 있습니다. 현금흐름을 먼저 확보하세요"
    if ss_n >= 4:
        return "기술·콘텐츠·전문 서비스형 창업이 장기적으로 맞는 편입니다"
    return "직장에서 전문성을 쌓은 뒤 소규모 사업·부업으로 확장하는 흐름이 안전합니다"


def _career_add(
    top5: List[Dict[str, str]],
    seen: set[str],
    직군: str,
    이유: str,
) -> None:
    j = 직군.strip()
    if not j or j in seen:
        return
    seen.add(j)
    top5.append({"직군": j, "이유": 이유.strip()})


class NativeStoryEngine:
    """동일 원국이라도 성별에 따라 전통 육친+현대 생활 표현을 섞어 스토리를 만든다."""

    PILLAR_KEYS = ("year", "month", "day", "hour")

    def __init__(
        self,
        *,
        day_master: str,
        pillars: dict,
        gender: str,
        counts: Dict[str, int],
        yong: Dict[str, Any],
        sip_c: Counter[str],
        rel_full: Dict[str, Any],
        sinsal: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.day_master = day_master
        self.pillars = pillars
        self.counts = counts
        self.yong = yong
        self.sip_c = sip_c
        self.rel_full = rel_full
        self.sinsal = sinsal or {}
        self.female = sp.is_female_gender(gender)

        self.y_pillar = pillars["year"]["pillar"]
        self.m_pillar = pillars["month"]["pillar"]
        self.d_pillar = pillars["day"]["pillar"]
        self.h_pillar = pillars["hour"]["pillar"]
        self.y_zhi = pillars["year"]["zhi"]
        self.m_zhi = pillars["month"]["zhi"]
        self.d_zhi = pillars["day"]["zhi"]
        self.h_zhi = pillars["hour"]["zhi"]

        self.native_chungs: List[Dict[str, Any]] = [
            r for r in (rel_full.get("원국_충") or []) if isinstance(r, dict)
        ]

        self.ss_n = sip_c["식신"] + sip_c["상관"]
        self.rex_n = sip_c["편재"] + sip_c["정재"]
        self.guan_n = sip_c["정관"] + sip_c["편관"]
        self.ins_n = sip_c["편인"] + sip_c["정인"]
        self.bib_n = sip_c["비견"] + sip_c["겁재"]
        self.geb_n = sip_c["겁재"]

        self.yong_el = (yong.get("용신_오행") or "").strip()
        self.gi_el = _gi_el_str(yong)
        self.verdict = yong.get("일간_강약") or "중화"

    def dm_nature(self) -> Dict[str, str]:
        return dict(_DM_NATURE.get(self.day_master, {"상징": "독특한 기운", "강점": "자신만의 강점", "약점": "자신만의 과제"}))

    def _p4(self) -> str:
        return f"{self.y_pillar}년주·{self.m_pillar}월주·{self.d_pillar}일주·{self.h_pillar}시주"

    def core_line(self) -> str:
        nat = self.dm_nature()
        chung_n = len(self.native_chungs)
        zero_els = [e for e, v in self.counts.items() if v == 0]

        chung_txt = ""
        if chung_n >= 2:
            chung_txt = (
                f"원국에 {chung_n}개의 충이 있어 변화와 도전이 끊이지 않는 역동적인 인생입니다. "
            )
        elif chung_n == 1:
            gz = str(self.native_chungs[0].get("글자", ""))
            chung_txt = f"원국 {gz}충으로 특정 영역에서 긴장이 반복됩니다. "

        zero_txt = ""
        if zero_els:
            elem_kw = {
                "목": "도전과 성장",
                "화": "열정과 표현",
                "토": "안정과 신뢰",
                "금": "결단과 추진",
                "수": "지혜와 유연성",
            }
            kws = [elem_kw.get(e, "") for e in zero_els]
            zero_txt = (
                f"{','.join(zero_els)} 기운이 없어 '{','.join(kws)}'이 평생의 과제입니다. "
            )

        if self.female:
            guan_stress = any(
                self.d_zhi in str(r.get("글자", "")) or self.m_zhi in str(r.get("글자", ""))
                for r in self.native_chungs
            )
            if self.guan_n >= 4:
                rel_txt = "관성이 강해 남편·직장 인연이 복잡하게 얽히기 쉬운 구조입니다"
            elif guan_stress:
                rel_txt = "배우자·직장 자리에 충이 있어 이 두 영역에서 변화가 반복됩니다"
            elif self.guan_n == 0:
                rel_txt = "관성이 없어 남편 인연보다 커리어·독립이 더 잘 맞는 구조입니다"
            else:
                rel_txt = "배우자 인연은 비교적 순조롭게 이어질 수 있습니다"

            if self.ss_n >= 4:
                child_txt = (
                    f"식상이 {self.ss_n}개로 강해 자녀 인연이 깊고 표현력·창의성이 뛰어납니다"
                )
            elif self.ss_n == 0:
                child_txt = "식상이 없어 자녀 인연이 약하거나 늦을 수 있습니다"
            else:
                child_txt = "자녀와의 인연이 있고 창의적 표현에서 보람을 찾습니다"

            return (
                f"{nat['상징']}처럼 {nat['강점']}을 타고난 여성입니다. "
                f"{self._p4()} 원국에서 {rel_txt}. "
                f"{child_txt}. "
                f"{chung_txt}"
                f"{zero_txt}"
                f"용신 {self.yong_el or '—'} 방향에서 운이 가장 잘 풀립니다."
            )

        rex_stress = any(self.d_zhi in str(r.get("글자", "")) for r in self.native_chungs)
        if self.rex_n >= 4:
            rel_txt = "재성이 강해 아내·재물 인연이 풍부하고 사업 감각이 뛰어납니다"
        elif self.geb_n > self.rex_n:
            rel_txt = "겁재가 재성보다 강해 재물과 배우자 인연에서 경쟁·손실 변수가 있습니다"
        elif rex_stress:
            rel_txt = "배우자 자리에 충이 있어 아내와의 관계에서 변화가 생기기 쉽습니다"
        else:
            rel_txt = "배우자 인연은 안정적으로 이어질 수 있는 구조입니다"

        if self.guan_n >= 3:
            child_txt = (
                f"관성이 {self.guan_n}개로 강해 자녀에 대한 책임감이 크고 사회적 명예를 중시합니다"
            )
        elif self.guan_n == 0:
            child_txt = "관성이 없어 자녀보다 자유로운 삶의 방식이 더 맞을 수 있습니다"
        else:
            child_txt = "자녀 인연이 있고 가장으로서의 책임감이 강합니다"

        return (
            f"{nat['상징']}처럼 {nat['강점']}을 타고난 남성입니다. "
            f"{self._p4()} 원국에서 {rel_txt}. "
            f"{child_txt}. "
            f"{chung_txt}"
            f"{zero_txt}"
            f"용신 {self.yong_el or '—'} 방향에서 운이 가장 잘 풀립니다."
        )

    def year_pillar_story(self) -> str:
        y, yz = self.y_pillar, self.y_zhi
        if self.female:
            return (
                f"{y} 년주(지지 {yz})는 모친·조상 축과 유년 환경을 말합니다. "
                f"여명에서는 인성(모친·보호)과 맞물려 정서적 뿌리가 커리어·독립 타이밍에도 영향을 줍니다. "
                f"전통 육친으로 보면 ‘집안 기운’이 곧 안전욕구로 이어지고, 현대적으로는 육아·가정 양립을 설계할 때 "
                f"년주가 먼저 흔들리지 않게 경계를 세우는 것이 중요합니다."
            )
        return (
            f"{y} 년주(지지 {yz})는 가문의 기대와 사회 첫 얼개를 나타냅니다. "
            f"남명에서는 비겁·관성이 맞물릴 때 형제·동료 경쟁과 명예욕이 이 축에서 동시에 요구됩니다. "
            f"전통적으로는 부친·조상의 그림자가 사업·가장 역할에 스며들고, 현대적으로는 성취·리더십을 증명하려는 "
            f"압박을 년주에서 먼저 읽을 수 있습니다."
        )

    def month_pillar_story(self) -> str:
        m, mz = self.m_pillar, self.m_zhi
        if self.female:
            return (
                f"{m} 월주(지지 {mz})는 사회화·직장·배우자 부모(시댁) 축과 연결됩니다. "
                f"여성에게 재성(정재·편재)은 시댁·재물로도 읽히므로 월주가 강하면 커리어와 가정 양립에서 "
                f"‘규범과 실리’가 동시에 작동합니다. "
                f"관성이 월에 깔리면 남편·상사 이미지가 이 시기에 각인되기 쉽습니다."
            )
        return (
            f"{m} 월주(지지 {mz})는 직장·관록·자녀(관성)와 부친의 기대가 겹치는 자리입니다. "
            f"남성에게 관성은 자녀·명예·책임으로 풀리므로 월주가 말하는 ‘사회적 역할’이 가장·경쟁자 국면으로 "
            f"바로 연결됩니다. "
            f"재성이 월에 붙으면 아내·재물 기회가 초중반 운의 중심축이 됩니다."
        )

    def day_pillar_story(self) -> str:
        d, dz = self.d_pillar, self.d_zhi
        if self.female:
            return (
                f"{d} 일주(지지 {dz})는 본인과 배우자궁(관성 참고)의 핵심입니다. "
                f"여명에서 식상은 자녀·표현·독립심으로 일간과 맞물리므로, 일주가 말하는 ‘나’는 "
                f"육아·창작·관계에서의 자기주장과 직결됩니다. "
                f"비겁이 일간을 돕면 자매·경쟁녀 속에서도 주체성이 살아납니다."
            )
        return (
            f"{d} 일주(지지 {dz})는 자아와 배우자(재성)·내실 재물의 중심입니다. "
            f"남명에서 재성은 아내·애인·사업으로 읽혀 일주의 안정이 곧 가정 경제와 연액됩니다. "
            f"식상이 강하면 장인·처갓집·기술 재능이 일간을 보완하는 축으로 작동합니다."
        )

    def hour_pillar_story(self) -> str:
        h, hz = self.h_pillar, self.h_zhi
        if self.female:
            return (
                f"{h} 시주(지지 {hz})는 말년·자녀·표현의 결실 자리입니다. "
                f"여성에게 식상이 시에 있으면 자녀·독립·콘텐츠가 말년 테마로 커지고, "
                f"관성이 시에 있으면 남편·직장의 ‘뒷바람’이나 책임이 늦은 나이에 재조명됩니다. "
                f"현대적으로는 커리어 후반·관계 정리에서 시주가 결정타가 됩니다."
            )
        return (
            f"{h} 시주(지지 {hz})는 후손·사회적 마무리·기술 명성 축입니다. "
            f"남성에게 관성이 시에 있으면 자녀 교육·직책 명예가 말년 과제로 올라오고, "
            f"재성이 시에 있으면 아내·노후 자산이 동시에 걸립니다. "
            f"현대적으로는 사업 승계·멘토링·레거시 설계가 시주 해석의 핵입니다."
        )

    def personality_story(self) -> Dict[str, Any]:
        nat = self.dm_nature()
        p4 = self._p4()

        if self.female:
            strengths: List[str] = []
            if self.ss_n >= 4:
                strengths.append(
                    f"식신·상관이 {self.ss_n}개로 강해 자녀 양육과 창의적 표현에서 타고난 능력이 발휘됩니다. "
                    f"{self.d_pillar} 일주와 맞물려 말과 글, 손재주로 빛나는 여성입니다"
                )
            if self.guan_n >= 3:
                strengths.append(
                    f"관성이 {self.guan_n}개로 커리어와 사회적 역할에서 책임감과 신뢰를 빠르게 쌓습니다. "
                    f"{self.m_pillar} 월주가 말하는 남편·직장상사 축과도 연결되어 직장에서 인정받는 유형입니다"
                )
            if self.ins_n >= 3:
                strengths.append(
                    "인성이 강해 배움과 모성(전통 육친)이 깊습니다. "
                    f"{self.y_pillar} 년주 방향의 보호 기운과 합쳐져 가족을 보살피고 지식을 쌓는 데서 진정한 보람을 찾습니다"
                )
            if self.rex_n >= 3:
                strengths.append(
                    "재성이 강해 살림과 재무 감각이 뛰어납니다. "
                    f"{p4}에서 읽히듯 시댁·재물(여명 재성)을 실질적으로 이끄는 능력이 있습니다"
                )
            if self.bib_n >= 3:
                strengths.append(
                    "비겁이 강해 독립심과 자아가 강합니다. "
                    f"{self.h_pillar} 시주와 맞물려 자매·경쟁녀 속에서도 스스로 길을 개척하는 여성입니다"
                )
            female_fb_s = [
                f"{nat['상징']}처럼 {nat['강점']}으로 주변에 신뢰와 안정감을 줍니다",
                "한번 맺은 인연은 끝까지 지키는 깊은 의리와 따뜻함이 있습니다",
                "위기 상황에서 감정을 추스르고 현실적인 해결책을 찾는 능력이 있습니다",
                "세심한 관찰력으로 상대방의 감정을 먼저 알아채는 공감 능력이 뛰어납니다",
                "오랜 시간 쌓은 전문성이 나이 들수록 더 빛나는 구조입니다",
            ]
            for s in female_fb_s:
                if len(strengths) >= 5:
                    break
                if s not in strengths:
                    strengths.append(s)
            strengths = list(dict.fromkeys(strengths))[:5]

            weaknesses: List[str] = []
            if self.guan_n >= 4:
                weaknesses.append(
                    "관성이 과다해 남편·직장 스트레스를 혼자 감당하려다 번아웃이 오기 쉽습니다. "
                    "도움을 요청하는 것도 능력입니다"
                )
            if self.ss_n >= 4 and self.guan_n >= 3:
                weaknesses.append(
                    "자녀·커리어·남편을 동시에 챙기려는 완벽한 여성상을 추구하다 정작 본인이 지치기 쉽습니다"
                )
            if self.geb_n >= 3:
                weaknesses.append(
                    "경쟁 의식이 강해 여성 관계에서 질투나 갈등이 생기기 쉽습니다. "
                    "협력을 선택하면 더 큰 것을 얻습니다"
                )
            if len(self.native_chungs) >= 2:
                weaknesses.append(
                    f"원국에 충이 {len(self.native_chungs)}개 있어 감정 기복과 환경 변화가 잦습니다. "
                    "일상의 루틴이 안정의 핵심입니다"
                )
            if self.ins_n >= 5:
                weaknesses.append(
                    "걱정과 생각이 많아 결정을 미루거나 남에게 의존하려는 경향이 있습니다"
                )
            female_fb_w = [
                "가까운 사람에게 더 엄격한 기준을 적용하는 경향이 있어 관계의 온도 조절이 필요합니다",
                "피로가 쌓이면 감정이 한꺼번에 터지는 패턴이 있어 미리 쉬는 시간을 확보하세요",
                "완벽한 어머니·가정의 동반자·직장인이 되려다 정작 자신을 잃는 경우를 주의하세요",
                f"{nat['약점']}을 주의해야 합니다. 스스로 인식하는 것만으로도 크게 개선됩니다",
                "기신 오행이 강해지는 시기에 감정 소비가 커지므로 에너지 관리가 중요합니다",
            ]
            seen_w = set(weaknesses)
            for w in female_fb_w:
                if len(weaknesses) >= 5:
                    break
                if w not in seen_w:
                    weaknesses.append(w)
                    seen_w.add(w)
            weaknesses = list(dict.fromkeys(weaknesses))[:5]

            if self.ss_n >= self.guan_n:
                social = (
                    "표현력과 감수성으로 사람을 끌어당기는 스타일입니다. 대화에서 공감을 먼저 해주는 편이라 "
                    "주변에 친구가 많고 신뢰를 빠르게 쌓습니다"
                )
            elif self.guan_n > self.ss_n:
                social = (
                    "역할과 책임을 중시하는 편입니다. 직장·조직에서 신뢰를 쌓는 속도가 빠르고 "
                    "한번 믿으면 끝까지 지키는 의리가 있습니다. 단, 규범과 다른 행동에는 불편함을 느낍니다"
                )
            else:
                social = (
                    "소수의 깊은 인연을 선호합니다. 넓은 네트워크보다 오래된 친구·가족을 소중히 여기며 "
                    "처음엔 조심스럽지만 신뢰가 쌓이면 진심을 다합니다"
                )

            if self.guan_n >= 4:
                stress = (
                    "남편·직장 압박이 겹치면 속으로 삭이다 한꺼번에 터지는 패턴입니다. "
                    "혼자 감당하지 말고 신뢰하는 사람에게 털어놓는 것이 가장 빠른 회복법입니다"
                )
            elif self.ins_n >= 5:
                stress = (
                    "스트레스 시 걱정·생각이 길어지고 혼자 검색하거나 추측이 많아집니다. "
                    "몸을 움직이는 활동(산책·운동)이 생각을 멈추는 가장 효과적인 방법입니다"
                )
            elif self.ss_n >= 4:
                stress = (
                    "스트레스를 수다·창작·쇼핑으로 푸는 편입니다. 혼자 있는 시간보다 사람과 교류할 때 회복 속도가 빠릅니다. "
                    "단, 충동 지출은 주의하세요"
                )
            else:
                stress = (
                    "평소 무던해 보이다 한계선에서 감정이 터지는 패턴입니다. "
                    "달력에 '나만의 회복일'을 미리 넣어두는 것이 효과적입니다"
                )

            if self.rex_n >= self.guan_n:
                decide = (
                    "실리와 현실을 보며 결정하는 편입니다. 가족에게 미치는 영향을 먼저 계산하고 움직이는 신중한 타입이지만 "
                    "결심하면 빠르게 실행합니다"
                )
            elif self.guan_n > self.rex_n:
                decide = (
                    "규범과 주변 시선을 고려해 안전한 선택을 하는 편입니다. "
                    "결정이 신중한 만큼 후회가 적고 가족·직장의 안정을 최우선합니다"
                )
            else:
                decide = (
                    "직관과 감으로 결정하는 편입니다. 첫 느낌이 정확한 경우가 많지만 "
                    "큰 결정(부동산·투자·이직)은 데이터를 먼저 확인 후 결정하세요"
                )
        else:
            strengths = []
            if self.rex_n >= 4:
                strengths.append(
                    f"재성이 {self.rex_n}개로 강해 아내·재물·사업에서 타고난 감각이 있습니다. "
                    f"{self.y_pillar}·{self.d_pillar} 축을 보면 거래와 협상에서 주도권을 잡고 실질적인 성과를 만드는 능력이 뛰어납니다"
                )
            if self.guan_n >= 3:
                strengths.append(
                    f"관성이 {self.guan_n}개로 자녀에 대한 책임감이 강하고 조직에서 리더십을 발휘합니다. "
                    f"{self.m_pillar} 월주와 맞물려 사회적 명예와 신뢰를 중시하는 남성입니다"
                )
            if self.ss_n >= 4:
                strengths.append(
                    f"식상이 {self.ss_n}개로 강해 아이디어와 기술로 결과물을 만드는 창의적 역량이 뛰어납니다. "
                    f"{self.h_pillar} 시주 방향의 장인·처갓집·재능 축과도 연결됩니다"
                )
            if self.ins_n >= 3:
                strengths.append(
                    "인성이 강해 학문과 분석에 깊이 몰입합니다. "
                    f"{self.y_pillar} 년주가 말하는 모친·보호 기운과 합쳐져 전문가로서의 내공이 나이 들수록 더 빛나는 구조입니다"
                )
            if self.bib_n >= 4:
                strengths.append(
                    "비겁이 강해 어떤 상황에서도 스스로 버티는 강한 독립심이 있습니다. "
                    "형제·동료·경쟁 환경에서 오히려 더 빛나는 타입입니다"
                )
            male_fb_s = [
                f"{nat['상징']}처럼 {nat['강점']}으로 가장으로서 든든한 버팀목이 됩니다",
                "한번 결심하면 끝까지 밀어붙이는 실행력과 뚝심이 있습니다",
                "위기 상황에서 오히려 침착해지는 역경 돌파 능력이 있습니다",
                "오랜 시간 쌓은 전문성이 나이 들수록 더 빛나는 구조입니다",
                "작은 약속도 지키는 신뢰감으로 조직과 가정에서 기둥 역할을 합니다",
            ]
            for s in male_fb_s:
                if len(strengths) >= 5:
                    break
                if s not in strengths:
                    strengths.append(s)
            strengths = list(dict.fromkeys(strengths))[:5]

            weaknesses = []
            if self.guan_n >= 5:
                weaknesses.append(
                    "관성이 과다해 자녀와 직장 두 가지 책임을 동시에 지며 번아웃이 오기 쉽습니다. "
                    "역할 분담과 위임을 배우세요"
                )
            if self.geb_n >= self.rex_n + 1:
                weaknesses.append(
                    "겁재가 재성보다 강해 동업·투자·보증에서 손실이 생기기 쉽습니다. "
                    "단독 결정보다 파트너와 검토 후 실행하는 습관이 필요합니다"
                )
            if self.ss_n <= 1 and self.guan_n >= 3:
                weaknesses.append(
                    "표현력(식상)이 약해 감정을 말로 표현하기보다 행동으로 보여주려는 경향이 있습니다. "
                    "가족·배우자와의 대화를 늘리세요"
                )
            if len(self.native_chungs) >= 2:
                weaknesses.append(
                    f"원국에 충이 {len(self.native_chungs)}개 있어 직업과 가정에서 변화가 잦습니다. "
                    "한 가지에 집중하는 시기를 정하면 에너지 소진을 줄일 수 있습니다"
                )
            if self.ins_n >= 5:
                weaknesses.append(
                    "생각이 너무 많아 결정을 미루거나 과분석하는 경향이 있습니다. "
                    "'80점으로 일단 실행'하는 습관이 큰 차이를 만듭니다"
                )
            male_fb_w = [
                "가까운 사람에게 더 높은 기준을 요구하는 경향이 있어 가족·부하직원과 마찰이 생길 수 있습니다",
                "성과와 결과에 집착하다 과정의 소중함을 놓치기 쉽습니다",
                "고집이 강해 한번 결정하면 바꾸기 어려운 면이 있습니다. 정보 업데이트를 의식적으로 하세요",
                f"{nat['약점']}을 주의하세요. 인식만으로도 크게 개선됩니다",
                "기신 오행이 강해지는 시기에 충동적 결정을 내리기 쉬우니 주요 결정은 그 시기를 피하세요",
            ]
            seen_m = set(weaknesses)
            for w in male_fb_w:
                if len(weaknesses) >= 5:
                    break
                if w not in seen_m:
                    weaknesses.append(w)
                    seen_m.add(w)
            weaknesses = list(dict.fromkeys(weaknesses))[:5]

            if self.rex_n >= self.ss_n:
                social = (
                    "실리와 교환가치를 중시하는 편입니다. 신뢰는 약속 이행과 금전적 명료함에서 생기며 "
                    "이해관계가 맞을 때 가장 활발하게 움직입니다. 감정적 접근보다 결과로 말하는 타입입니다"
                )
            elif self.guan_n >= self.rex_n:
                social = (
                    "위계와 역할을 중시합니다. 선후배·직급 관계에서 예의를 갖추는 편이며 "
                    "한번 맺은 의리는 끝까지 지킵니다. 처음엔 거리감이 있어 보이지만 신뢰가 쌓이면 깊은 우정을 나눕니다"
                )
            else:
                social = (
                    "소수의 깊은 인연을 선호합니다. 넓은 인맥보다 믿을 수 있는 핵심 파트너를 중시하며 "
                    "한번 등 돌리면 회복이 어려운 타입입니다. 관계에서 진심이 전달되는 것이 중요합니다"
                )

            if self.guan_n >= 4:
                stress = (
                    "직장·자녀 압박이 겹치면 더 바짝 매달리다 몸이 먼저 반응합니다. "
                    "근육 긴장·수면 문제가 신호이니 운동·사우나로 몸부터 풀어주세요"
                )
            elif self.geb_n >= 4:
                stress = (
                    "경쟁·비교 의식이 발동하면 무리한 약속이나 과시적 지출로 번아웃이 올 수 있습니다. "
                    "자신만의 기준을 세우고 남과의 비교를 줄이는 것이 핵심입니다"
                )
            elif self.ins_n >= 5:
                stress = (
                    "스트레스 시 혼자 삭이거나 과도한 분석으로 결정을 미룹니다. "
                    "신뢰하는 사람과 대화하면 회복 속도가 훨씬 빨라집니다"
                )
            else:
                stress = (
                    "평소 무던해 보이다 한계선에서 폭발하는 패턴이 있습니다. "
                    "주 1회 이상 '혼자만의 시간'을 의도적으로 만드는 것이 효과적입니다"
                )

            if self.rex_n >= self.guan_n and self.bib_n >= 3:
                decide = (
                    "손익 계산이 빠르고 결정 속도가 빠른 편입니다. 사업·투자에서는 강점이지만 "
                    "가족 관련 결정은 한 박자 늦춰 배우자와 상의 후 결정하세요"
                )
            elif self.guan_n > self.rex_n:
                decide = (
                    "규정과 안전을 중시해 신중하게 결정하는 편입니다. "
                    "결정이 느릴 수 있지만 그만큼 실수가 적고 신뢰를 쌓습니다"
                )
            else:
                decide = (
                    "직관과 경험 법칙으로 결정하는 편입니다. "
                    "큰 결정(부동산·이직·사업)은 데이터와 주변 의견을 수렴한 뒤 확정하는 것이 후회를 줄입니다"
                )

        pad_used: set[str] = set()
        strengths = [
            _min_chars(
                s.strip(), 100, pool=_PAD_STRENGTH_POOL, used_fillers=pad_used
            )
            for s in strengths
            if s.strip()
        ]
        weaknesses = [
            _min_chars(
                s.strip(), 100, pool=_PAD_WEAKNESS_POOL, used_fillers=pad_used
            )
            for s in weaknesses
            if s.strip()
        ]

        gender_label = "여명" if self.female else "남명"
        return {
            "장점_5": strengths,
            "단점_5": weaknesses,
            "대인관계_스타일": _min_chars(social.strip(), 80),
            "스트레스_반응": _min_chars(stress.strip(), 80),
            "의사결정_방식": _min_chars(decide.strip(), 80),
            "_성별": gender_label,
            "_참고_성별해석축": gender_label,
        }

    def career_story(self) -> Dict[str, Any]:
        """용신+일간+십신+오행+신살 조합으로 이 사주만의 직업군을 도출한다."""
        dm = self.day_master
        yong_el = self.yong_el or "토"
        domain = YONG_DOMAIN.get(yong_el, {})
        style = DM_WORK_STYLE.get(dm, {})

        total = sum(self.counts.values()) or 1
        dominant_el = max(self.counts, key=self.counts.get)
        dominant_ratio = self.counts[dominant_el] / total

        functions = get_sipsin_job_function(self.sip_c)
        specs = get_ohaeng_job_spec(self.counts, yong_el)
        talents = get_sinsal_job_talent(_sinsal_names_from_block(self.sinsal))
        pillar_fp = self._p4()

        top5: List[Dict[str, str]] = []
        seen: set[str] = set()

        gender_tail = (
            "가정·조직 균형을 고려한 역할 설계가 장기적으로 유리합니다."
            if self.female
            else "책임·수입 안정을 함께 잡는 구조가 유리합니다."
        )

        for job in _match_yong_dm_jobs(
            yong_el,
            dm,
            dominant_el=dominant_el,
            dominant_ratio=dominant_ratio,
            pillar_fp=pillar_fp,
            female=self.female,
        )[:2]:
            reason = f"{job['이유']}. {pillar_fp} 원국과 연결됩니다. {gender_tail}"
            _career_add(top5, seen, job["직군"], reason)

        func_slice = functions[:2]
        if self.female and len(functions) > 2:
            func_slice = functions[1:3] if len(functions) >= 3 else functions
        elif not self.female and len(functions) > 1:
            func_slice = functions[:2]

        for func in func_slice:
            if len(top5) >= 5:
                break
            _career_add(
                top5,
                seen,
                func["역할"],
                (
                    f"{func['이유']}. {func['역할']} 유형으로 "
                    f"{func['구체']} 등이 잘 맞습니다"
                ),
            )

        for talent in talents[:1]:
            if len(top5) >= 5:
                break
            first_job = str(talent.get("직업", "")).split("·")[0].strip()
            _career_add(
                top5,
                seen,
                first_job or talent["신살"],
                (
                    f"{talent['신살']}이 있어 {talent['이유']}. "
                    f"{talent['직업']} 분야에서 특별한 재능이 있습니다"
                ),
            )

        domain_jobs = list(domain.get("구체", []))
        h = sum(ord(c) for c in dm + yong_el + pillar_fp + ("F" if self.female else "M"))
        for spec in specs[:1]:
            if len(top5) >= 5 or not domain_jobs:
                break
            pick = domain_jobs[(h + len(spec.get("타입", ""))) % len(domain_jobs)]
            _career_add(
                top5,
                seen,
                pick,
                f"{spec.get('타입', '')}: {spec.get('설명', '')}. {dm}일간에 맞는 {yong_el} 분야 특화",
            )

        gender_key = "female" if self.female else "male"
        fb_idx = 0
        while len(top5) < 5:
            pool = domain_jobs + [x["직군"] for x in _CAREER_FALLBACK[gender_key]]
            added = False
            for label in pool:
                if label in seen:
                    continue
                _career_add(
                    top5,
                    seen,
                    label,
                    (
                        f"{yong_el} 용신 환경({domain.get('환경', '')})에서 "
                        f"{dm}일간 {style.get('스타일', '')}으로 일할 때 적합합니다"
                    ),
                )
                added = True
                break
            if not added:
                fb = _CAREER_FALLBACK[gender_key]
                if fb_idx < len(fb):
                    _career_add(top5, seen, fb[fb_idx]["직군"], fb[fb_idx]["이유"])
                    fb_idx += 1
                else:
                    break

        core_reason = (
            f"{dm}일간 {style.get('스타일', '')}으로 "
            f"{yong_el} 에너지가 살아나는 환경({domain.get('환경', '')})에서 "
            f"{domain.get('행위', '')} 일이 가장 잘 맞습니다. "
            f"특히 {style.get('강점', '')}."
        )

        return {
            "최적_직군_TOP5": top5[:5],
            "직업_핵심_이유": core_reason,
            "오행_특화": specs,
            "신살_재능": talents,
            "피해야_할_직군": _get_avoid_jobs(self.gi_el),
            "사업_적합": _get_biz_fit(
                verdict=self.verdict,
                rex_n=self.rex_n,
                geb_n=self.geb_n,
                ss_n=self.ss_n,
            ),
            "근무형태_판정": _get_work_type(
                verdict=self.verdict,
                ss_n=self.ss_n,
                rex_n=self.rex_n,
                guan_n=self.guan_n,
                bib_n=self.bib_n,
            ),
            "_성별": "여명" if self.female else "남명",
        }

    def health_story(self) -> Dict[str, Any]:
        organ_female = {
            "목": "간·담·눈·근육·관절",
            "화": "심장·혈압·혈관·소화",
            "토": "위장·비장·췌장·피부",
            "금": "폐·대장·기관지·뼈",
            "수": "신장·방광·부인과·허리",
        }
        organ_male = {
            **{k: v for k, v in organ_female.items() if k != "수"},
            "수": "신장·방광·요로·허리",
        }

        dom = oh.dominant_weak_elements(self.counts)
        weak_e = list(dom.get("weak") or [])

        if self.female:
            organ = organ_female
            weak_desc: List[str] = []
            for e in weak_e[:2]:
                o = organ.get(e, "")
                weak_desc.append(
                    f"{e}({o}) 기운이 약해 여성으로서 이 부위를 꼼꼼히 챙겨야 합니다"
                )
            if "수" in weak_e or self.counts.get("수", 0) <= 1:
                weak_desc.append(
                    "수(신장·방광·부인과) 기운이 약해 생리불순·냉증·부인과 질환에 특별히 주의가 필요합니다. "
                    "수분 섭취와 하체 보온을 습관화하세요"
                )
            if self.ss_n >= 4:
                weak_desc.append(
                    "식상이 강해 에너지 소비가 크고 육아·일을 병행할 때 철분 부족·빈혈에 주의하세요"
                )

            age_notes = {
                "20~30대": (
                    "출산·육아 시기와 맞물려 철분·칼슘·수면이 가장 중요합니다. "
                    "산후 우울·갑상선 이상을 놓치지 마세요"
                ),
                "40~50대": (
                    "갱년기가 시작되는 시기로 호르몬 변화에 따른 골밀도·심혈관·자궁 건강을 정기 검진으로 관리하세요"
                ),
                "60대 이후": (
                    "골다공증·관절염·순환 관리가 핵심입니다. 가벼운 유산소 운동과 칼슘·비타민D 섭취를 꾸준히 하세요"
                ),
            }

            longevity = (
                "여성으로서 생명력은 강한 편입니다. "
                "호르몬 변화 시기(갱년기)를 잘 관리하면 건강하게 장수할 수 있습니다"
            )
            if self.guan_n >= 4:
                longevity = (
                    "남편·직장 스트레스가 건강의 가장 큰 적입니다. 스트레스 관리가 장수의 핵심입니다"
                )

            advice = [
                "충·해가 걸린 지지 장부는 여성 정기 검진(자궁·유방·갑상선) 우선",
                "부인과 검진을 매년 빠짐없이 챙기세요",
                f"용신 {self.yong_el or '—'} 계절에 야외 활동·햇빛을 늘리면 면역력과 활력이 올라갑니다",
            ]

        else:
            organ = organ_male
            weak_desc = []
            for e in weak_e[:2]:
                o = organ.get(e, "")
                weak_desc.append(
                    f"{e}({o}) 기운이 약해 남성으로서 이 부위에 만성 질환이 생기기 쉽습니다"
                )
            if self.counts.get("화", 0) >= 4:
                weak_desc.append(
                    "화(심장·혈압·혈관) 기운이 과다해 고혈압·부정맥·뇌졸중에 주의가 필요합니다. "
                    "음주·과로를 줄이는 것이 첫 번째입니다"
                )
            if self.guan_n >= 4:
                weak_desc.append(
                    "관성 과다로 직장 스트레스가 크고 위장·심혈관·근골격계에 만성 피로가 쌓이기 쉽습니다"
                )

            age_notes = {
                "20~30대": (
                    "과음·과로가 가장 위험합니다. 간 기능·혈압을 정기적으로 체크하고 수면의 질을 최우선으로 챙기세요"
                ),
                "40~50대": (
                    "성인병(고혈압·당뇨·고지혈증)이 시작되는 시기입니다. "
                    "종합검진을 2년에 한 번에서 매년으로 늘리세요"
                ),
                "60대 이후": (
                    "전립선·심혈관·관절 관리가 핵심입니다. 근력 운동을 유지해 낙상·근감소증을 예방하세요"
                ),
            }

            longevity = (
                "건강 수명은 40대 생활 습관에 달려 있습니다. 금연·절주·규칙적 운동이 10년을 더 건강하게 만듭니다"
            )
            if self.guan_n >= 5 or self.geb_n >= 4:
                longevity = (
                    "스트레스와 경쟁 압박이 건강의 가장 큰 위협입니다. 마음 관리가 신체 건강의 선행 조건입니다"
                )

            advice = [
                "충·형이 걸린 지지 장부는 남성 정기 검진(심혈관·간·전립선) 우선",
                "음주 횟수를 줄이고 수면 7시간을 지키는 것만으로도 건강 지표가 크게 개선됩니다",
                f"용신 {self.yong_el or '—'} 방향 운동 환경에서 활동하면 면역력과 활력이 올라갑니다",
            ]

        if not weak_desc:
            weak_desc = ["종합 검진으로 개인 우선순위를 확인하세요"]

        gender_label = "여명" if self.female else "남명"
        return {
            "선천_취약_축": weak_desc[:3],
            "나이대별_주의": age_notes,
            "장수_가능성": _min_chars(longevity.strip(), 100),
            "건강_유지_조언": advice,
            "_성별": gender_label,
        }

    def build_full_story(self) -> Dict[str, Any]:
        gender_label = "여명" if self.female else "남명"
        return {
            "핵심_한줄": self.core_line(),
            "년주_해설": self.year_pillar_story(),
            "월주_해설": self.month_pillar_story(),
            "일주_해설": self.day_pillar_story(),
            "시주_해설": self.hour_pillar_story(),
            "성격_분석": self.personality_story(),
            "직업_적성": self.career_story(),
            "건강_평생": self.health_story(),
            "_성별": gender_label,
        }
