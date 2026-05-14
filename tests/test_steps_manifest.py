# -*- coding: utf-8 -*-
"""
STEP 1–12 세팅 순서 대비 산출물 경로 검증.

STEP 1  폴더/구조
STEP 2  기본 데이터 (천간지지·지장간·오행·절기 내장)
STEP 3  원국 계산
STEP 4  십신
STEP 5  충파해합형
STEP 6  대운·세운
STEP 7  용신
STEP 8  신살
STEP 9  십이운성
STEP 10 종합분석
STEP 11 웹 UI
STEP 12 서버(main)
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "step,paths",
    [
        (
            1,
            [
                ROOT / "saju",
                ROOT / "saju" / "__init__.py",
                ROOT / "static",
                ROOT / "main.py",
                ROOT / "requirements.txt",
            ],
        ),
        (
            2,
            [
                ROOT / "saju" / "ganji.py",
                ROOT / "saju" / "jijanggan.py",
                ROOT / "saju" / "ohaeng.py",
                ROOT / "saju" / "jieqi_embedded.py",
            ],
        ),
        (
            3,
            [
                ROOT / "saju" / "saju_calc.py",
                ROOT / "saju" / "calendar_conv.py",
            ],
        ),
        (4, [ROOT / "saju" / "sipsin.py"]),
        (5, [ROOT / "saju" / "chung_pa_hae.py"]),
        (6, [ROOT / "saju" / "daewoon.py", ROOT / "saju" / "sewoon.py"]),
        (7, [ROOT / "saju" / "yongsin.py"]),
        (8, [ROOT / "saju" / "sinsal.py"]),
        (9, [ROOT / "saju" / "sibiunsung.py"]),
        (10, [ROOT / "saju" / "analysis.py"]),
        (
            11,
            [
                ROOT / "static" / "index.html",
                ROOT / "static" / "style.css",
                ROOT / "static" / "script.js",
            ],
        ),
        (12, [ROOT / "main.py"]),
    ],
)
def test_step_files_exist(step: int, paths: list[Path]) -> None:
    missing = [p for p in paths if not p.exists()]
    assert not missing, f"STEP {step} 경로 누락: {missing}"
