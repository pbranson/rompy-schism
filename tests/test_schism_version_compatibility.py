"""Run ROMPY-generated parameter schemas against real SCHISM revisions."""

from pathlib import Path

import pytest
from rompy.backends.config import DockerConfig
from rompy.core.data import DataBlob
from rompy.model import ModelRun

from rompy_schism.boundary_core import TidalDataset
from rompy_schism.config import SCHISMConfig
from rompy_schism.data import (
    BoundarySetupWithSource,
    SCHISMData,
    SCHISMDataBoundaryConditions,
)
from rompy_schism.grid import SCHISMGrid
from rompy_schism.namelists import NML, Param
from rompy_schism.schema import SCHISM_PINS


def _compatibility_model_run(tmp_path, tidal_data_files, schema_version, param):
    """Create the smallest existing ROMPY SCHISM case suitable for ipre=1."""
    test_data = Path(__file__).parent / "data" / "schism"

    grid = SCHISMGrid(
        hgrid=DataBlob(id="hgrid", source=str(test_data / "hgrid.gr3")),
        drag=2.5e-3,
        crs="epsg:4326",
    )
    boundary_conditions = SCHISMDataBoundaryConditions(
        data_type="boundary_conditions",
        setup_type="tidal",
        tidal_data=TidalDataset(
            tidal_database=tidal_data_files,
            tidal_model="OCEANUM-atlas",
            constituents=["M2", "S2", "N2"],
            nodal_corrections=False,
            tidal_potential=False,
            extrapolate_tides=True,
        ),
        boundaries={
            0: BoundarySetupWithSource(
                elev_type=3,
                vel_type=3,
                temp_type=0,
                salt_type=0,
            )
        },
    )
    config = SCHISMConfig(
        model_type="schism",
        schema_version=schema_version,
        grid=grid,
        data=SCHISMData(
            data_type="schism",
            boundary_conditions=boundary_conditions,
        ),
        nml=NML(param=param),
    )

    return ModelRun(
        output_dir=str(tmp_path),
        period={
            "start": "20230101T00",
            "end": "20230101T01",
            "interval": 3600,
        },
        run_id=f"param_compat_{schema_version}",
        delete_existing=True,
        config=config,
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    ("schism_ref", "schema_version", "param"),
    [
        pytest.param(
            SCHISM_PINS["schism-v5.13"],
            "schism-v5.13",
            Param(
                core={
                    "ipre": 1,
                    "dt": 150.0,
                    "ibc": 1,
                    "ibtp": 0,
                },
                schout={"iout_sta": 0},
            ),
            id="schism-v5.13",
        ),
        pytest.param(
            SCHISM_PINS["schism-dev-20250523"],
            "schism-dev-20250523",
            Param(
                core={
                    "ipre": 1,
                    "dt": 150.0,
                    "ibc": 1,
                    "ibtp": 0,
                    "nmarsh_types": 2,
                },
                schout={"iout_sta": 0},
            ),
            id="schism-dev-20250523",
        ),
        pytest.param(
            SCHISM_PINS["schism-dev-20261019"],
            "schism-dev-20261019",
            Param(
                core={"ipre": 1, "dt": 150.0, "ibc": 1, "ibtp": 0},
                schout={"iout_sta": 0},
            ),
            id="schism-dev-20261019",
        ),
    ],
)
def test_generated_param_schema_initializes_in_schism(
    tmp_path,
    docker_available,
    should_skip_docker_builds,
    tidal_data_files,
    schism_ref,
    schema_version,
    param,
):
    """SCHISM must parse and initialize each matching ROMPY parameter schema."""
    if not docker_available:
        pytest.skip("Docker is not available")
    if should_skip_docker_builds:
        pytest.skip("Docker builds are disabled in this environment")

    model_run = _compatibility_model_run(
        tmp_path, tidal_data_files, schema_version, param
    )
    context_path = Path(__file__).resolve().parents[1] / "docker" / "schism"
    docker_config = DockerConfig(
        dockerfile=Path("Dockerfile.compat"),
        build_context=context_path,
        build_args={"SCHISM_REF": schism_ref},
        executable="schism",
        mpiexec="mpirun",
        cpu=1,
        timeout=1800,
        env_vars={
            "OMPI_ALLOW_RUN_AS_ROOT": "1",
            "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
        },
    )

    assert model_run.run(backend=docker_config) is True

    fatal_error = Path(model_run.staging_dir) / "outputs" / "fatal.error"
    assert fatal_error.read_text().strip() == "", (
        f"SCHISM reported a fatal error:\n{fatal_error.read_text()}"
    )

    generated_param = Path(model_run.staging_dir) / "param.nml"
    rendered = generated_param.read_text()
    assert "schema_version" not in rendered
    if schema_version == "schism-v5.13":
        assert "isconsv = 0" in rendered
        assert "nmarsh_types" not in rendered
    else:
        assert "nmarsh_types = 2" in rendered
        assert "isconsv" not in rendered
    if schema_version == "schism-dev-20261019":
        assert "veg_lai" not in rendered
