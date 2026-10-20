"""Frozen SCHISM schemas must keep rendering exactly what they always rendered."""

from pathlib import Path

import pytest

from rompy_schism.namelists.param import Param

GOLDEN = Path(__file__).parents[1] / "schema_fixtures" / "golden"

V513_CUSTOM = {"opt": {"isconsv": 0, "veg_lai": 3, "vclose_surf_frac": 0.5}}
DEV_CUSTOM = {
    "core": {"nmarsh_types": 3},
    "opt": {"veg_lai": 3, "vclose_surf_frac": 0.5},
}

GOLDEN_CASES = [
    ("param-v5.13-default", "schism-v5.13", {}),
    ("param-v5.13-custom", "schism-v5.13", V513_CUSTOM),
    ("param-dev-20250523-default", "schism-dev-20250523", {}),
    ("param-dev-20250523-custom", "schism-dev-20250523", DEV_CUSTOM),
]


@pytest.mark.parametrize(("stem", "schema_version", "kwargs"), GOLDEN_CASES)
def test_frozen_schema_render_is_byte_identical(stem, schema_version, kwargs):
    expected = (GOLDEN / f"{stem}.nml").read_text()
    assert Param(**kwargs).render(schema_version) == expected
