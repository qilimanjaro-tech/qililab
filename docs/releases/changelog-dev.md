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

- Fixed a bug in `load_sequence_by_id` where measurements were returned in an undefined order, causing incorrect results when processing sequences. Measurements are now ordered by `measurement_id`.
  [#1132](https://github.com/qilimanjaro-tech/qililab/pull/1132)

- Pinned spirack to ==0.2.12 as some newer versions may cause an error when importing qblox-instruments.
  [#1135](https://github.com/qilimanjaro-tech/qililab/pull/1135)