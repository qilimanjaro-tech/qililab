# Release dev (development release)

### New features since last release

### Improvements

- Upgraded `qblox-instruments` dependency from `0.16.0` to `1.0.3`.
  [#1134](https://github.com/qilimanjaro-tech/qililab/pull/1134)

- Updated `Platform.execute_qprogram` and `Platform.execute_qprograms_parallel` so that when uploading the sequence to a QBlox cluster, if the previous program is the same, it updated acquisitions (to reset the bins) and weights and waveforms if they changed. This speeds up software loops where the program does not change between executions.
  []()

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
[#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
