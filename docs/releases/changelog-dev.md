# Release dev (development release)

### New features since last release

- Allow execution of `QProgram` through `platform.execute_qprogram` method for Quantum Machines hardware.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

### Improvements

- Added `bus_mapping` parameter in `QbloxCompiler.compile` method to allow changing the bus names of the compiled output.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Added `DictSerializable` protocol and `from_dict` utility function to enable (de)serialization (from)to dictionary for any class.
  [#659](https://github.com/qilimanjaro-tech/qililab/pull/659)

- Added method to get the QRM `channel_id` for a given qubit
  [#664](https://github.com/qilimanjaro-tech/qililab/pull/664)

### Improvements

- Compilation for pulses is now done at platform instead of being delegated to each bus pointing to an awg instrument. This allows easier
  communication between `pulse_bus_schedules` so that they can be handled at the same time in order to tackle more complex tasks which were
  not possible otherwise. It also decouples, to a great extent, the instruments and instrument controllers (hardware) from higher level processes more typical of quantum control, which are involved in the pulse compilation to assembly program steps.
  [#651](https://github.com/qilimanjaro-tech/qililab/pull/651)

- Changed save and load methods using `PyYAML` to `ruamel.YAML`
  [#661](https://github.com/qilimanjaro-tech/qililab/pull/661)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
