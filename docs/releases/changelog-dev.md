# Release dev (development release)

### New features since last release
- Add magic method to run python code as slurm jobs from Jupyter Notebooks.
[#600](https://github.com/qilimanjaro-tech/qililab/pull/600)
- Added the two main classes need for automatic-calibration, `CalibrationController` and `CalibrationNode`: [#554](https://github.com/qilimanjaro-tech/qililab/pull/554)

- Added the driver for Quantum Machines Manager and a new QuantumMachinesResult class to handle Quantum Machines instruments.
  [#568](https://github.com/qilimanjaro-tech/qililab/pull/568)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed [bug #579](https://github.com/qilimanjaro-tech/qililab/issues/579), were now all `yaml.dumps` are done with [ruamel](https://yaml.readthedocs.io/en/latest/#changelog), for not losing decimals precisons, and also following the previous bug due to the elimination of `ruamel.yaml.round_trip_dump`, the version of ruamel in qililab got fixed, and imports where rewritten for more clarity, [#577](https://github.com/qilimanjaro-tech/qililab/pull/578)
