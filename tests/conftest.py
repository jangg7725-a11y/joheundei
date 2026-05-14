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
