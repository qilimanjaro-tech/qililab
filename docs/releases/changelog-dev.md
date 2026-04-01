# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
- Circuits: fixed a `KeyError` caused by incorrectly creating an empty flux bus schedule to apply an offset. This process was unintentionally adding all instruments from the settings (including the S4g) to the pulse schedule, which is incorrect. The unnecessary flux bus schedule has been removed, as the instrument already applies the offset automatically.
[#1085](https://github.com/qilimanjaro-tech/qililab/pull/1085)