# Release dev (development release)

### New features since last release

- Added the Qblox-specific `set_markers()` method in `QProgram`. This method takes a 4-bit binary mask as input, where `0` means that the associated marker will be open (no signal) and `1` means that the associated marker will be closed (signal). The mapping between bit indexes and markers depends on the Qblox module that the compiled `QProgram` will run on.

  Example:

  ```Python
  qp = QProgram()
  qp.qblox.set_markers(bus='drive_q0', mask='0111')
  ```

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
