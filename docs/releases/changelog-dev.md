# Release dev (development release)

### New features since last release

### Improvements

- Moved qblox external trigger check from compiler to platform. This avoids raising errors related to the Runcard inside the compiler.
  [#1112](https://github.com/qilimanjaro-tech/qililab/pull/1112)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
[#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
