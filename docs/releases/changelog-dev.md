# Release dev (development release)

### New features since last release

- Multiple measurements on the same qubit at arbitrary points of the circuit are now supported. So far results for this can only be obtained through the `result.array`
  property. Results in the array will be grouped by iq pairs (same as before) and ordered in the same order as measurements in the circuit.
  For example, if a circuit is measuring `M(1)-M(2)-M(0,1)` the first iq values will be those for `M(1)`, followed by `M(2)`, `M(0)` and `M(1)`.
  [#524](https://github.com/qilimanjaro-tech/qililab/pull/524)

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
