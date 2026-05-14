# -*- coding: utf-8 -*-
"""
원국 사주(연월일시) 계산.

- 음력 입력은 ``calendar_conv``(lunar_python)으로 양력으로 환산합니다.
  한국천문연구원 공식 음력표와 완전 일치를 보장하지는 않으나,
  동일한 천문 알고리즘 계열을 사용하는 라이브러리 값에 근접합니다.

- 년주·월주: 입춘·節氣 시각은 lunar_python ``LunarYear`` 천문 테이블을 따릅니다.
  동일 출처로 생성한 ``jieqi_embedded`` 모듈에 1900~2100년 12절기 일시를 내장하여
  참조·검증용으로 노출합니다.

- 일주: **1900-01-01 = 甲戌日**를 기준으로 양력 연·월·일만 역산합니다.
  당일 23:00~23:59도 같은 양력 일자의 일주를 쓰고, 시지만 자시 등으로 둡니다.

- 시주: lunar_python 시지 규칙 + 시간 천간 ``(일간인덱스×2 + 시지인덱스) mod 10``.

대운 등 ``EightChar`` 연산과 일주 기준을 맞추기 위해, 위 일주·시주 확정 후
``Lunar`` 객체 내부 일간·시간 간지를 안전하게 덮어씁니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from lunar_python import Solar
from lunar_python.Lunar import Lunar

from . import calendar_conv as cc
from . import ganji as gj

try:
    from . import jieqi_embedded as _jieqi_emb
except ImportError:  # pragma: no cover
    _jieqi_emb = None  # type: ignore

ANCHOR_SOLAR_DATE = date(1900, 1, 1)
ANCHOR_JIAZI_INDEX = 10

DAY_INDICES_MAX_ABS_DELTA = 365242 * 2


@dataclass
class BirthInput:
    """calendar: ``solar``(양력 입력) 또는 ``lunar``(음력 입력).

    ya_jasi: 야자시(夜子時) 처리 여부.
      True = 23:00~23:59 출생을 다음 날 일주로 배속 (다수 학파 기준).
      False(기본) = 당일 일주 유지.
    """

    calendar: str
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    lunar_leap: bool = False
    gender: str = ""
    ya_jasi: bool = False  # 야자시 처리 여부


def _day_gan_zhi_indices(y: int, m: int, d: int) -> Tuple[int, int]:
    birth = date(y, m, d)
    delta = (birth - ANCHOR_SOLAR_DATE).days
    if abs(delta) > DAY_INDICES_MAX_ABS_DELTA:
        raise ValueError("지원 범위를 벗어난 양력 날짜입니다.")
    idx60 = (ANCHOR_JIAZI_INDEX + delta) % 60
    return idx60 % 10, idx60 % 12


def _patch_lunar_day_and_time(lunar: Lunar, *, ya_jasi: bool = False) -> None:
    """라이브러리 일주를 기준일 역산 결과로 맞추고 시주를 재계산합니다.

    ya_jasi=True이면 23시(夜子時)를 다음 날 일주로 배속합니다.
    """
    from datetime import date as _date, timedelta as _td
    solar = lunar.getSolar()
    y, m, d, h = solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour()
    if ya_jasi and h == 23:
        next_day = _date(y, m, d) + _td(days=1)
        y, m, d = next_day.year, next_day.month, next_day.day
    dg, dz = _day_gan_zhi_indices(y, m, d)
    object.__setattr__(lunar, "_Lunar__dayGanIndex", dg)
    object.__setattr__(lunar, "_Lunar__dayZhiIndex", dz)
    object.__setattr__(lunar, "_Lunar__dayGanIndexExact", dg)
    object.__setattr__(lunar, "_Lunar__dayZhiIndexExact", dz)
    object.__setattr__(lunar, "_Lunar__dayGanIndexExact2", dg)
    object.__setattr__(lunar, "_Lunar__dayZhiIndexExact2", dz)
    Lunar._Lunar__computeTime(lunar)
    object.__setattr__(lunar, "_Lunar__eightChar", None)


def _pillar_dict(gan: str, zhi: str) -> Dict[str, Any]:
    pillar = gan + zhi
    return {
        "gan": gan,
        "zhi": zhi,
        "pillar": pillar,
        "gan_kr": gj.STEM_KR[gj.stem_index(gan)],
        "zhi_kr": gj.BRANCH_KR[gj.branch_index(zhi)],
        "label_kr": gj.pillar_label_kr(gan, zhi),
        "stem_element": gj.element_of_stem(gan),
        "branch_element": gj.element_of_branch(zhi),
        "nayin": gj.nayin_for_pillar(pillar),
    }


def _pillars_from_lunar(lunar: Lunar) -> Dict[str, Dict[str, Any]]:
    return {
        "year": _pillar_dict(lunar.getYearGanExact(), lunar.getYearZhiExact()),
        "month": _pillar_dict(lunar.getMonthGanExact(), lunar.getMonthZhiExact()),
        "day": _pillar_dict(lunar.getDayGanExact(), lunar.getDayZhiExact()),
        "hour": _pillar_dict(lunar.getTimeGan(), lunar.getTimeZhi()),
    }


def _embedded_jieqi_row(calendar_year: int) -> Optional[List[Tuple[str, Tuple[int, int, int, int]]]]:
    if _jieqi_emb is None:
        return None
    row = _jieqi_emb.TERM_TWELVE_BY_YEAR.get(calendar_year)
    if row is None:
        return None
    names = _jieqi_emb.JIE_TWELVE_NAMES_KR
    return list(zip(names, row))


def compute_saju(birth: BirthInput, *, sect: int = 1) -> Dict[str, Any]:
    solar_dt = cc.resolve_calendar_input(
        birth.calendar,
        birth.year,
        birth.month,
        birth.day,
        birth.hour,
        birth.minute,
        birth.lunar_leap,
    )
    solar = Solar.fromYmdHms(
        solar_dt.year,
        solar_dt.month,
        solar_dt.day,
        solar_dt.hour,
        solar_dt.minute,
        0,
    )
    lunar = solar.getLunar()
    _patch_lunar_day_and_time(lunar, ya_jasi=birth.ya_jasi)

    ec = lunar.getEightChar()
    ec.setSect(sect)

    pillars = _pillars_from_lunar(lunar)
    day_master = pillars["day"]["gan"]
    lunar_conv = cc.solar_to_lunar(solar_dt)

    input_cal = birth.calendar.lower().strip()
    leap_flag = bool(lunar_conv.is_leap_month)

    result: Dict[str, Any] = {
        "calendar_input": birth.calendar,
        "gender": birth.gender,
        "solar": {
            "year": solar_dt.year,
            "month": solar_dt.month,
            "day": solar_dt.day,
            "hour": solar_dt.hour,
            "minute": solar_dt.minute,
            "label": cc.format_solar_string(solar_dt),
        },
        "lunar": {
            "year": lunar_conv.year,
            "month": lunar_conv.month,
            "day": lunar_conv.day,
            "hour": lunar_conv.hour,
            "minute": lunar_conv.minute,
            "is_leap_month": leap_flag,
            "label": cc.format_lunar_string(lunar_conv),
        },
        "is_leap_month": leap_flag,
        "pillars": pillars,
        "day_master": day_master,
        "day_master_kr": gj.STEM_KR[gj.stem_index(day_master)],
        "day_master_element": gj.element_of_stem(day_master),
        "eight_char_string": ec.toString(),
        "day_anchor_note": (
            "일주 기준: 1900-01-01=甲戌, 양력 일자 기준."
            + (" ⚡야자시(23시) → 다음 날 일주 적용." if birth.ya_jasi else " (야자시 미적용: 23시도 당일 일주)")
        ),
        "ya_jasi_applied": birth.ya_jasi,
        "jieqi_embedded_year": _embedded_jieqi_row(solar_dt.year),
        "_eight_char": ec,
    }

    if input_cal in ("lunar", "음력"):
        result["lunar_input_used_leap_month_field"] = birth.lunar_leap

    return result


def serialize_saju_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """JSON 응답용: 비직렬화 객체 제거."""
    return {k: v for k, v in raw.items() if k != "_eight_char"}
