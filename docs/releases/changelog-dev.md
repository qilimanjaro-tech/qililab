# Release dev (development release)

### New features since last release

- Allow execution of `QProgram` through `platform.execute_qprogram` method for Quantum Machines hardware.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Allow multiple measurements of the same qubit in a single circuit. Also allow measurements in the middle of a circuit.
  [#674](https://github.com/qilimanjaro-tech/qililab/pull/674)

- Wait times longer than 2\*\*16-4 (QBLOX maximum wait time in a Q1ASM wait instruction) are now allowed in the middle of
  a circuit.
  [#674](https://github.com/qilimanjaro-tech/qililab/pull/674)

### Improvements

- Added `bus_mapping` parameter in `QbloxCompiler.compile` method to allow changing the bus names of the compiled output.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Improved `QuantumMachinesCluster` instrument functionality.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Improved execution times of `QProgram` when used inside a software loop by using caching mechanism.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Added `DictSerializable` protocol and `from_dict` utility function to enable (de)serialization (from)to dictionary for any class.
  [#659](https://github.com/qilimanjaro-tech/qililab/pull/659)

- Added method to get the QRM `channel_id` for a given qubit.
  [#664](https://github.com/qilimanjaro-tech/qililab/pull/664)

- Added Domain restrictions to `Drag` pulse, `DragCorrection` waveform and `Gaussian` waveform.
  [#679](https://github.com/qilimanjaro-tech/qililab/pull/679)

### Improvements

- Compilation for pulses is now done at platform instead of being delegated to each bus pointing to an awg instrument. This allows easier
  communication between `pulse_bus_schedules` so that they can be handled at the same time in order to tackle more complex tasks which were
  not possible otherwise. It also decouples, to a great extent, the instruments and instrument controllers (hardware) from higher level processes more typical of quantum control, which are involved in the pulse compilation to assembly program steps.
  [#651](https://github.com/qilimanjaro-tech/qililab/pull/651)

- Changed save and load methods using `PyYAML` to `ruamel.YAML`.
  [#661](https://github.com/qilimanjaro-tech/qililab/pull/661)

- Allow measurements on more than one qblox readout module. This can be done by simply adding more than one readout bus and its corresponding
  connections to the runcard.
  [#656](https://github.com/qilimanjaro-tech/qililab/pull/656)

- Qprogram's qblox compiler now allows iterations over variables even if these variables do nothing. (eg. iterate over nshots)
  [#666](https://github.com/qilimanjaro-tech/qililab/pull/666)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Added the temporary parameter `wait_time` to QProgram's `play` method. This allows the user to emulate a `time_of_flight` duration for measurement until this is added as a setting in runcard.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Fixed issue with Yokogawa GS200 instrument, that raised an error during initial_setup when the instrument's output was on.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)
