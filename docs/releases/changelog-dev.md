# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed issue where `Platform.set_parameter` using the alias of a "rswu-sp16tr" instrument would raise an error.
  [#1130](https://github.com/qilimanjaro-tech/qililab/pull/1130)

- Fixed a bug in `load_sequence_by_id` where measurements were returned in an undefined order, causing incorrect results when processing sequences. Measurements are now ordered by `measurement_id`.
  [#1132](https://github.com/qilimanjaro-tech/qililab/pull/1132)
