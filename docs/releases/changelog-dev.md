# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug where `CrosstalkMatrix.to_array()` crashed instead of creating the right array when some field of the matrix dictionary where missing (missing values of the matrix), this should default to the identity (values of 1 in the diagonal and 0 outside the diagonal). Now it creates an array even if there are missing elements of the matrix and defaults them to 0 or 1 if those elements are in the diagonal of the matrix.
Also fixed the `str` representation of the same crosstalk matrix as the same missing values were represented with ones instead of zeroes.
  [#1125](https://github.com/qilimanjaro-tech/qililab/pull/1125)