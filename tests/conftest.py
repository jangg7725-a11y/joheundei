# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

from saju import saju_calc as sc


@pytest.fixture
def sample_birth() -> sc.BirthInput:
    return sc.BirthInput(
        calendar="solar",
        year=1990,
        month=5,
        day=15,
        hour=12,
        minute=0,
        gender="male",
        lunar_leap=False,
    )


@pytest.fixture
def raw_saju(sample_birth: sc.BirthInput):
    return sc.compute_saju(sample_birth)


@pytest.fixture
def sample_pillars(raw_saju):
    return raw_saju["pillars"]


@pytest.fixture
def day_master(raw_saju):
    return raw_saju["day_master"]


@pytest.fixture
def verification_birth():
    """검증용 사주: 음력 1966-11-04 02:05 여성
    예상 원국: 丙午 庚子 戊申 癸丑"""
    return sc.BirthInput(
        calendar="lunar",
        year=1966,
        month=11,
        day=4,
        hour=2,
        minute=5,
        gender="female",
        lunar_leap=False,
    )


@pytest.fixture
def verification_raw(verification_birth):
    return sc.compute_saju(verification_birth)


@pytest.fixture
def verification_pillars(verification_raw):
    return verification_raw["pillars"]
