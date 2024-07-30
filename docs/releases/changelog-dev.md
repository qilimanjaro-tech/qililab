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

### Improvements

- Now platform.get_parameter works for QM without the need of connecting to the machine.

- Added the option to get the time of flight and smearing information from the QM cluster
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

### Breaking changes

### Deprecations / Removals

- Deleted all the files in `execution` and `experiment` directories (Already obsolete).
  [#749](https://github.com/qilimanjaro-tech/qililab/pull/749)

### Documentation

### Bug fixes

- get_parameter for QM did not work due to the lack of the variable `bus_alias in self.system_control.get_parameter`. The variable has been added to the function and now get parameter does not return a crash.
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)
