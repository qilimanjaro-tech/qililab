# Release dev (development release)

### New features since last release

### Improvements

- Removed `external_trigger` parameter from within the runcard's qblox controller instrument. Now the function `QbloxClusterController.set_ext_trigger` is risen internally every time a qprogram contains a `wait_trigger` using the trigger channel 15 (last one).
  [#1112](https://github.com/qilimanjaro-tech/qililab/pull/1112)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
[#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
