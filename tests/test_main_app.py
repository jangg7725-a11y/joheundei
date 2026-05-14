# -*- coding: utf-8 -*-
"""STEP 11–12: 정적 자산 및 FastAPI."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name",
    ["index.html", "style.css", "script.js"],
)
def test_step11_static_assets(name: str) -> None:
    assert (ROOT / "static" / name).is_file()


def test_step12_get_index_and_post_saju() -> None:
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    r = client.get("/")
    assert r.status_code == 200
    assert "四柱" in r.text or "사주" in r.text

    payload = {
        "calendar": "solar",
        "year": 1990,
        "month": 5,
        "day": 15,
        "hour": 12,
        "minute": 0,
        "gender": "male",
        "lunar_leap": False,
    }
    pr = client.post("/api/saju", json=payload)
    assert pr.status_code == 200
    data = pr.json()
    assert data.get("ok") is True
    assert data["result"]["day_master"]
    assert data["result"]["분석_카테고리"]


def test_step12_validation_error_shape() -> None:
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    pr = client.post("/api/saju", json={"calendar": "invalid"})
    assert pr.status_code == 422
    body = pr.json()
    assert body.get("ok") is False
    assert "detail" in body


def test_goonghap_api_ok() -> None:
    """POST /api/goonghap — 1966-11-04 여성 × 1963-03-15 남성 궁합 전체 검증."""
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)

    person_a = {
        "calendar": "solar",
        "year": 1966,
        "month": 11,
        "day": 4,
        "hour": 2,
        "minute": 5,
        "gender": "female",
        "lunar_leap": False,
    }
    person_b = {
        "calendar": "solar",
        "year": 1963,
        "month": 3,
        "day": 15,
        "hour": 10,
        "minute": 0,
        "gender": "male",
        "lunar_leap": False,
    }

    pr = client.post(
        "/api/goonghap",
        json={
            "person_a": person_a,
            "person_b": person_b,
            "name_a": "A여",
            "name_b": "B남",
        },
    )
    assert pr.status_code == 200, pr.text
    data = pr.json()
    assert data.get("ok") is True, f"ok 플래그 없음: {data}"

    res = data["result"]

    # ── 최상위 키 존재 여부 ─────────────────────────────────────────
    for key in ("기본_일지", "오행_궁합", "일간_궁합", "천간합", "용신_궁합",
                "종합_점수", "총평", "원국_나란히"):
        assert key in res, f"결과에 '{key}' 키가 없습니다"

    # ── 종합_점수 내 5개 영역 별점 존재 및 1~5 범위 ─────────────────
    score_block = res["종합_점수"]
    for domain in ("인연_강도", "갈등_가능성", "경제적_궁합", "성격_궁합", "전체_궁합"):
        assert domain in score_block, f"종합_점수에 '{domain}' 없음"
        star = score_block[domain]["별점"]
        assert 1 <= star <= 5, f"{domain} 별점({star})이 1~5 범위를 벗어남"

    # ── 하트 게이지 (0 초과~100 이하) ──────────────────────────────
    pct = score_block["하트_게이지_퍼센트"]
    assert 0 < pct <= 100, f"하트_게이지_퍼센트({pct})가 범위 밖"

    # ── 일지 관계 필드 ──────────────────────────────────────────────
    ilji = res["기본_일지"]
    for key in ("지지_A", "지지_B", "관계_표기", "커플_유형", "해설"):
        assert key in ilji, f"기본_일지에 '{key}' 없음"
    assert isinstance(ilji["관계_표기"], list), "관계_표기는 list여야 함"

    # ── 오행 궁합 필드 ──────────────────────────────────────────────
    ohaeng = res["오행_궁합"]
    for key in ("A_강함", "A_약함", "B_강함", "B_약함", "요약_문장"):
        assert key in ohaeng, f"오행_궁합에 '{key}' 없음"

    # ── 일간 궁합 필드 ──────────────────────────────────────────────
    ilgan = res["일간_궁합"]
    for key in ("유형", "해설"):
        assert key in ilgan, f"일간_궁합에 '{key}' 없음"

    # ── 천간합 여부 필드 ────────────────────────────────────────────
    cheon = res["천간합"]
    assert "성립" in cheon, "천간합에 '성립' 없음"
    assert isinstance(cheon["성립"], bool), "천간합.성립은 bool이어야 함"

    # ── 용신 궁합 필드 ──────────────────────────────────────────────
    yong = res["용신_궁합"]
    for side in ("A가_느끼는_상대", "B가_느끼는_상대"):
        assert side in yong, f"용신_궁합에 '{side}' 없음"
        assert yong[side]["등급"] in ("최상", "양호", "보통", "주의"), \
            f"{side}.등급 값이 예상 밖: {yong[side]['등급']}"

    # ── 궁합 총평 (비어 있지 않은 문자열) ─────────────────────────
    chonpyeong = res["총평"]
    assert isinstance(chonpyeong, str) and chonpyeong.strip(), "총평이 비어 있음"

    # ── 핵심한마디 — 커플 유형으로 대체 검증 ──────────────────────
    assert ilji["커플_유형"].strip(), "커플_유형(핵심한마디)이 비어 있음"

    # ── 원국 나란히 — 이름 확인 ────────────────────────────────────
    nara = res["원국_나란히"]
    assert nara["A"]["표시_이름"] == "A여"
    assert nara["B"]["표시_이름"] == "B남"
