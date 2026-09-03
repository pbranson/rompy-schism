"""pyTMD 3 tidal BC: constituents import, overlay JSON, interpolate path."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import pyTMD.constituents
from pyTMD.io.model import load_database

pytest.importorskip("pyTMD")
pytest.importorskip("rompy_schism")

_OVERLAY = (
    Path(__file__).resolve().parents[1] / "test_data" / "tides" / "database.json"
)


class _LocalAmpPhase:
    """Minimal mapping so ``name in ds`` / ``ds[name].tmd`` work."""

    def __init__(self, names, npts):
        self.data_vars = list(names)
        self._data = {
            name: SimpleNamespace(
                tmd=SimpleNamespace(
                    amplitude=np.ones(npts),
                    phase=np.zeros(npts),
                )
            )
            for name in names
        }

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]


def test_bctides_imports_constituents():
    """bctides uses pyTMD.constituents (pyTMD 3); no arguments fallback."""
    from rompy_schism import bctides

    assert bctides._tmd_args is pyTMD.constituents
    for name in (
        "nodal_modulation",
        "frequency",
        "coefficients_table",
        "_constituent_parameters",
    ):
        assert hasattr(bctides._tmd_args, name), name
    assert not hasattr(bctides.Bctides, "_interpolate_tidal_data_v2")


def test_fixture_overlay_lists_oceanum_atlas():
    """Test extra_databases JSON is pyTMD 3 (model-name keys, z/u/v groups)."""
    params = load_database(extra_databases=[_OVERLAY])
    assert "OCEANUM-atlas" in list(params.keys())
    model = params["OCEANUM-atlas"]
    for group in ("z", "u", "v"):
        assert group in model, group


def test_get_tidal_factors_m2_fes():
    """Nodal/frequency call sites run on pyTMD.constituents."""
    from rompy_schism.bctides import Bctides

    bc = Bctides.__new__(Bctides)
    bc.tnames = ["m2"]
    bc.tidal_model = "FES2014"
    bc._start_time = datetime(2020, 1, 1)
    bc.amp = []
    bc._get_tidal_factors()
    assert len(bc.freq) == 1
    assert bc.freq[0] > 0
    assert bc.nodal_factor[0] > 0


def test_interp_group_opens_chunked_then_crops():
    """Regional path: chunks at open, then tmd.crop(bounds)."""
    from rompy_schism import bctides
    from rompy_schism.bctides import Bctides

    bc = Bctides.__new__(Bctides)
    bc.tide_interpolation_method = "linear"
    bc.extrapolate_tides = False
    bc.extrapolation_distance = 0.0

    cons = ["M2"]
    lons = np.array([150.0, 151.0])
    lats = np.array([-23.0, -24.0])
    bounds = [149.0, 152.0, -25.0, -22.0]
    npts = lons.size

    local = _LocalAmpPhase(cons, npts)
    cropped = MagicMock()
    cropped.tmd.coords_as.return_value = (lons, lats)
    cropped.tmd.interp.return_value = local

    opened = MagicMock()
    opened.tmd.crop.return_value = cropped

    model = MagicMock()
    model.open_dataset.return_value = opened

    amp, pha = bc._interp_group(model, "z", lons, lats, cons, bounds)

    model.reduce_constituents.assert_called_once_with(cons, group="z")
    model.open_dataset.assert_called_once_with(
        group="z",
        constituents=cons,
        chunks=bctides._OPEN_CHUNKS,
    )
    opened.tmd.crop.assert_called_once_with(bounds, buffer=0)
    np.testing.assert_array_equal(amp, np.ones((2, 1)))
    np.testing.assert_array_equal(pha, np.zeros((2, 1)))


def test_elevation_from_database_z_only():
    """Elevation-only extracts must not require u/v model files."""
    from rompy_schism.bctides import Bctides

    bc = Bctides.__new__(Bctides)
    bc.tidal_database = None
    bc.extra_databases = []
    bc.tidal_model = "FES2014"
    bc.tide_interpolation_method = "linear"
    bc.extrapolate_tides = False
    bc.extrapolation_distance = 0.0

    tmd_model = MagicMock()
    model = MagicMock()
    tmd_model.from_database.return_value = model
    amp = np.ones((2, 1))
    pha = np.zeros((2, 1))
    bc._interp_group = MagicMock(return_value=(amp, pha))

    with patch("rompy_schism.bctides.pyTMD.io.model", return_value=tmd_model):
        out = bc._interpolate_tidal_data(
            np.array([150.0, 151.0]),
            np.array([-23.0, -24.0]),
            ["m2"],
            "h",
        )

    tmd_model.from_database.assert_called_once_with("FES2014", group=("z",))
    assert out.shape == (2, 1, 2)


def test_uv_from_database_zuv():
    """Velocity extracts still load z+u+v metadata."""
    from rompy_schism.bctides import Bctides

    bc = Bctides.__new__(Bctides)
    bc.tidal_database = None
    bc.extra_databases = []
    bc.tidal_model = "FES2014"
    bc.tide_interpolation_method = "linear"
    bc.extrapolate_tides = False
    bc.extrapolation_distance = 0.0

    tmd_model = MagicMock()
    model = MagicMock()
    tmd_model.from_database.return_value = model
    amp = np.ones((2, 1))
    pha = np.zeros((2, 1))
    bc._interp_group = MagicMock(return_value=(amp, pha))

    with patch("rompy_schism.bctides.pyTMD.io.model", return_value=tmd_model):
        out = bc._interpolate_tidal_data(
            np.array([150.0, 151.0]),
            np.array([-23.0, -24.0]),
            ["m2"],
            "uv",
        )

    tmd_model.from_database.assert_called_once_with(
        "FES2014", group=("z", "u", "v")
    )
    assert out.shape == (2, 1, 4)
