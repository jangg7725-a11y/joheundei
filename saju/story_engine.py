# -*- coding: utf-8 -*-
"""원국 스토리 — 성별(여명·남명)에 따라 문장 체계를 완전히 분리해 생성한다."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from . import ohaeng as oh
from . import sipsin as sp


def _min_chars(text: str, min_len: int, tail: str) -> str:
    s = text.strip()
    if len(s) >= min_len:
        return s
    out = s
    while len(out) < min_len:
        out = f"{out} {tail.strip()}"
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
    ) -> None:
        self.day_master = day_master
        self.pillars = pillars
        self.counts = counts
        self.yong = yong
        self.sip_c = sip_c
        self.rel_full = rel_full
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

        zlab = ("년", "월", "일", "시")
        zpil = (self.y_pillar, self.m_pillar, self.d_pillar, self.h_pillar)
        strengths = [
            _min_chars(
                s,
                100,
                (
                    f"여명 기준 {zlab[i % 4]}주 {zpil[i % 4]}와 연결된 강점입니다. "
                    if self.female
                    else f"남명 기준 {zlab[i % 4]}주 {zpil[i % 4]}와 연결된 강점입니다. "
                )
                + f"{p4} 원국에서 같은 주제도 성별에 따라 다른 무게로 읽힙니다.",
            )
            for i, s in enumerate(strengths)
        ]
        weaknesses = [
            _min_chars(
                s,
                100,
                (
                    f"여명에서 {zlab[i % 4]}주 {zpil[i % 4]} 축을 의식하면 단점 완화에 도움이 됩니다. "
                    if self.female
                    else f"남명에서 {zlab[i % 4]}주 {zpil[i % 4]} 축을 의식하면 단점 완화에 도움이 됩니다. "
                ),
            )
            for i, s in enumerate(weaknesses)
        ]

        gender_label = "여명" if self.female else "남명"
        return {
            "장점_5": strengths,
            "단점_5": weaknesses,
            "대인관계_스타일": _min_chars(social, 80, f"{gender_label} 해석입니다."),
            "스트레스_반응": _min_chars(stress, 80, f"{gender_label} 해석입니다."),
            "의사결정_방식": _min_chars(decide, 80, f"{gender_label} 해석입니다."),
            "_성별": gender_label,
            "_참고_성별해석축": gender_label,
        }

    def career_story(self) -> Dict[str, Any]:
        nat = self.dm_nature()
        yong_jobs = {
            "목": [
                ("교육·출판", "나무처럼 키우고 성장시키는"),
                ("환경·농업", "자연과 생명을 다루는"),
                ("의류·인테리어", "감각으로 공간과 스타일을 만드는"),
            ],
            "화": [
                ("방송·미디어", "빛과 에너지로 사람을 끌어당기는"),
                ("요식업·서비스", "따뜻하게 사람을 모으는"),
                ("미용·패션", "감각과 열정이 필요한"),
            ],
            "토": [
                ("부동산·건설", "실질적 가치를 만드는"),
                ("의료·복지", "생명과 건강을 돌보는"),
                ("금융·보험", "신뢰와 안정이 기반인"),
            ],
            "금": [
                ("법률·군경", "원칙과 정의를 다루는"),
                ("기계·제조", "정밀함과 결단이 필요한"),
                ("의료·수술", "섬세함과 결단이 동시에 필요한"),
            ],
            "수": [
                ("무역·유통", "넓은 시야와 유연성이 필요한"),
                ("철학·상담", "깊은 통찰과 공감이 필요한"),
                ("예술·엔터", "감수성과 창의성이 필요한"),
            ],
        }

        top5: List[Dict[str, str]] = []
        seen: set = set()

        gender_tag = "여명" if self.female else "남명"
        hub_job = f"{gender_tag}·{self.day_master}일간·{self.d_pillar}·용신{self.yong_el or '—'}"
        hub_reason = (
            f"동일 원국이라도 {gender_tag} 해석 축이 갈립니다. "
            f"관성(남편·직장상사)·재성(시댁·재물)·식상(자녀·표현·독립)을 "
            f"커리어·육아·가정 양립 설계에 연결합니다. "
            f"이 슬롯은 {self._p4()}에서 {self.day_master} 일간이 받는 십신 균형을 직무 선택에 먼저 얹은 가이드입니다."
            if self.female
            else (
                f"동일 원국이라도 {gender_tag} 해석 축이 갈립니다. "
                f"재성(아내·재물)·관성(자녀·명예)·비겁(동료·경쟁)을 "
                f"가장·사업·성취 축에 연결합니다. "
                f"이 슬롯은 {self._p4()}에서 {self.day_master} 일간이 받는 십신 균형을 직무 선택에 먼저 얹은 가이드입니다."
            )
        )
        top5.append(
            {
                "직군": hub_job,
                "이유": _min_chars(
                    hub_reason,
                    100,
                    f"{gender_tag} 직업 해석: {self.d_pillar} 일주·용신 {self.yong_el or '—'} 축입니다.",
                ),
            }
        )
        seen.add(hub_job)

        for job, desc in (yong_jobs.get(self.yong_el) or [])[:2]:
            if job in seen:
                continue
            seen.add(job)
            top5.append(
                {
                    "직군": job,
                    "이유": (
                        f"{desc} 분야에서 용신 {self.yong_el or '—'} 에너지가 자연스럽게 발휘됩니다. "
                        f"{self._p4()} 원국과 연결해 보면 장기 커리어 그래프가 안정됩니다."
                    ),
                }
            )

        if self.female:
            if self.ss_n >= 4:
                j = "크리에이터·강사·상담사"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                f"식상이 {self.ss_n}개로 강해 말하고 가르치고 표현하는 일에서 타고난 능력이 빛납니다. "
                                f"1인 미디어·교육·코칭에서 수입과 보람을 동시에 찾을 수 있으며, "
                                f"{self.d_pillar} 일주 여성에게 특히 맞습니다."
                            ),
                        }
                    )
            if self.guan_n >= 3:
                j = "관리직·공공기관·HR"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                "관성이 강해 조직 내 중간 관리자·인사·복지 역할에서 신뢰를 빠르게 쌓습니다. "
                                f"{self.m_pillar} 월주가 말하는 직장상사·남편성 축과도 맞물려 직장 내 커리어우먼형입니다"
                            ),
                        }
                    )
            if self.ins_n >= 4:
                j = "연구·컨설팅·전문직"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                "인성이 깊어 전문 지식을 쌓고 조언하는 역할에서 두각을 나타냅니다. "
                                f"{self.y_pillar} 년주와 연결된 모친·학문 보호 축이 여성 전문가 신뢰도를 높입니다"
                            ),
                        }
                    )
            if self.rex_n >= 3:
                j = "영업·유통·스타트업"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                "재성이 강해 거래 감각과 실물 경제 감각이 뛰어납니다. "
                                f"시댁·재물(여명 재성)을 {self.h_pillar} 시주 방향까지 엮어 보면 "
                                "여성 사업가로서 섬세함과 실행력을 겸비한 타입입니다"
                            ),
                        }
                    )
            for fb in (
                {"직군": "의료·간호·돌봄", "이유": "사람을 직접 돕는 분야에서 따뜻한 에너지가 빛납니다"},
                {"직군": "뷰티·웰니스", "이유": "감각과 세심함이 필요한 분야에 적성이 있습니다"},
            ):
                if len(top5) >= 5:
                    break
                if fb["직군"] not in seen:
                    seen.add(fb["직군"])
                    top5.append(fb)

            modes = []
            if self.verdict == "신강" and self.rex_n >= 3:
                modes.append(
                    "창업·독립: 추진력과 재성이 맞물려 여성 창업가로서 강한 실행력을 발휘합니다. "
                    "육아와 일을 병행할 수 있는 유연한 구조 설계가 핵심입니다"
                )
            if self.ss_n >= 4:
                modes.append(
                    "프리랜서·1인 기업: 표현력을 살린 콘텐츠·강의·컨설팅으로 육아·가정과 병행 가능한 수입 구조를 만들 수 있습니다"
                )
            if self.guan_n >= 3 or self.verdict == "신약":
                modes.append(
                    "직장인: 조직 내 역할이 명확할 때 커리어와 안정을 동시에 잡을 수 있습니다. "
                    "육아휴직·복직 시 조직 충성도가 높아집니다"
                )
            if not modes:
                modes.append(
                    "파트타임·병행직: 가정과 일의 균형을 잡으며 전문성을 쌓다가 적절한 시기에 풀타임 또는 독립으로 전환하는 흐름이 좋습니다"
                )

            avoid = []
            if self.gi_el:
                avoid.append(
                    f"기신 {self.gi_el} 계열 업종은 에너지 소진이 크고 가정·건강과의 균형이 깨지기 쉽습니다"
                )

            biz = (
                "재성·신강 구조로 여성 창업에 적합한 신호가 있습니다. 육아 시기를 고려한 단계적 창업을 추천합니다"
                if self.verdict == "신강" and self.rex_n >= 3
                else "직장 경력을 쌓은 후 40대 이후 소규모 독립이 가장 안정적인 흐름입니다"
            )

        else:
            if self.rex_n >= 4:
                j = "사업·영업·투자"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                f"재성이 {self.rex_n}개로 강해 거래·협상·투자에서 타고난 감각이 있습니다. "
                                f"가장으로서 재물을 직접 만드는 구조에서 최고의 능력을 발휘하며, "
                                f"{self.d_pillar} 일주 남성에게 아내·사업 축이 강하게 작동합니다"
                            ),
                        }
                    )
            if self.ss_n >= 4:
                j = "기술직·개발·전문가"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                f"식상이 {self.ss_n}개로 강해 기술과 전문성으로 결과물을 만드는 남성 전문가형입니다. "
                                f"장인·처갓집(식상) 보완과 {self.h_pillar} 시주가 말하는 재능이 수입으로 연결됩니다"
                            ),
                        }
                    )
            if self.guan_n >= 4:
                j = "관리직·공무원·군경"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                f"관성이 {self.guan_n}개로 강해 조직과 규범 안에서 책임감 있는 리더십을 발휘합니다. "
                                f"자녀·명예(남명 관성)와 맞물려 승진·진급에서 두각을 나타내는 타입입니다"
                            ),
                        }
                    )
            if self.ins_n >= 4:
                j = "연구·학문·컨설팅"
                if j not in seen:
                    seen.add(j)
                    top5.append(
                        {
                            "직군": j,
                            "이유": (
                                "인성이 깊어 전문 지식을 깊이 파고드는 남성 학자·연구자형입니다. "
                                f"{self.y_pillar} 년주 모친·보호 축과 합쳐져 나이 들수록 가치가 올라가는 커리어입니다"
                            ),
                        }
                    )
            for fb in (
                {"직군": "건설·부동산·인프라", "이유": "실질적 결과물을 만드는 분야에서 강점이 나타납니다"},
                {"직군": "금융·보험·자산관리", "이유": "숫자와 리스크를 다루는 분야에 적성이 있습니다"},
            ):
                if len(top5) >= 5:
                    break
                if fb["직군"] not in seen:
                    seen.add(fb["직군"])
                    top5.append(fb)

            modes = []
            if self.verdict == "신강" and self.rex_n >= 3:
                modes.append(
                    "사업가: 재성과 신강이 맞물려 사업 추진력이 강합니다. "
                    "가장으로서 안정적 수입을 먼저 확보한 뒤 단계적으로 사업을 키우는 전략이 좋습니다"
                )
            if self.ss_n >= 4:
                modes.append(
                    "전문직·프리랜서: 기술·콘텐츠·전문성으로 단가를 높이면 직장보다 더 큰 수입을 만들 수 있는 구조입니다"
                )
            if self.guan_n >= 3 or self.verdict == "신약":
                modes.append(
                    "직장인: 조직 내 역할이 명확할 때 가장으로서 안정적 수입과 사회적 지위를 함께 잡을 수 있습니다"
                )
            if not modes:
                modes.append(
                    "직장 내 전문가로 경력을 쌓은 뒤 40대 이후 소규모 창업 또는 컨설팅으로 전환하는 흐름이 가장 안정적입니다"
                )

            avoid = []
            if self.gi_el:
                avoid.append(
                    f"기신 {self.gi_el} 계열 업종은 에너지 소진이 크고 가장으로서의 수입 안정성이 흔들릴 수 있습니다"
                )

            biz = (
                "재성·신강 구조로 사업 적합 신호가 강합니다. 가족 생계를 고려한 단계적·분산 투자 전략으로 리스크를 줄이세요"
                if self.verdict == "신강" and self.rex_n >= 3
                else "직장 내 전문가 포지션을 먼저 확보하고 부업·투자로 수입 다각화 후 창업을 검토하는 흐름이 안전합니다"
            )

        for idx, it in enumerate(top5):
            it["이유"] = _min_chars(
                it.get("이유", ""),
                100,
                (
                    f"여명 직업 해석: {self.d_pillar} 일간 기준입니다. "
                    if self.female
                    else f"남명 직업 해석: {self.d_pillar} 일간 기준입니다. "
                ),
            )

        return {
            "최적_직군_TOP5": top5[:5],
            "피해야_할_직군": avoid
            or [f"기신 오행 계열 업종은 에너지 소진이 크니 용신 {self.yong_el or '—'} 방향을 우선 고려하세요"],
            "사업_적합": biz,
            "근무형태_판정": modes,
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
            "장수_가능성": _min_chars(longevity, 100, f"{gender_label} {self._p4()} 기준 참고입니다."),
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
