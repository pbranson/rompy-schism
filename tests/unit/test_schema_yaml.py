"""Golden YAML round-trip tests for complete SCHISM schema contracts."""

from pathlib import Path

import pytest
import yaml

from rompy_schism.config import SCHISMConfig
from rompy_schism.schema import resolve_schema

FIXTURES = Path(__file__).parents[1] / "schema_fixtures"


@pytest.mark.parametrize(
    ("fixture", "expected_version"),
    [
        ("unversioned-v513.yaml", "schism-v5.13"),
        ("explicit-v513.yaml", "schism-v5.13"),
        ("explicit-dev-20250523.yaml", "schism-dev-20250523"),
        ("explicit-schism-master.yaml", "schism-dev-20261019"),
    ],
)
def test_complete_config_yaml_round_trip_preserves_rendering(fixture, expected_version):
    source = yaml.safe_load((FIXTURES / fixture).read_text())
    original = SCHISMConfig.model_validate(source)
    original_rendered = original.nml.param.render(original.schema_version)

    serialized = original.model_dump(mode="json")
    yaml_text = yaml.safe_dump(serialized, sort_keys=False)
    restored = SCHISMConfig.model_validate(yaml.safe_load(yaml_text))
    restored_rendered = restored.nml.param.render(restored.schema_version)

    assert resolve_schema(original.schema_version) == expected_version
    assert restored.schema_version == expected_version
    assert restored_rendered == original_rendered
    assert serialized["schema_version"] == expected_version
    assert "param_schema" not in serialized["nml"]["param"]

    core = serialized["nml"]["param"]["core"]
    opt = serialized["nml"]["param"]["opt"]
    if expected_version == "schism-v5.13":
        assert "nmarsh_types" not in core
        assert opt["isconsv"] == 0
    else:
        assert core["nmarsh_types"] == 2
        assert "isconsv" not in opt
    if expected_version == "schism-dev-20261019":
        assert "veg_lai" not in opt and "vclose_surf_frac" not in opt


def test_unversioned_and_explicit_v513_are_semantically_identical():
    unversioned = SCHISMConfig.model_validate(
        yaml.safe_load((FIXTURES / "unversioned-v513.yaml").read_text())
    )
    explicit = SCHISMConfig.model_validate(
        yaml.safe_load((FIXTURES / "explicit-v513.yaml").read_text())
    )

    assert unversioned.model_dump(mode="json") == explicit.model_dump(mode="json")
    assert unversioned.nml.param.render() == explicit.nml.param.render()
