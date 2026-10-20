"""Which param.nml names each SCHISM schema pin declares.

SCHISM aborts on any namelist name the binary does not declare and on missing
/CORE/ names. Only names that differ across pins appear here; everything else is
declared by every pin.
"""

from dataclasses import dataclass
from typing import Any

from rompy_schism.schema import schema_index


@dataclass(frozen=True)
class NamelistName:
    """One name's life across the pins in ``SCHISM_PINS``.

    ``fill`` is rendered wherever the name is declared and the user left it
    ``None``. /CORE/ names need one (SCHISM has no default); /OPT/ and /SCHOUT/
    additions should not have one (SCHISM defaults them before reading).
    """

    group: str
    name: str
    added: str | None = None
    removed: str | None = None
    fill: Any = None
    hint: str = ""

    def declared_in(self, schema: str) -> bool:
        index = schema_index(schema)
        after_add = self.added is None or index >= schema_index(self.added)
        before_remove = self.removed is None or index < schema_index(self.removed)
        return after_add and before_remove

    def unsupported_message(self, schema: str) -> str:
        if self.added is not None and schema_index(schema) < schema_index(self.added):
            reason = f"it was added in {self.added}"
        else:
            reason = f"it was removed in {self.removed}"
        message = f"{self.group}.{self.name} is not supported by {schema}: {reason}"
        return f"{message}; {self.hint}" if self.hint else message


LIFECYCLE: tuple[NamelistName, ...] = (
    NamelistName("core", "nmarsh_types", added="schism-dev-20250523", fill=2),
    NamelistName(
        "opt",
        "isconsv",
        removed="schism-dev-20250523",
        fill=0,
        hint="compile SCHISM with PREC_EVAP instead",
    ),
    NamelistName("opt", "veg_lai", fill=1),
    NamelistName("opt", "vclose_surf_frac", fill=1.0),
)
