# Release dev (development release)

### New features since last release

- Added `platform.set_calibration`, which stores a `Calibration` (given an instance or file path) on the platform. `execute_qprogram`, `execute_qprograms_parallel`, and database/stream saving now fall back to it when no `calibration` argument is passed; an explicit argument always overrides it.
  [#1165](https://github.com/qilimanjaro-tech/qililab/pull/1165)

### Improvements

- Added the `_Sentinels` enum class in `utils/sentinels.py`, currently exposing only `UNSET` (more sentinels can be added later). Sentinels mark uninitialized, unset or otherwise undefined values without relying on `None`, which keeps the logic clearer and makes it possible to distinguish an explicit `None` from an unset default.
  [#1173](https://github.com/qilimanjaro-tech/qililab/pull/1173)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Passing `None` to `NonLinearCrosstalkMatrix.set_non_linear_params` now clears the parameters instead of keeping their previously set values, allowing users to remove non-linear parameters that were set earlier.
  [#1173](https://github.com/qilimanjaro-tech/qililab/pull/1173)