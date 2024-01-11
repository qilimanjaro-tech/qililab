# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Allow execution of `QProgram` through `platform.execute_qprogram` method for Quantum Machines hardware.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

### Improvements

- Added `bus_mapping` parameter in `QbloxCompiler.compile` method to allow changing the bus names of the compiled output.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Added `DictSerializable` protocol and `from_dict` utility function to enable (de)serialization (from)to dictionary for any class.
  [#659](https://github.com/qilimanjaro-tech/qililab/pull/659)

### Improvements

- Changed save and load methods using `PyYAML` to `ruamel.YAML`
  [#661](https://github.com/qilimanjaro-tech/qililab/pull/661)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
