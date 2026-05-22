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


def _honorific(name: str, gender: str) -> str:
    n = (name or "").strip() or "의뢰인"
    if gender == "female":
        return f"{n}님"
    if gender == "male":
        return f"{n}님"
    return f"{n}님"


def _ti_yong_story(rel: dict[str, str], phase: str) -> str:
    """체·용 관계를 스토리 문장으로."""
    label = rel.get("label", "")
    if "비화" in label:
        return (
            f"{phase}에서는 나와 환경이 같은 결을 맞추려는 흐름입니다. "
            "무리한 대립보다 리듬을 맞추면 일이 자연스럽게 풀립니다."
        )
    if "체생용" in label:
        return (
            f"{phase}에서는 내 기운이 밖으로 흘러나가기 쉽습니다. "
            "베풂과 성과 사이에서 에너지 관리가 관건입니다."
        )
    if "용생체" in label:
        return (
            f"{phase}에서는 밖에서 들어오는 도움과 기회가 나를 살립니다. "
            "받아들이는 태도가 곧 운을 키웁니다."
        )
    if "체극용" in label:
        return (
            f"{phase}에서는 내가 상황을 이끌기 유리합니다. "
            "주도권을 쥐되, 상대의면도 남겨 두면 관계가 오래갑니다."
        )
    if "용극체" in label:
        return (
            f"{phase}에서는 외부 압력이나 시기가 나를 먼저 흔듭니다. "
            "억지로 맞서기보다 방어와 조율로 버티는 것이 현명합니다."
        )
    return f"{phase}에서는 {rel.get('desc', '체와 용이 서로 다른 방향으로 작용합니다.')}"


def _suri_aspect_line(suri_db: dict[int, Any], num: int, label: str = "종합운") -> str:
    aspects = suri_db.get(num, {}).get("aspects") or []
    for a in aspects:
        if a.get("label") == label:
            return a.get("text", "")
    return aspects[0].get("text", "") if aspects else ""


def build_synthesis_story(
    *,
    user_name: str,
    gender: str,
    cal: dict[str, Any],
    suri_db: dict[int, Any],
    basic: int,
    sd: dict[str, Any],
    cur_year: int,
    cur_suri: int,
    cur_sd: dict[str, Any],
    hd: dict[str, str],
    cd: dict[str, str],
    ben_upper: dict[str, Any],
    ben_lower: dict[str, Any],
    rel: dict[str, str],
    ch_rel: dict[str, str],
    dong: dict[str, Any],
    dong_idx: int,
) -> dict[str, Any]:
    """통합 요약 — 평생 수리·본괘·동효·之卦·올해를 한 이야기로 엮는다."""
    who = _honorific(user_name, gender)
    lunar_lbl = cal["lunar"]["label"]
    basic_name = sd.get("name", "")
    basic_kw = sd.get("kw", "")
    basic_char = sd.get("char", "")
    cur_name = cur_sd.get("name", "")
    cur_kw = cur_sd.get("kw", "")

    ben_name = hd.get("name", "")
    ben_hanja = hd.get("hanja", "")
    ben_desc = hd.get("desc", "")
    zhi_name = cd.get("name", "")
    zhi_hanja = cd.get("hanja", "")
    zhi_desc = cd.get("desc", "")

    headline = (
        f"평생 {basic}수의 바탕 위에 「{ben_name}」이 펼쳐지고, "
        f"{dong_idx}효를 지나 「{zhi_name}」으로 흐름이 이어집니다."
    )

    opening = (
        f"{who}의 매화역수·수리 통합 이야기입니다. "
        f"음력 {lunar_lbl}에 맞춰 본괘와 수리가 함께 말을 건넵니다. "
        f"아래 네 장면—평생의 바탕, 지금의 장면, 변화의 씨앗, 흐름이 향하는 곳—을 "
        f"한 호흡으로 읽으시면 전체 그림이 선명해집니다."
    )

    foundation = (
        f"먼저 평생의 바탕입니다. {who}에게는 **{basic}수 · {basic_name}**이 "
        f"타고난 리듬으로 자리합니다. 키워드는 「{basic_kw}」입니다. "
        f"{basic_char} "
        f"이 수리는 인생 전반의 ‘기본 음’이므로, 아래 괘의 흐름도 이 결을 "
        f"끝까지 잃지 않고 이어집니다."
    )

    present = (
        f"지금 펼쳐진 장면은 **본괘 {ben_name}({ben_hanja})**입니다. "
        f"하괘 체(내면)는 {ben_lower.get('name', '')}괘({ben_lower.get('nat', '')}) — "
        f"{ben_lower.get('xiang') or ben_lower.get('char', '')}. "
        f"상괘 용(외부)은 {ben_upper.get('name', '')}괘({ben_upper.get('nat', '')}) — "
        f"{ben_upper.get('xiang') or ben_upper.get('char', '')}. "
        f"{ben_desc} "
        f"{_ti_yong_story(rel, '본괘의 체·용(體用)')}"
    )

    turning = (
        f"이야기의 전환점은 **{dong_idx}효 · {dong.get('name', '')}**입니다. "
        f"{dong.get('pos', '')}. "
        f"{dong.get('desc', '')} "
        f"시기상으로는 {dong.get('timing', '')} "
        f"지금 겪는 변화나 고민의 ‘핵심 관문’이 여기에 놓여 있다고 보시면 됩니다."
    )

    future = (
        f"동효가 가리키는 다음 장면은 **之卦 {zhi_name}({zhi_hanja})**입니다. "
        f"{zhi_desc} "
        f"변화 후 체·용은 {ch_rel.get('label', '')} — "
        f"{_ti_yong_story(ch_rel, '之卦의 체·용')} "
        f"본괘에서 멈추지 말고, 이 결으로 흐름이 어디로 기울는지 함께 두시면 좋습니다."
    )

    year_line = _suri_aspect_line(suri_db, cur_suri)
    if not year_line:
        year_line = cur_sd.get("char", "")

    year_chapter = (
        f"**{cur_year}년(올해)**의 수리 흐름은 평생 {basic}수에서 **{cur_suri}수 · {cur_name}**"
        f"({cur_kw})로 맞춰집니다. "
        f"{year_line} "
        f"올해는 괘의 이야기와 맞물려, "
        f"「{ben_name} → {dong_idx}효 → {zhi_name}」의 호흡 속에서 "
        f"위 {cur_suri}수의 기운이 실제 선택과 만남으로 드러납니다."
    )

    closing = (
        f"정리하면, {who}의 길은 **평생 {basic}수**라는 뿌리에서 출발해 "
        f"**{ben_name}**의 장면을 거쳐 **{dong_idx}효**에서 방향을 바꾸고 "
        f"**{zhi_name}**으로 기울어 갑니다. "
        f"본괘 체·용({rel.get('label', '')})과 之卦({ch_rel.get('label', '')})를 "
        f"한 쌍으로 보면, ‘지금 버틸 것’과 ‘앞으로 맞출 것’이 분명해집니다. "
        f"올해는 {cur_suri}수의 결을 의식하며, 동효가 가리킨 지점—"
        f"{dong.get('name', '')}—에 작은 실천을 두시면 이야기가 살아납니다."
    )

    sections = [
        {"id": "foundation", "icon": "🌱", "title": "1장 · 평생의 바탕", "text": foundation},
        {"id": "present", "icon": "☯", "title": "2장 · 지금 펼쳐진 본괘", "text": present},
        {"id": "turning", "icon": "✦", "title": "3장 · 변화의 씨앗 (동효)", "text": turning},
        {"id": "future", "icon": "→", "title": "4장 · 흐름이 향하는 之卦", "text": future},
        {"id": "year", "icon": "📅", "title": f"5장 · {cur_year}년의 결", "text": year_chapter},
    ]

    full_text = "\n\n".join(
        [headline, opening]
        + [f"【{s['title']}】\n{s['text']}" for s in sections]
        + [f"【마무리】\n{closing}"]
    )

    return {
        "headline": headline,
        "opening": opening,
        "sections": sections,
        "closing": closing,
        "narrative": full_text,
    }


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

    cur_suri = calc_year_suri(basic, ly, cur_year)
    cur_sd = suri_db.get(cur_suri, {})

    story = build_synthesis_story(
        user_name=user_name or "의뢰인",
        gender=gender,
        cal=cal,
        suri_db=suri_db,
        basic=basic,
        sd=sd,
        cur_year=cur_year,
        cur_suri=cur_suri,
        cur_sd=cur_sd,
        hd=hd,
        cd=cd,
        ben_upper=_trigram_payload(trigrams, imagery, yong, "용"),
        ben_lower=_trigram_payload(trigrams, imagery, che, "체"),
        rel=rel,
        ch_rel=ch_rel,
        dong={**dd, "index": dong, "timing": _TIMING_HINTS.get(dong, "")},
        dong_idx=dong,
    )
    synthesis = story["headline"]

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
            "current_year_suri": cur_suri,
            "current_year_name": cur_sd.get("name"),
            "current_year_kw": cur_sd.get("kw"),
        },
        "synthesis": synthesis,
        "synthesis_story": story,
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
