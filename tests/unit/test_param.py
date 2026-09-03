"""SCHISM ≥ v5.12 CORE/OPT param.nml contracts."""

import warnings
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

    def test_opt_ignores_legacy_isconsv_zero(self, tmp_path):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            opt = Opt(isconsv=0)
            Param.model_validate({"opt": {"isconsv": 0}})
        assert "isconsv" not in opt.model_dump()
        Param(opt=Opt(isconsv=0)).write_nml(tmp_path)
        assert "isconsv =" not in (tmp_path / "param.nml").read_text()

    def test_opt_warns_on_legacy_isconsv_nonzero(self):
        with pytest.warns(DeprecationWarning, match="isconsv"):
            Opt(isconsv=1)

    def test_opt_still_rejects_unknown_keys(self):
        with pytest.raises(ValidationError, match="not_a_real_opt"):
            Opt(not_a_real_opt=1)
