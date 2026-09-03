"""pyTMD 2.x / 3.x import compatibility for bctides."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

pytest.importorskip("pyTMD")
pytest.importorskip("rompy_schism")


def test_tmd_args_module_exposes_bctides_api():
    """bctides imports _tmd_args from arguments (2.x) or constituents (3.x)."""
    from rompy_schism import bctides

    try:
        import pyTMD.arguments as expected
    except ImportError:
        import pyTMD.constituents as expected

    assert bctides._tmd_args is expected
    for name in (
        "nodal_modulation",
        "frequency",
        "coefficients_table",
        "_constituent_parameters",
    ):
        assert hasattr(bctides._tmd_args, name), name


def test_interp_group_v3_opens_chunked_then_crops():
    """pyTMD regional path: chunks='auto' at open, then tmd.crop(bounds)."""
    from rompy_schism.bctides import Bctides

    bc = Bctides.__new__(Bctides)
    bc.tide_interpolation_method = "linear"
    bc.extrapolate_tides = False
    bc.extrapolation_distance = 0.0

    cons = ["M2"]
    lons = np.array([150.0, 151.0])
    lats = np.array([-23.0, -24.0])
    bounds = [149.0, 152.0, -25.0, -22.0]

    local = MagicMock()
    local.__contains__ = lambda self, key: key == "M2"
    local.__getitem__ = lambda self, key: SimpleNamespace(
        tmd=SimpleNamespace(amplitude=np.ones(2), phase=np.zeros(2))
    )

    cropped = MagicMock()
    cropped.tmd.coords_as.return_value = (lons, lats)
    cropped.tmd.interp.return_value = local

    opened = MagicMock()
    opened.tmd.crop.return_value = cropped

    model = MagicMock()
    model.open_dataset.return_value = opened

    amp, pha = bc._interp_group_v3(model, "z", lons, lats, cons, bounds)

    model.reduce_constituents.assert_called_once_with(cons, group="z")
    model.open_dataset.assert_called_once_with(
        group="z",
        constituents=cons,
        chunks="auto",
    )
    opened.tmd.crop.assert_called_once_with(bounds, buffer=0)
    assert amp.shape == (2, 1)
    assert pha.shape == (2, 1)
