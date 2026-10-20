# SCHISM configuration schema versions

`SCHISMConfig.schema_version` identifies the contract used by the **complete
serialized configuration**. It is the single source of truth for
version-dependent defaults, validation, serialization, and generated model
inputs.

```yaml
model_type: schism
schema_version: schism-master

grid:
  # ...

nml:
  param:
    # No nested version discriminator
```

## Compatibility contract

Configurations that omit `schema_version` are always interpreted as
`schism-v5.13`. This is a permanent compatibility rule: the implicit version
must not advance when support for newer SCHISM releases is added.

When an unversioned configuration is serialized, Rompy writes the resolved
value explicitly:

```yaml
schema_version: schism-v5.13
```

This ensures that loading and re-serializing a historical configuration makes
its contract visible without changing its behaviour.

Serialized configurations contain the resolved fields for their selected
schema. Consequently, a load → dump → load round trip preserves both the schema
version and the generated namelist behaviour.

## Pins

Each schema is an immutable pin to one SCHISM revision, oldest first:

| Schema | SCHISM ref | Namelist changes from the previous pin |
| --- | --- | --- |
| `schism-v5.13` | `v5.13.0` | — |
| `schism-dev-20250523` | `2135910d` | adds `core.nmarsh_types` (rendered as 2); removes `opt.isconsv` (use `PREC_EVAP`) |
| `schism-dev-20261019` | `a3e58bff` | removes `opt.veg_lai` and `opt.vclose_surf_frac`; adds `opt.vclose_surf_frac0`, `opt.age_marsh_min`, `opt.istemp`, `opt.relax_2_airt`, `schout.chunk_size_vrt` |

`schism-vX.Y` names are used only for SCHISM release tags. Other pins are
`schism-dev-YYYYMMDD`, using the SCHISM commit date.

`schism-master` is an authoring alias for the newest pin. Configs written with
it are serialized with the pin name, so a saved config keeps its meaning when
the alias moves.

Values for names a pin does not declare are rejected. New `/OPT/` and
`/SCHOUT/` names are rendered only when set; SCHISM supplies their defaults.

## Adding a pin

1. Diff the `/CORE/`, `/OPT/` and `/SCHOUT/` declarations in
   `src/Hydro/schism_init.F90` between the newest pin and the new SCHISM ref.
2. Append the pin to `SCHISM_PINS` and `SchismSchemaVersion` in
   `rompy_schism/schema.py`.
3. For each changed name rompy-schism models, add or update a row in
   `rompy_schism/namelists/lifecycle.py`; add model fields (default `None`) for
   new names worth exposing.
4. Add a YAML round-trip fixture and a case in
   `tests/test_schism_version_compatibility.py`.
5. Never edit an existing pin's ref or rows' meaning for existing pins.

Do not independently version nested namelist models. A SCHISM release is one
configuration contract, even when a particular release changes only one
namelist.
