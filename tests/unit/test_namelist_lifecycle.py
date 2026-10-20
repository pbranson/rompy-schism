import pytest
from pydantic import ValidationError
from rompy.core.time import TimeRange

from rompy_schism.namelists import NML
from rompy_schism.namelists.lifecycle import LIFECYCLE
from rompy_schism.namelists.param import Opt, Param, Schout
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


MASTER_NEW = {
    "opt": {
        "vclose_surf_frac0": 0.5,
        "age_marsh_min": 1.0,
        "istemp": 1,
        "ihconsv": 1,
        "relax_2_airt": 0.1,
    },
    "schout": {"chunk_size_vrt": 4},
}


def test_master_render_drops_retired_and_omits_unset_new_names():
    rendered = Param().render("schism-master")
    assert "nmarsh_types = 2" in rendered
    for gone in ("veg_lai", "vclose_surf_frac", "isconsv", "istemp", "chunk_size_vrt"):
        assert f"{gone} =" not in rendered


def test_master_renders_new_names_when_set():
    rendered = Param(**MASTER_NEW).render("schism-master")
    assert "vclose_surf_frac0 = 0.5" in rendered
    assert "istemp = 1" in rendered
    assert "chunk_size_vrt = 4" in rendered


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"opt": {"veg_lai": 1}}, "veg_lai.*removed in schism-dev-20261019"),
        ({"opt": {"vclose_surf_frac": 1.0}}, "vclose_surf_frac.*vclose_surf_frac0"),
    ],
)
def test_master_rejects_retired_names(kwargs, match):
    with pytest.raises(ValueError, match=match):
        Param(**kwargs).validate_schema("schism-master")


@pytest.mark.parametrize("schema", ["schism-v5.13", "schism-dev-20250523"])
def test_frozen_pins_reject_master_names(schema):
    with pytest.raises(ValueError, match="added in schism-dev-20261019"):
        Param(opt={"istemp": 0}).validate_schema(schema)


def test_update_times_keeps_master_valid():
    nml = NML(param=Param())
    nml.update_times(TimeRange(start="2023-01-01", end="2023-01-02", dt=3600))
    nml.param.validate_schema("schism-master")
    assert "veg_lai =" not in nml.param.render("schism-master")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vclose_surf_frac0": 1.5},
        {"relax_2_airt": -0.1},
        {"relax_2_airt": 1.1},
        {"age_marsh_min": -1.0},
        {"istemp": 1, "ihconsv": 0},
    ],
)
def test_new_opt_values_mirror_schism_aborts(kwargs):
    with pytest.raises(ValidationError):
        Opt(**kwargs)


def test_negative_vclose_surf_frac0_means_read_vclose_gr3():
    assert Opt(vclose_surf_frac0=-1.0).vclose_surf_frac0 == -1.0


def test_chunk_size_vrt_rejects_zero():
    with pytest.raises(ValidationError):
        Schout(chunk_size_vrt=0)
