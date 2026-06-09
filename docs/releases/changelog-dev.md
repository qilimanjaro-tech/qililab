# Release dev (development release)

### New features since last release

### Improvements

- Upgraded `qblox-instruments` dependency from `0.16.0` to `1.0.3`.
  [#1134](https://github.com/qilimanjaro-tech/qililab/pull/1134)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `load_sequence_by_id` where measurements were returned in an undefined order, causing incorrect results when processing sequences. Measurements are now ordered by `measurement_id`.
  [#1132](https://github.com/qilimanjaro-tech/qililab/pull/1132)
