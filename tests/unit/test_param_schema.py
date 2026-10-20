"""Tests for top-level SCHISM configuration schema versioning."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from rompy.core.data import DataBlob

from rompy_schism.config import SCHISMConfig
from rompy_schism.grid import SCHISMGrid
from rompy_schism.namelists import NML
from rompy_schism.namelists.param import Core, Param


def _grid(tmp_path: Path) -> SCHISMGrid:
    hgrid = tmp_path / "hgrid.gr3"
    hgrid.write_text("test grid\n")
    return SCHISMGrid(hgrid=DataBlob(source=str(hgrid)), rough=0.02)


class TestTopLevelSchemaVersion:
    def test_missing_version_preserves_v513_contract(self, tmp_path):
        config = SCHISMConfig.model_validate(
            {
                "model_type": "schism",
                "grid": _grid(tmp_path),
                "nml": {"param": {}},
            }
        )

        assert config.schema_version == "schism-v5.13"
        dumped = config.model_dump()
        assert dumped["schema_version"] == "schism-v5.13"
        assert "param_schema" not in dumped["nml"]["param"]
        assert "nmarsh_types" not in dumped["nml"]["param"]["core"]
        assert dumped["nml"]["param"]["opt"]["isconsv"] == 0

        rendered = config.nml.param.render(config.schema_version)
        assert "isconsv = 0" in rendered
        assert "nmarsh_types" not in rendered

    def test_dev_20250523_contract_is_selected_at_top_level(self, tmp_path):
        config = SCHISMConfig(
            schema_version="schism-dev-20250523",
            grid=_grid(tmp_path),
            nml=NML(param=Param()),
        )

        dumped = config.model_dump()
        assert dumped["nml"]["param"]["core"]["nmarsh_types"] == 2
        assert "isconsv" not in dumped["nml"]["param"]["opt"]

        rendered = config.nml.param.render(config.schema_version)
        assert "nmarsh_types = 2" in rendered
        assert "isconsv =" not in rendered
        assert "schema_version" not in rendered

    def test_serialized_version_survives_round_trip(self, tmp_path):
        config = SCHISMConfig(
            schema_version="schism-dev-20250523",
            grid=_grid(tmp_path),
            nml=NML(param=Param(core={"nmarsh_types": 3})),
        )

        restored = SCHISMConfig.model_validate(config.model_dump())
        assert restored.schema_version == "schism-dev-20250523"
        assert restored.nml.param.core.nmarsh_types == 3
        assert "nmarsh_types = 3" in restored.nml.param.render(restored.schema_version)

    def test_rejects_dev_only_field_under_v513(self, tmp_path):
        with pytest.raises(ValidationError, match="nmarsh_types"):
            SCHISMConfig(
                grid=_grid(tmp_path),
                nml=NML(param=Param(core={"nmarsh_types": 2})),
            )

    def test_rejects_legacy_isconsv_enabled_under_dev_20250523(self, tmp_path):
        with pytest.raises(ValidationError, match="PREC_EVAP"):
            SCHISMConfig(
                schema_version="schism-dev-20250523",
                grid=_grid(tmp_path),
                nml=NML(param=Param(opt={"isconsv": 1})),
            )

    def test_v514_name_is_gone(self, tmp_path):
        with pytest.raises(ValidationError, match="schema_version"):
            SCHISMConfig(schema_version="schism-v5.14", grid=_grid(tmp_path))

    def test_rejects_unknown_schema_version(self, tmp_path):
        with pytest.raises(ValidationError, match="schema_version"):
            SCHISMConfig(
                schema_version="schism-v6.0",
                grid=_grid(tmp_path),
            )


class TestVersionedParamRendering:
    def test_nml_write_passes_top_level_schema(self, tmp_path):
        NML(param=Param()).write_nml(tmp_path, schema_version="schism-dev-20250523")
        rendered = (tmp_path / "param.nml").read_text()
        assert "nmarsh_types = 2" in rendered
        assert "isconsv =" not in rendered

    @pytest.mark.parametrize("bad", [0, -1])
    def test_nmarsh_types_must_be_positive(self, bad):
        with pytest.raises(ValidationError):
            Core(nmarsh_types=bad)
