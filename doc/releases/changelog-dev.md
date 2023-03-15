# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added new ChangeLog!
  [#170](https://github.com/qilimanjaro-tech/qililab/pull/170)

### Improvements

- Cast `chip` dictionary into the `ChipSchema` class and remove unused `InstrumentControllerSchema` class.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

### Breaking changes

### Deprecations

### Documentation

### Bug fixes

- Fix bug where calling `set_parameter` with `Parameter.DRAG_COEFFICIENT` would raise an error.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)
