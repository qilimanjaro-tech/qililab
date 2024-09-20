# Release dev (development release)

### New features since last release

- Added offset set and get for quantum machines (both OPX+ and OPX1000). For hardware loops there is `qp.set_offset(bus: str, offset_path0: float, offset_path1: float | None)` where `offset_path0` is a mandatory field (for flux, drive and readout lines) and `offset_path1` is only used when changing the offset of buses that have to IQ lines (drive and readout). For software loops there is `platform.set_parameter(alias=bus_name, parameter=ql.Parameter.OFFSET_PARAMETER, value=offset_value)`. The possible arguments for `ql.Parameter` are: `DC_OFFSET` (flux lines), `OFFSET_I` (I lines for IQ buses), `OFFSET_Q` (Q lines for IQ buses), `OFFSET_OUT1` (output 1 lines for readout lines), `OFFSET_OUT2` (output 2 lines for readout lines).

[#791](https://github.com/qilimanjaro-tech/qililab/pull/791)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fix typo in ExceptionGroup import statement for python 3.11+
  [#808](https://github.com/qilimanjaro-tech/qililab/pull/808)
