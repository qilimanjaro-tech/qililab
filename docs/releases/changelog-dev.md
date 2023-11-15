# Release dev (development release)

### New features since last release

- Added real time results saving capability.
  [#598](https://github.com/qilimanjaro-tech/qililab/pull/598)

- Added the two main classes need for automatic-calibration, `CalibrationController` and `CalibrationNode`: [#554](https://github.com/qilimanjaro-tech/qililab/pull/554)

- Add magic method to run python code as slurm jobs from Jupyter Notebooks.
  [#600](https://github.com/qilimanjaro-tech/qililab/pull/600)

- Implemented `QuantumMachinesCompiler` class to compile QPrograms to QUA programs.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Implemented `platform.execute_qprogram()` method to execute a qprogram on Qblox hardware.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Added the two main classes need for automatic-calibration, `CalibrationController` and `CalibrationNode`
  [#554](https://github.com/qilimanjaro-tech/qililab/pull/554)

- Added the driver for Quantum Machines Manager and a new QuantumMachinesResult class to handle Quantum Machines instruments.
  [#568](https://github.com/qilimanjaro-tech/qililab/pull/568)

### Improvements

- Improved the UX for circuit transpilation by unifying the native gate and pulse transpiler under one `CircuitTranspiler` class, which has 3 methods:

  - `circuit_to_native`: transpiles a qibo circuit to native gates (Drag, CZ, Wait, M) and optionally RZ if optimize=False (optimize=True by default)
  - `circuit_to_pulses`: transpiles a native gate circuit to a `PulseSchedule`
  - `transpile_circuit`: runs both of the methods above sequentially
    `Wait` gate moved from the `utils` module to `circuit_transpilation_native_gates`
    [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

- Added `infinite_loop()` method to QProgram.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Added `measure()` method to QProgram.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Various improvements in the compilation flow of `QbloxCompiler`.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

### Breaking changes

- Changed `resolution` parameter of waveforms' `envelope()` method to integer.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Changed the way variables work within a QProgram. Variables are now instantiated based on the physical domain they affect.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

### Deprecations / Removals

- Removed the park gate since it is no longer needed
  [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

### Documentation

### Bug fixes

- Fixed [bug #579](https://github.com/qilimanjaro-tech/qililab/issues/579), were now all `yaml.dumps` are done with [ruamel](https://yaml.readthedocs.io/en/latest/#changelog), for not losing decimals precisons, and also following the previous bug due to the elimination of `ruamel.yaml.round_trip_dump`, the version of ruamel in qililab got fixed, and imports where rewritten for more clarity
  [#577](https://github.com/qilimanjaro-tech/qililab/pull/578)
