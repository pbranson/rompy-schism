"""Default param.nml must not emit veg_lai.

SCHISM 5a174a05 removed veg_lai from namelist /OPT/. Gfortran aborts the
OPT read on an unknown name. Older revisions initialize veg_lai to 1 before
that read, so omitting the name keeps those builds on the same default.
"""

import pytest
from pydantic import ValidationError

from rompy_schism.namelists.param import Param, Vegetation


def test_default_param_omits_veg_lai():
    rendered = Param().render()
    assert "veg_lai" not in rendered
    assert "veg_cw = 1.5" in rendered


def test_explicit_veg_lai_still_renders():
    rendered = Param(vegetation=Vegetation(veg_lai=4.0)).render()
    assert "veg_lai = 4.0" in rendered


def test_negative_veg_lai_rejected():
    with pytest.raises(ValidationError, match="veg_lai"):
        Vegetation(veg_lai=-1.0)
