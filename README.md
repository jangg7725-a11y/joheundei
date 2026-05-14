# 四柱八字 사주 분석 서버

생년월일시를 입력하면 원국·합충·용신·대운·세운·월운·일운·신살·궁합을 분석합니다.

---

## 개발환경 세팅

```bash
pip install -r requirements-dev.txt
```

## 테스트 실행

```bash
pytest tests/ -v
```

## 서버 실행

### 원클릭 실행 스크립트

| OS | 파일 | 실행 방법 |
|----|------|-----------|
| Windows | `run_local.bat` | 파일 더블클릭 또는 `.\run_local.bat` |
| Mac / Linux | `run_local.sh` | `chmod +x run_local.sh && ./run_local.sh` |

스크립트가 ① `requirements-dev.txt` 자동 설치 → ② 서버 기동 → ③ 3초 후 브라우저 자동 실행까지 처리합니다.

### 직접 실행

```bash
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

브라우저에서 `http://localhost:8000/` 으로 접속하세요.

---

## 브라우저 체크리스트

서버 실행 후 아래 항목을 순서대로 확인하세요.

| # | 확인 항목 | 기준 |
|---|-----------|------|
| ☐ | **사주 입력 → 분석결과 출력** | 생년월일시 입력 후 결과 카드 정상 표시 |
| ☐ | **세운 탭 — 연도 변경** | 연도 선택기 조작 시 별점·충 내용 즉시 갱신 |
| ☐ | **월운 탭 — 12절월 카드** | 1~12절월 카드가 전부 렌더링, 길흉 배지 표시 |
| ☐ | **일운 탭 — 오늘 일진** | 오늘 날짜·간지·한줄판정·추천행동 정상 출력 |
| ☐ | **충파해 화살표 시각화** | 사주탭 관계도 SVG에 충·파·해·합 화살표 표시 |
| ☐ | **오행 레이더 차트** | 오행탭(또는 사주탭) 레이더 차트 5각형 정상 렌더 |
| ☐ | **타임라인 골드 마커** | 타임라인에 세운 연도 점(dot) 및 색상 그라디언트 표시 |
| ☐ | **모바일 375px — 하단 탭바** | DevTools 375px 뷰포트에서 하단 탭바 표시, 스와이프 전환 동작 |
| ☐ | **궁합 — 두 사람 입력 결과** | 두 사람 사주 입력 후 궁합 점수·내러티브 정상 표시 |

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 프런트엔드 HTML |
| `POST` | `/api/saju` | 사주 전체 분석 |
| `POST` | `/api/goonghap` | 두 사람 궁합 분석 |
| `POST` | `/api/sewoon` | 특정 연도 세운 상세 |
| `POST` | `/api/wolwoon` | 연도별 12절월 월운표 |
| `POST` | `/api/ilwoon` | 오늘·이번 주·이번 달 일진 |
| `POST` | `/api/timeline` | 대운·세운 통합 타임라인 |

### 기본 요청 예시 (`/api/saju`)

```json
{
  "calendar": "solar",
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 12,
  "minute": 0,
  "gender": "male",
  "lunar_leap": false
}
```

### 궁합 요청 예시 (`/api/goonghap`)

```json
{
  "person_a": {
    "calendar": "solar",
    "year": 1966, "month": 11, "day": 4,
    "hour": 2, "minute": 5,
    "gender": "female", "lunar_leap": false
  },
  "person_b": {
    "calendar": "solar",
    "year": 1963, "month": 3, "day": 15,
    "hour": 10, "minute": 0,
    "gender": "male", "lunar_leap": false
  },
  "name_a": "A",
  "name_b": "B"
}
```

---

## 패키지 구성

```
saju_project/
├── main.py                  # FastAPI 앱 진입점
├── saju/
│   ├── analysis.py          # 종합 분석 빌더
│   ├── goonghap.py          # 궁합 분석
│   ├── daewoon.py           # 대운
│   ├── sewoon.py            # 세운
│   ├── wolwoon.py           # 월운
│   ├── ilwoon.py            # 일운
│   ├── timeline.py          # 타임라인
│   ├── yongsin.py           # 용신·희신·기신
│   ├── ohaeng.py            # 오행 분포
│   ├── sinsal.py            # 신살
│   ├── sipsin.py            # 십신
│   ├── ganji.py             # 천간·지지 기본 데이터
│   └── saju_calc.py         # 원국 계산
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── tests/
│   └── test_*.py
├── requirements.txt
└── requirements-dev.txt
```

---

> 본 결과는 입문용 규칙 기반 참고 자료이며, 파종·월령·대운 해석 유파에 따라 달라질 수 있습니다.
