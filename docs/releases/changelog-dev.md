# Release dev (development release)

### New features since last release

- Added `NonLinearState` to qprogram qblox crosstalk handler. This class controls the behavior of `play`, `set_offset`, `set_gain` and loop unpacking of the handler.
  [#1149](https://github.com/qilimanjaro-tech/qililab/pull/1149)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug with the automatic non-linear crosstalk compensation at the `QbloxCompiler` where the offset was set unnecessary times whenever a play followed a set offset in a qprogram.
  [#1149](https://github.com/qilimanjaro-tech/qililab/pull/1149)