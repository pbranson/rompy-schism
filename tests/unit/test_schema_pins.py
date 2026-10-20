from typing import get_args

import pytest

from rompy_schism.schema import (
    DEFAULT_SCHISM_SCHEMA,
    SCHISM_MASTER_ALIAS,
    SCHISM_PINS,
    SchismSchemaVersion,
    resolve_schema,
    schema_index,
)


def test_literal_lists_every_pin_and_the_alias():
    assert set(get_args(SchismSchemaVersion)) == {*SCHISM_PINS, SCHISM_MASTER_ALIAS}


def test_master_alias_resolves_to_newest_pin():
    assert resolve_schema(SCHISM_MASTER_ALIAS) == list(SCHISM_PINS)[-1]


def test_master_is_dev_20261019():
    assert resolve_schema("schism-master") == "schism-dev-20261019"


def test_pins_are_ordered_from_the_permanent_default():
    assert next(iter(SCHISM_PINS)) == DEFAULT_SCHISM_SCHEMA
    assert schema_index("schism-v5.13") < schema_index("schism-dev-20250523")


@pytest.mark.parametrize("bad", ["schism-v5.14", "schism-v6.0"])
def test_unknown_schema_is_rejected(bad):
    with pytest.raises(ValueError, match="Unsupported SCHISM schema"):
        resolve_schema(bad)
