"""SCHISM ≥ v5.12 CORE/OPT param.nml contracts."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from rompy_schism.namelists.param import Core, Opt, Param

pytest.importorskip("rompy_schism")


class TestParamV512:
    def test_write_nml_emits_nmarsh_types_not_isconsv(self, tmp_path):
        Param().write_nml(tmp_path)
        text = (tmp_path / "param.nml").read_text()
        assert "nmarsh_types" in text
        assert "isconsv =" not in text

    def test_nmarsh_types_default(self):
        assert Core().nmarsh_types == 2

    @pytest.mark.parametrize("bad", [0, -1])
    def test_nmarsh_types_must_be_positive(self, bad):
        with pytest.raises(ValidationError, match="nmarsh_types must be positive"):
            Core(nmarsh_types=bad)

    def test_opt_has_no_isconsv_field(self):
        assert "isconsv" not in Opt.model_fields
