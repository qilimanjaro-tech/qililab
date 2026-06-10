# Release dev (development release)

### New features since last release

- Added bus_mapping to measurement database table `Measurement`. Bus mapping is necessary for live plot drawing of the qprogram and it has been information missing in the database. StreamArray already has the bus_mapping as an input, this input is the dictionary that will be saved in the database.
  [#1136](https://github.com/qilimanjaro-tech/qililab/pull/1136)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `load_sequence_by_id` where measurements were returned in an undefined order, causing incorrect results when processing sequences. Measurements are now ordered by `measurement_id`.
  [#1132](https://github.com/qilimanjaro-tech/qililab/pull/1132)

- Pinned spirack to ==0.2.12 as some newer versions may cause an error when importing qblox-instruments.
  [#1135](https://github.com/qilimanjaro-tech/qililab/pull/1135)