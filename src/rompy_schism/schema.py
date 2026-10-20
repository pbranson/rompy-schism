"""Version contract for complete serialized SCHISM configurations."""

from typing import Literal

SchismSchemaVersion = Literal[
    "schism-v5.13",
    "schism-dev-20250523",
    "schism-master",
]

# This default is a permanent compatibility contract. Never advance it when a
# new SCHISM schema is introduced; unversioned historical configs are v5.13.
DEFAULT_SCHISM_SCHEMA: SchismSchemaVersion = "schism-v5.13"

# Immutable pins, oldest first: schema name -> SCHISM git ref. Release tags are
# named schism-vX.Y; anything else is schism-dev-YYYYMMDD (SCHISM commit date).
SCHISM_PINS: dict[str, str] = {
    "schism-v5.13": "v5.13.0",
    "schism-dev-20250523": "2135910d067608ca6b3d3663234cc0f01fd11f3d",
}

# Authoring alias for the newest pin. Serialized configs record the pin, so a
# saved config keeps its meaning when the alias moves.
SCHISM_MASTER_ALIAS = "schism-master"


def resolve_schema(version: str) -> str:
    """Return the pin a schema name stands for."""
    if version == SCHISM_MASTER_ALIAS:
        return next(reversed(SCHISM_PINS))
    if version not in SCHISM_PINS:
        raise ValueError(f"Unsupported SCHISM schema version: {version}")
    return version


def schema_index(version: str) -> int:
    """Position of the resolved pin in SCHISM_PINS."""
    return list(SCHISM_PINS).index(resolve_schema(version))
