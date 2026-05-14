# -*- coding: utf-8 -*-
"""양력·음력 상호 변환 (lunar_python 기반).

한국천문연구원 공식 음력 데이터와 날짜가 어긋날 수 있으니 행정·법적 용도에는 공식 데이터를 확인하세요.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lunar_python import Lunar, Solar


@dataclass
class SolarDateTime:
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0


@dataclass
class LunarDateTime:
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    is_leap_month: bool = False


def lunar_month_param(month: int, is_leap_month: bool) -> int:
    """음력 윤달은 lunar_python 규약상 월을 음수로 둡니다."""
    if is_leap_month and month > 0:
        return -month
    return month


def solar_to_lunar(dt: SolarDateTime) -> LunarDateTime:
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
    lunar = solar.getLunar()
    m = lunar.getMonth()
    return LunarDateTime(
        year=lunar.getYear(),
        month=abs(m),
        day=lunar.getDay(),
        hour=lunar.getHour(),
        minute=lunar.getMinute(),
        is_leap_month=m < 0,
    )


def lunar_to_solar(lt: LunarDateTime) -> SolarDateTime:
    m = lunar_month_param(lt.month, lt.is_leap_month)
    lunar = Lunar.fromYmdHms(lt.year, m, lt.day, lt.hour, lt.minute, 0)
    solar = lunar.getSolar()
    return SolarDateTime(
        year=solar.getYear(),
        month=solar.getMonth(),
        day=solar.getDay(),
        hour=solar.getHour(),
        minute=solar.getMinute(),
    )


def format_lunar_string(lt: LunarDateTime) -> str:
    leap = " 윤" if lt.is_leap_month else " "
    return f"음력 {lt.year}년{leap}{lt.month}월 {lt.day}일 {lt.hour:02d}:{lt.minute:02d}"


def format_solar_string(dt: SolarDateTime) -> str:
    return f"양력 {dt.year}년 {dt.month}월 {dt.day}일 {dt.hour:02d}:{dt.minute:02d}"


def solar_from_parts(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
) -> SolarDateTime:
    return SolarDateTime(year=year, month=month, day=day, hour=hour, minute=minute)


def lunar_from_parts(
    year: int,
    month: int,
    day: int,
    *,
    hour: int = 12,
    minute: int = 0,
    is_leap_month: bool = False,
) -> LunarDateTime:
    return LunarDateTime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        is_leap_month=is_leap_month,
    )


def resolve_calendar_input(
    calendar: str,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    lunar_leap: bool = False,
) -> SolarDateTime:
    """calendar가 lunar이면 양력으로 환산합니다."""
    cal = calendar.lower().strip()
    if cal == "solar" or cal == "양력":
        return solar_from_parts(year, month, day, hour, minute)
    if cal == "lunar" or cal == "음력":
        lt = lunar_from_parts(year, month, day, hour=hour, minute=minute, is_leap_month=lunar_leap)
        return lunar_to_solar(lt)
    raise ValueError("calendar는 'solar' 또는 'lunar' 여야 합니다.")
