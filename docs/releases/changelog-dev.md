# Release dev (development release)

### New features since last release

- Previously, `QProgram.set_offset` required both I and Q offsets (`offset_path0` and `offset_path1`) to be of the same type (either both constants or both variables).
 This restriction has been removed: it is now possible to mix constants and variables between I and Q.
  ```
  qp = ql.QProgram()
  offset = qp.variable(label="offset", domain=ql.Domain.Voltage)
  with qp.for_loop(variable=offset, start=0, stop=1, step=0.1):
      qp.set_offset(bus="drive", offset_path0= offset, offset_path1=0.5)
      qp.set_offset(bus="drive", offset_path0=0.1, offset_path1=offset)
  ```
  [#1024](https://github.com/qilimanjaro-tech/qililab/pull/1024)

### Improvements

- Implemented a new driver for the Becker Nachrichtentechnik RSWU-SP16TR
  [#1020](https://github.com/qilimanjaro-tech/qililab/pull/1020)

- For Autocalibration database, moved `sample_name` and `cooldown` from `AutocalMeasurement` (independent experiment) to `CalibrationRun` (full calibration tree). This way the database does not include redundant information, as these variables do not change from one measurement to another, only in different calibration runs.
  [#1053](https://github.com/qilimanjaro-tech/qililab/pull/1053)

- Added sequence run table to measurements database. This table works similar to calibration run and is intended to store a series of experiment runs one after the other. Added `add_sequence_run` to database manager to operate it. Also modified the quibit index on the autocalibration database from integer to string to take into account two qubit gate experiments.
  [#1070](https://github.com/qilimanjaro-tech/qililab/pull/1070)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
