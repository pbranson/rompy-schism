import pytest
from pydantic import ValidationError

from rompy_schism.namelists.lifecycle import LIFECYCLE
from rompy_schism.namelists.param import Opt, Param
from rompy_schism.schema import SCHISM_PINS


def test_every_row_names_a_real_model_field_and_pins():
    for row in LIFECYCLE:
        model = type(getattr(Param(), row.group))
        assert row.name in model.model_fields, row
        assert model.model_fields[row.name].default is None, row
        for pin in (row.added, row.removed):
            assert pin is None or pin in SCHISM_PINS, row


def test_dev_only_name_rejected_on_v513_with_pin_in_message():
    with pytest.raises(ValueError, match="nmarsh_types.*added in schism-dev-20250523"):
        Param(core={"nmarsh_types": 2}).validate_schema("schism-v5.13")


def test_retired_name_rejected_with_hint():
    with pytest.raises(
        ValueError, match="isconsv.*removed in schism-dev-20250523.*PREC_EVAP"
    ):
        Param(opt={"isconsv": 0}).validate_schema("schism-dev-20250523")


def test_fill_applies_only_where_declared():
    v513 = Param().resolved_dump("schism-v5.13")
    dev = Param().resolved_dump("schism-dev-20250523")
    assert v513["opt"]["isconsv"] == 0 and "nmarsh_types" not in v513["core"]
    assert dev["core"]["nmarsh_types"] == 2 and "isconsv" not in dev["opt"]


@pytest.mark.parametrize("name", ["veg_lai", "vclose_surf_frac"])
def test_validators_accept_none(name):
    assert getattr(Opt(**{name: None}), name) is None


def test_vclose_surf_frac_range_still_checked():
    with pytest.raises(ValidationError):
        Opt(vclose_surf_frac=1.5)
