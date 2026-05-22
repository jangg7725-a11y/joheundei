# -*- coding: utf-8 -*-
"""매화역수(梅花易數) + 수리역학 9수 통합 엔진. 만세력(manseryeok) 확장 슬롯 포함."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from saju import calendar_conv as cc

_DATA_DIR = Path(__file__).resolve().parent / "data" / "maehwa"

# 오행: 1목 2토 3화 4금 5수 (trigrams.json ohaeng 필드)
_SHENG = ((1, 3), (3, 2), (2, 5), (5, 4), (4, 1))
_KE = ((1, 2), (3, 5), (2, 4), (5, 1), (4, 3))

_TIMING_HINTS = {
    1: "초기·봄·시작 단계. 서두르지 말고 기반을 다지는 시기.",
    2: "내실·초여름. 조용히 힘을 모으는 시기.",
    3: "전환·불안정. 하괘와 상괘의 경계 — 신중.",
    4: "중기·가을 전환. 방향 수정이 필요할 수 있음.",
    5: "정점·겨울 전. 주도권을 쥐기 좋은 때.",
    6: "말기·마무리. 변화의 씨앗이 다음 사이클로 넘어감.",
}


def _load_json(name: str) -> Any:
    return json.loads((_DATA_DIR / name).read_text(encoding="utf-8"))


def _mod8(n: int) -> int:
    r = n % 8
    return 8 if r == 0 else r


def _mod6(n: int) -> int:
    r = n % 6
    return 6 if r == 0 else r


def _year_digit_sum(year: int) -> int:
    return sum(int(c) for c in str(year))


def _hour_shi_index(hour: int) -> int:
    if hour >= 23 or hour < 1:
        return 1
    return (hour + 1) // 2 + 1


def _lines_to_gua(lines: list[int], gl: dict[int, list[int]]) -> int:
    for n in range(1, 9):
        g = gl[n]
        if g[0] == lines[0] and g[1] == lines[1] and g[2] == lines[2]:
            return n
    return 1


def _ti_yong_relation(che_o: int, yong_o: int) -> dict[str, str]:
    if che_o == yong_o:
        return {
            "label": "비화(比和)",
            "desc": "체와 용이 같은 오행입니다. 나와 외부가 균형을 이루며 조화로운 흐름입니다.",
        }
    if (che_o, yong_o) in _SHENG:
        return {
            "label": "체생용(體生用)",
            "desc": "내 기운이 외부로 흘러나갑니다. 에너지 소모가 있으니 내실을 챙기세요.",
        }
    if (yong_o, che_o) in _SHENG:
        return {
            "label": "용생체(用生體)",
            "desc": "외부에서 나를 돕는 구조입니다. 귀인·지원이 들어오기 쉽습니다.",
        }
    if (che_o, yong_o) in _KE:
        return {
            "label": "체극용(體剋用)",
            "desc": "내가 외부를 제어하는 구조입니다. 주도권을 쥐기 유리합니다.",
        }
    if (yong_o, che_o) in _KE:
        return {
            "label": "용극체(用剋體)",
            "desc": "외부가 나를 압박합니다. 신중한 대처와 내면 방어가 필요합니다.",
        }
    return {"label": "복합 관계", "desc": "오행이 복합적으로 작용합니다. 상황을 세밀히 살피세요."}


def _flip_line(lines: list[int], dong: int) -> list[int]:
    out = list(lines)
    if dong <= 3:
        out[dong - 1] = 1 - out[dong - 1]
    else:
        out[dong - 4] = 1 - out[dong - 4]
    return out


def _hex_lines(che: int, yong: int, gl: dict[int, list[int]]) -> list[dict[str, Any]]:
    lower = gl[che]
    upper = gl[yong]
    rows = []
    for i, v in enumerate(lower):
        rows.append({"index": i + 1, "yang": bool(v), "moving": False, "layer": "che"})
    for i, v in enumerate(upper):
        rows.append({"index": i + 4, "yang": bool(v), "moving": False, "layer": "yong"})
    return rows


def _apply_moving(rows: list[dict[str, Any]], dong: int) -> None:
    for r in rows:
        if r["index"] == dong:
            r["moving"] = True


def _mod9(n: int) -> int:
    r = n % 9
    return 9 if r == 0 else r


def calc_basic_suri(lunar_month: int, lunar_day: int) -> int:
    return _mod9(lunar_month + lunar_day + 1)


def calc_year_suri(base: int, birth_year: int, target_year: int) -> int:
    age = target_year - birth_year + 1
    age_sum = sum(int(c) for c in str(age))
    return _mod9(age_sum + base - 1)


def resolve_lunar_input(
    calendar: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lunar_leap: bool,
) -> dict[str, Any]:
    if calendar == "solar":
        solar = cc.SolarDateTime(year, month, day, hour, minute)
        lunar = cc.solar_to_lunar(solar)
    else:
        lunar = cc.LunarDateTime(year, month, day, hour, minute, lunar_leap)
        solar = cc.lunar_to_solar(lunar)
    return {
        "solar": {
            "year": solar.year,
            "month": solar.month,
            "day": solar.day,
            "hour": solar.hour,
            "minute": solar.minute,
            "label": cc.format_solar_string(solar),
        },
        "lunar": {
            "year": lunar.year,
            "month": lunar.month,
            "day": lunar.day,
            "hour": lunar.hour,
            "minute": lunar.minute,
            "is_leap_month": lunar.is_leap_month,
            "label": cc.format_lunar_string(lunar),
        },
    }


def build_reading(
    calendar: str,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "male",
    lunar_leap: bool = False,
    user_name: str = "",
) -> dict[str, Any]:
    """통합 매화역수 + 수리 해석 payload."""
    trigrams = _load_json("trigrams.json")
    gl_raw = _load_json("trigram_lines.json")
    gl = {int(k): v for k, v in gl_raw.items()}
    hex64 = _load_json("hex64.json")
    dong_db = {int(k): v for k, v in _load_json("dong_yao.json").items()}
    suri_db = {int(k): v for k, v in _load_json("suri.json").items()}
    imagery = {int(k): v for k, v in _load_json("imagery.json").items()}

    cal = resolve_lunar_input(calendar, year, month, day, hour, minute, lunar_leap)
    ly, lm, ld = cal["lunar"]["year"], cal["lunar"]["month"], cal["lunar"]["day"]
    lh = cal["lunar"]["hour"]

    yn = _year_digit_sum(ly)
    mn, dn = lm, ld
    hn = _hour_shi_index(lh)
    upper_sum = yn + mn + dn
    lower_sum = upper_sum + hn

    yong = _mod8(upper_sum)
    che = _mod8(lower_sum)
    dong = _mod6(lower_sum)

    hk = f"{yong}-{che}"
    hd = hex64.get(hk, {"name": "준비중", "hanja": "", "desc": ""})

    che_lines = list(gl[che])
    yong_lines = list(gl[yong])
    if dong <= 3:
        che_lines = _flip_line(che_lines, dong)
        changed_lower, changed_upper = _lines_to_gua(che_lines, gl), yong
    else:
        yong_lines = _flip_line(yong_lines, dong)
        changed_lower, changed_upper = che, _lines_to_gua(yong_lines, gl)

    ck = f"{changed_upper}-{changed_lower}"
    cd = hex64.get(ck, {"name": "변괘 준비중", "hanja": "", "desc": ""})

    rel = _ti_yong_relation(trigrams[str(che)]["ohaeng"], trigrams[str(yong)]["ohaeng"])
    ch_rel = _ti_yong_relation(
        trigrams[str(changed_lower)]["ohaeng"],
        trigrams[str(changed_upper)]["ohaeng"],
    )

    rows = _hex_lines(che, yong, gl)
    _apply_moving(rows, dong)
    dd = dong_db[dong]

    basic = calc_basic_suri(lm, ld)
    sd = suri_db.get(basic, {})

    cur_year = date.today().year
    year_rows = []
    for yr in range(cur_year - 2, cur_year + 6):
        ys = calc_year_suri(basic, ly, yr)
        year_rows.append(
            {
                "year": yr,
                "age": yr - ly + 1,
                "suri": ys,
                "kw": suri_db.get(ys, {}).get("kw", ""),
                "is_current": yr == cur_year,
            }
        )

    synthesis = (
        f"평생 {basic}수({sd.get('name', '')})의 기질 위에, "
        f"현재 본괘 {hd.get('name', '')}가 펼쳐지고 "
        f"동효 {dong}효를 지나 {cd.get('name', '')}로 흐름이 이어집니다. "
        f"체·용 관계는 {rel['label']}로, 외부와 내면의 균형을 이 관계로 읽으시면 됩니다."
    )

    return {
        "user_name": user_name or "의뢰인",
        "gender": gender,
        "calendar_input": calendar,
        "datetime": cal,
        "method_note": (
            "상괘=용(외부), 하괘=체(내면). "
            "상괘=(년+월+일) mod 8, 하괘=(년+월+일+시) mod 8, 동효=(년+월+일+시) mod 6."
        ),
        "gua_flow": {
            "ben": {
                "key": hk,
                "name": hd.get("name"),
                "hanja": hd.get("hanja"),
                "desc": hd.get("desc"),
                "upper": _trigram_payload(trigrams, imagery, yong, "용"),
                "lower": _trigram_payload(trigrams, imagery, che, "체"),
                "lines": rows,
                "ti_yong": rel,
            },
            "dong": {
                "index": dong,
                **dd,
                "timing": _TIMING_HINTS.get(dong, ""),
            },
            "zhi": {
                "key": ck,
                "name": cd.get("name"),
                "hanja": cd.get("hanja"),
                "desc": cd.get("desc"),
                "upper": _trigram_payload(trigrams, imagery, changed_upper, "변상"),
                "lower": _trigram_payload(trigrams, imagery, changed_lower, "변하"),
                "ti_yong": ch_rel,
            },
        },
        "suri": {
            "basic_num": basic,
            "name": sd.get("name"),
            "kw": sd.get("kw"),
            "tags": sd.get("tags", []),
            "char": sd.get("char"),
            "aspects": sd.get("aspects", []),
            "year_table": year_rows,
            "current_year_suri": calc_year_suri(basic, ly, cur_year),
        },
        "synthesis": synthesis,
        "manseryeok": {
            "status": "coming_soon",
            "label": "만세력",
            "message": "만세력(萬歲曆) 연동은 다음 단계에서 사주 원국·절기와 함께 제공됩니다.",
            "placeholder_tabs": ["절기", "월령", "일진", "시진"],
        },
    }


def _trigram_payload(
    trigrams: dict[str, Any],
    imagery: dict[int, Any],
    num: int,
    role: str,
) -> dict[str, Any]:
    t = trigrams[str(num)]
    img = imagery.get(num, {})
    return {
        "num": num,
        "role": role,
        "sym": t["sym"],
        "name": t["name"],
        "nat": t["nat"],
        "elemK": t["elemK"],
        "ohaeng": t["ohaeng"],
        "char": t["char"],
        "xiang": img.get("xiang", ""),
        "life": img.get("life", ""),
    }


def meta() -> dict[str, Any]:
    return {
        "title": "매화역수 · 수리역학",
        "subtitle": "梅花易數",
        "features": ["gua", "xiang", "shu", "dong", "tiyong", "timing", "suri", "manseryeok"],
        "manseryeok_status": "coming_soon",
    }
