# Release dev (development release)

### New features since last release

- Added the Qblox-specific `set_markers()` method in `QProgram`. This method takes a 4-bit binary mask as input, where `0` means that the associated marker will be open (no signal) and `1` means that the associated marker will be closed (signal). The mapping between bit indexes and markers depends on the Qblox module that the compiled `QProgram` will run on.

  Example:

  ```Python
  qp = QProgram()
  qp.qblox.set_markers(bus='drive_q0', mask='0111')
  ```

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `set_markers_override_enabled_by_port` and `set_markers_override_value_by_port` methods in `QbloxModule` to set markers through QCoDeS, overriding Q1ASM values.

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `threshold_rotations` argument to `compile()` method in `QProgram`. This argument allows to use rotation angles on measurement instructions if not specified. Currently used to use the angle rotations specified on the runcard (if any) so the user does not have to explicitly pass it as argument to the measure instruction.  Used for classification of results in Quantum Machines's modules.

  [#759](https://github.com/qilimanjaro-tech/qililab/pull/759)

### Improvements

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

### Breaking changes

### Deprecations / Removals

- Deleted all the files in `execution` and `experiment` directories (Already obsolete).
  [#749](https://github.com/qilimanjaro-tech/qililab/pull/749)

### Documentation

### Bug fixes
