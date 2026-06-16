# Release dev (development release)

### New features since last release

- Added bus_mapping to measurement database table `Measurement`. Bus mapping is necessary for live plot drawing of the qprogram and it has been information missing in the database. StreamArray already has the bus_mapping as an input, this input is the dictionary that will be saved in the database.
  [#1136](https://github.com/qilimanjaro-tech/qililab/pull/1136)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
[#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
