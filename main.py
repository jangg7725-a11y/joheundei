# -*- coding: utf-8 -*-
"""
사주 팔자 FastAPI 서버.

실행 예시:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

브라우저: http://127.0.0.1:8000/
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from saju import ai_interpreter as ai
from saju import analysis
from saju import daewoon as dw
from saju import goonghap as gh
from saju import ilwoon as il
from saju import ohaeng as oh
from saju import saju_calc as sc
from saju import sewoon as sw
from saju import timeline as tl
from saju import wolwoon as ww
from saju import yongsin as ys

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class NativeChartRequest(BaseModel):
    """사주 원국만 (생년월일시·음양력·성별)."""

    calendar: str = Field(description="양력 solar | 음력 lunar")
    year: int = Field(ge=1800, le=2100, description="생년")
    month: int = Field(ge=1, le=12, description="생월")
    day: int = Field(ge=1, le=31, description="생일")
    hour: int = Field(default=12, ge=0, le=23, description="생시")
    minute: int = Field(default=0, ge=0, le=59, description="생분")
    gender: str = Field(description="남/여 또는 male/female")
    lunar_leap: bool = Field(default=False, description="음력 윤달 여부")
    ya_jasi: bool = Field(default=False, description="야자시(夜子時) 처리: 23시 출생을 다음 날 일주로 배속")

    @field_validator("calendar", mode="before")
    @classmethod
    def normalize_calendar(cls, v: Any) -> str:
        if v is None:
            raise ValueError("calendar는 필수입니다.")
        s = str(v).strip().lower()
        if s in ("solar", "s", "양력", "양"):
            return "solar"
        if s in ("lunar", "l", "음력", "음"):
            return "lunar"
        raise ValueError("calendar는 양력(solar) 또는 음력(lunar)이어야 합니다.")

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v: Any) -> str:
        if v is None:
            raise ValueError("gender는 필수입니다.")
        s = str(v).strip().lower()
        if s in ("male", "m", "남", "남성", "남자"):
            return "male"
        if s in ("female", "f", "여", "여성", "여자"):
            return "female"
        raise ValueError("gender는 남성(male/남) 또는 여성(female/여)이어야 합니다.")

    @model_validator(mode="after")
    def validate_solar_date_when_applicable(self) -> NativeChartRequest:
        if self.calendar == "solar":
            try:
                date(self.year, self.month, self.day)
            except ValueError:
                raise ValueError("양력 생년월일이 달력상 존재하지 않습니다.") from None
        return self


class SewoonYearRequest(NativeChartRequest):
    query_year: int = Field(ge=1800, le=2100, description="조회할 세운 연도(양력)")


class WolwoonYearRequest(NativeChartRequest):
    solar_year: int = Field(ge=1800, le=2100, description="월운표 기준 세운 연도")


class IlwoonChartRequest(NativeChartRequest):
    reference_date: date | None = Field(
        default=None,
        description="일운 기준일(미입력 시 서버 오늘 날짜)",
    )


class TimelineChartRequest(NativeChartRequest):
    current_year: int | None = Field(
        default=None,
        ge=1800,
        le=2100,
        description="타임라인 기준 연도(미입력 시 올해)",
    )


class GoonghapRequest(BaseModel):
    """두 사람 생년월일시로 궁합 패키지."""

    person_a: NativeChartRequest
    person_b: NativeChartRequest
    name_a: str | None = Field(default=None, description="첫 번째 사람 표시 이름")
    name_b: str | None = Field(default=None, description="두 번째 사람 표시 이름")
    current_year: int | None = Field(
        default=None, ge=1800, le=2100,
        description="세운 궁합 기준 연도 (미입력 시 올해)",
    )


def _compute_native(chart: NativeChartRequest) -> tuple[Any, Any, str, str, dict[str, Any]]:
    """(raw, eight_char, day_master, gender_str, counts)"""
    birth = sc.BirthInput(
        calendar=chart.calendar,
        year=chart.year,
        month=chart.month,
        day=chart.day,
        hour=chart.hour,
        minute=chart.minute,
        lunar_leap=chart.lunar_leap,
        gender=chart.gender,
        ya_jasi=chart.ya_jasi,
    )
    raw = sc.compute_saju(birth)
    ec = raw["_eight_char"]
    pillars = raw["pillars"]
    dm = raw["day_master"]
    counts = oh.count_elements(pillars, include_hidden=True)
    return raw, ec, dm, chart.gender, counts


class SajuRequest(BaseModel):
    """사주 전체 분석 요청 본문."""

    calendar: str = Field(description="양력 solar | 음력 lunar")
    year: int = Field(ge=1800, le=2100, description="연도")
    month: int = Field(ge=1, le=12, description="월")
    day: int = Field(ge=1, le=31, description="일")
    hour: int = Field(default=12, ge=0, le=23, description="시")
    minute: int = Field(default=0, ge=0, le=59, description="분")
    gender: str = Field(description="남/여 또는 male/female")
    lunar_leap: bool = Field(default=False, description="음력 윤달 여부")
    ya_jasi: bool = Field(default=False, description="야자시(夜子時) 처리: 23시 출생을 다음 날 일주로 배속")
    sewoon_center_year: int | None = Field(default=None, ge=1800, le=2100, description="세운 기준 연도")
    wolwoon_center_year: int | None = Field(
        default=None,
        ge=1800,
        le=2100,
        description="월운표 기준 세운 연도(미입력 시 양력 현재 연도)",
    )
    partner_day_pillar: str | None = Field(
        default=None,
        description="궁합용 상대 일주 두 글자 간지(예: 庚子)",
    )

    @field_validator("calendar", mode="before")
    @classmethod
    def normalize_calendar(cls, v: Any) -> str:
        if v is None:
            raise ValueError("calendar는 필수입니다.")
        s = str(v).strip().lower()
        if s in ("solar", "s", "양력", "양"):
            return "solar"
        if s in ("lunar", "l", "음력", "음"):
            return "lunar"
        raise ValueError("calendar는 양력(solar) 또는 음력(lunar)이어야 합니다.")

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v: Any) -> str:
        if v is None:
            raise ValueError("gender는 필수입니다.")
        s = str(v).strip().lower()
        if s in ("male", "m", "남", "남성", "남자"):
            return "male"
        if s in ("female", "f", "여", "여성", "여자"):
            return "female"
        raise ValueError("gender는 남성(male/남) 또는 여성(female/여)이어야 합니다.")

    @field_validator("partner_day_pillar", mode="before")
    @classmethod
    def normalize_partner_pillar(cls, v: Any) -> str | None:
        if v is None:
            return None
        t = str(v).strip()
        if not t:
            return None
        if len(t) != 2:
            raise ValueError("partner_day_pillar는 한글 간지 두 글자(예: 庚子)여야 합니다.")
        return t

    @model_validator(mode="after")
    def validate_solar_date_when_applicable(self) -> SajuRequest:
        if self.calendar == "solar":
            try:
                date(self.year, self.month, self.day)
            except ValueError:
                raise ValueError("양력 생년월일이 달력상 존재하지 않습니다.") from None
        return self


app = FastAPI(
    title="사주 분석 API",
    version="1.0.0",
    description="四柱八字 계산 및 종합 분석",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_request: Any, exc: RequestValidationError) -> JSONResponse:
    errors = jsonable_encoder(exc.errors())
    messages = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        msg = err.get("msg", "")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": "validation_error",
            "detail": errors,
            "message": "; ".join(messages) if messages else "입력값을 확인하세요.",
        },
    )


def _run_saju(req: SajuRequest) -> dict[str, Any]:
    return analysis.build_report(
        calendar=req.calendar,
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        minute=req.minute,
        gender=req.gender,
        lunar_leap=req.lunar_leap,
        ya_jasi=req.ya_jasi,
        sewoon_center_year=req.sewoon_center_year,
        wolwoon_center_year=req.wolwoon_center_year,
        partner_day_pillar=req.partner_day_pillar,
    )


@app.get("/")
async def index_page() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=500, detail="static/index.html 파일이 없습니다.")
    return FileResponse(index_file)


@app.post("/api/saju")
async def api_saju(req: SajuRequest) -> dict[str, Any]:
    """
    사주 전체 계산: 원국·오행·십신·합충·용신·대운·세운·신살·종합 분석 등.
    """
    try:
        report = _run_saju(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 계산 오류: {e}") from e
    return {"ok": True, "result": report}


@app.post("/api/analyze")
async def api_analyze_legacy(req: SajuRequest) -> dict[str, Any]:
    """하위 호환: 예전 클라이언트용. 동작은 ``/api/saju``와 동일합니다."""
    return await api_saju(req)


@app.post("/api/sewoon")
async def api_sewoon(req: SewoonYearRequest) -> dict[str, Any]:
    """사주 원국 + 조회 연도 → 해당 연도 세운 상세 분석(정밀분석 포함)."""
    try:
        raw, _ec, dm, gender, counts = _compute_native(req)
        pillars = raw["pillars"]
        row = sw.analyze_sewoon_year(dm, pillars, gender, req.query_year, counts=counts)
        row["정밀분석"] = analysis._precision_pack_sewoon_only(dm, pillars, row["천간"], row["지지"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 계산 오류: {e}") from e
    return {"ok": True, "result": row}


@app.post("/api/wolwoon")
async def api_wolwoon(req: WolwoonYearRequest) -> dict[str, Any]:
    """사주 원국 + 세운 연도 → 12절월 월운표 전체(정밀분석 포함)."""
    try:
        raw, _ec, dm, gender, counts = _compute_native(req)
        pillars = raw["pillars"]
        pack = ww.wolwoon_year_pack(dm, pillars, req.solar_year, gender=gender, counts=counts)
        analysis._enrich_wolwoon_pack(pack, dm, pillars)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 계산 오류: {e}") from e
    return {"ok": True, "result": pack}


@app.post("/api/ilwoon")
async def api_ilwoon(req: IlwoonChartRequest) -> dict[str, Any]:
    """사주 원국 + 기준일(미입력 시 오늘) → 오늘 일진·이번 주·이번 달 달력."""
    try:
        raw, _ec, dm, _gender, _counts = _compute_native(req)
        pillars = raw["pillars"]
        ref = req.reference_date if req.reference_date is not None else date.today()
        snap = il.ilwoon_snapshot_pack(dm, pillars, reference_date=ref)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 계산 오류: {e}") from e
    return {"ok": True, "result": snap}


@app.post("/api/timeline")
async def api_timeline(req: TimelineChartRequest) -> dict[str, Any]:
    """사주 원국 → 대운·세운·월운 통합 타임라인."""
    try:
        raw, ec, dm, gender, counts = _compute_native(req)
        pillars = raw["pillars"]
        gender_male = gender == "male"
        daewoon_block = dw.compute_daewoon(ec, gender_male)
        yong_block = ys.suggest_useful_gods(counts, dm, pillars["month"]["zhi"], pillars=pillars)
        cy = req.current_year if req.current_year is not None else datetime.now().year
        pack = tl.build_timeline_pack(
            dm,
            pillars,
            gender,
            counts,
            birth_year=req.year,
            daewoon_cycles=daewoon_block["cycles"],
            yong_block=yong_block,
            current_year=cy,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 계산 오류: {e}") from e
    return {"ok": True, "result": pack}


@app.post("/api/goonghap")
async def api_goonghap(req: GoonghapRequest) -> dict[str, Any]:
    """두 명 원국 → 일지·오행·일간·천간합·용신 기반 궁합 요약."""
    try:
        raw_a, _ec_a, dm_a, _gender_a, counts_a = _compute_native(req.person_a)
        raw_b, _ec_b, dm_b, _gender_b, counts_b = _compute_native(req.person_b)
        pillars_a = raw_a["pillars"]
        pillars_b = raw_b["pillars"]
        yong_a = ys.suggest_useful_gods(counts_a, dm_a, pillars_a["month"]["zhi"], pillars=pillars_a)
        yong_b = ys.suggest_useful_gods(counts_b, dm_b, pillars_b["month"]["zhi"], pillars=pillars_b)
        na = (req.name_a or "").strip() or "A"
        nb = (req.name_b or "").strip() or "B"
        cy = req.current_year if req.current_year is not None else datetime.now().year
        pack = gh.analyze_goonghap_pair(
            raw_a=raw_a,
            raw_b=raw_b,
            counts_a=counts_a,
            counts_b=counts_b,
            yong_a=yong_a,
            yong_b=yong_b,
            label_a=na,
            label_b=nb,
            gender_a=req.person_a.gender,
            gender_b=req.person_b.gender,
            current_year=cy,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 계산 오류: {e}") from e
    return {"ok": True, "result": pack}


class AiInterpretRequest(BaseModel):
    """AI 맞춤 스토리텔링 해설 요청."""

    tab: str = Field(description="wonkuk|hapchung|yongsin|daewoon|jonghap|sinsal 또는 0~5")
    saju_data: dict[str, Any] = Field(description="build_report 결과 전체")
    user_name: str | None = Field(default=None, description="표시 이름")
    force_refresh: bool = Field(default=False, description="캐시 무시 재생성")
    tier: str = Field(default="free", description="free | premium")


@app.post("/api/ai/interpret")
async def api_ai_interpret(
    req: AiInterpretRequest,
    x_saju_tier: str | None = Header(default=None, alias="X-Saju-Tier"),
) -> dict[str, Any]:
    """탭별 AI 맞춤 해설 (JSON)."""
    tier = (x_saju_tier or req.tier or "free").strip().lower()
    try:
        result = ai.interpret_tab(
            req.tab,
            req.saju_data,
            user_name=req.user_name,
            force_refresh=req.force_refresh,
            tier=tier,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 해설 오류: {e}") from e
    return {"ok": bool(result.get("ok")), "result": result}


@app.post("/api/ai/interpret/stream")
async def api_ai_interpret_stream(
    req: AiInterpretRequest,
    x_saju_tier: str | None = Header(default=None, alias="X-Saju-Tier"),
) -> StreamingResponse:
    """탭별 AI 해설 SSE 스트리밍."""
    tier = (x_saju_tier or req.tier or "free").strip().lower()

    def event_gen() -> Iterator[str]:
        try:
            for ev in ai.stream_interpret_tab(
                req.tab,
                req.saju_data,
                user_name=req.user_name,
                force_refresh=req.force_refresh,
                tier=tier,
            ):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        except RuntimeError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'AI 오류: {e}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/ai/config")
async def api_ai_config() -> dict[str, Any]:
    """클라이언트용 AI 설정."""
    import os

    provider = ai.active_provider()
    return {
        "ok": True,
        "enabled": provider is not None,
        "provider": provider or "",
        "model": ai.active_model_name(),
        "free_daily_limit": int(os.getenv("SAJU_AI_FREE_DAILY", "6")),
    }


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
