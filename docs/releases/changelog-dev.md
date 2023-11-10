# Release dev (development release)

### New features since last release

- Added the two main classes need for automatic-calibration, `CalibrationController` and `CalibrationNode`: [#554](https://github.com/qilimanjaro-tech/qililab/pull/554)

- Added the driver for Quantum Machines Manager and a new QuantumMachinesResult class to handle Quantum Machines instruments.
  [#568](https://github.com/qilimanjaro-tech/qililab/pull/568)

### Improvements

- Improved the UX for circuit transpilation by unifying the native gate and pulse transpiler under one `CircuitTranspiler` class, which has 3 methods:
  - `circuit_to_native`: transpiles a qibo circuit to native gates (Drag, CZ, Wait, M) and optionally RZ if optimize=False (optimize=True by default)
  - `circuit_to_pulses`: transpiles a native gate circuit to a `PulseSchedule`
  - `transpile_circuit`: runs both of the methods above sequentially
    `Wait` gate moved from the `utils` module to `circuit_transpilation_native_gates`
    [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

### Breaking changes

### Deprecations / Removals

- Removed the park gate since it is no longer needed
  [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

### Documentation

### Bug fixes

- Fixed [bug #579](https://github.com/qilimanjaro-tech/qililab/issues/579), were now all `yaml.dumps` are done with [ruamel](https://yaml.readthedocs.io/en/latest/#changelog), for not losing decimals precisons, and also following the previous bug due to the elimination of `ruamel.yaml.round_trip_dump`, the version of ruamel in qililab got fixed, and imports where rewritten for more clarity, [#577](https://github.com/qilimanjaro-tech/qililab/pull/578)
