"""pyTMD 2.x / 3.x import compatibility for bctides."""

import pytest

pytest.importorskip("pyTMD")
pytest.importorskip("rompy_schism")


def test_tmd_args_module_exposes_bctides_api():
    """bctides imports _tmd_args from arguments (2.x) or constituents (3.x)."""
    from rompy_schism import bctides

    for name in (
        "nodal_modulation",
        "frequency",
        "coefficients_table",
        "_constituent_parameters",
    ):
        assert hasattr(bctides._tmd_args, name), name
