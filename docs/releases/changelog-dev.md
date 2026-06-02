# Release dev (development release)

### New features since last release

- Added `load_sequence_by_id` inside the database manager. This function allows to retrieve simultaneous measurements given a list of IDs from a sequence of measurements. `Measurement.sequence_id`has been added as a measurement expression inside head and tail.
  [#1121](https://github.com/qilimanjaro-tech/qililab/pull/1121)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in the `Calibration` crosstalk matrix where the `inter_crosstalk`'s new_matrix was not correctly calculated. Now it behaves as intended.
  [#1121](https://github.com/qilimanjaro-tech/qililab/pull/1121)

- Fixed a bug where `CrosstalkMatrix.to_array()` crashed instead of creating the right array when some field of the matrix dictionary where missing (missing values of the matrix), this should default to the identity (values of 1 in the diagonal and 0 outside the diagonal). Now it creates an array even if there are missing elements of the matrix and defaults them to 0 or 1 if those elements are in the diagonal of the matrix.
Also fixed the `str` representation of the same crosstalk matrix as the same missing values were represented with ones instead of zeroes.
  [#1125](https://github.com/qilimanjaro-tech/qililab/pull/1125)

- Fixed `NonLinearFluxVector` handling of the ForLoop to mach the QbloxCompiler behavior.
 [#1126](https://github.com/qilimanjaro-tech/qililab/pull/1126)
