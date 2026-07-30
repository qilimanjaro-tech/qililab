# Release dev (development release)

### New features since last release

- Added `platform.set_calibration`, which stores a `Calibration` (given an instance or file path) on the platform. `execute_qprogram`, `execute_qprograms_parallel`, and database/stream saving now fall back to it when no `calibration` argument is passed; an explicit argument always overrides it.
  [#1165](https://github.com/qilimanjaro-tech/qililab/pull/1165)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Make it so if you input None in `NonLinearCrosstalkMatrix.set_non_linear_params` it sets the parameters to None, instead of ignoring them.
  [#1173](https://github.com/qilimanjaro-tech/qililab/pull/1173)