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

- Changed internal structure of waveform generation on the qblox compiler.
Added a check in the platform for QCM and QRM modules with only one channel.
Now whenever a single waveform is given instead of giving this waveform to I and creating an empty Q, it checks first how many channels does it have based on platform:
  - If it has 2 channels the behavior is the same (waveform to I and an empty Q)
  - If it has 1 channel, I and Q are identical waveforms and register as one single waveform (effectively doubling the Q1ASM waveform compilation available size and setting the correct amplitude). If the user gives an IQPair regardless, the behavior remains unchanged and a Q wave will be saved in memory but never sent through the machine.

This check is automatic and requires no input from the user aside from setting the runcard correctly.
  [#1076](https://github.com/qilimanjaro-tech/qililab/pull/1076)

- Added a `data_folder` option to `get_db_manager` to overwrite other base paths generated.

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- [BUG] - VNA E5080B Driver. Enum Parameters were passing the entire Enum to the device causing an error when setting the parameter. Now the value of the Enum is passed to the device.
  [#1072](https://github.com/qilimanjaro-tech/qililab/pull/1072)

- Calibration file: The `with_calibration` method in `qprogram` was not storing the needed information to import blocks, this information is now being stored.
  The `insert_block` method in `structured_qprogram` has been modified such that the block is flattened, hence each element is added separately, rather than adding the block. Adding the block directly was causing problems at compilation because adding twice in a single `qprogram` the same block meant they shared the same UUID.
  [#1050](https://github.com/qilimanjaro-tech/qililab/pull/1050)

- QbloxDraw: Fixed two acquisition-related bugs:.

  1. Acquisition-only programs are now displayed correctly.
  1. Acquisition timing issues caused by wait instructions have been fixed.
     [#1051](https://github.com/qilimanjaro-tech/qililab/pull/1051)

- QbloxDraw: Variable offsets can now be plotted.
  [#1049](https://github.com/qilimanjaro-tech/qililab/pull/1049)

- Removed threading for `ExperimentExecutor()`. This feature caused a deadlock on the execution if any error is raised inside it (mainly involving the ExperimentsResultsWriter). The threading has been removed as it was only necessary for parallel time tracking.
[#1055](https://github.com/qilimanjaro-tech/qililab/pull/1055)

- Fixed conflict with base path not being unique for parallel qprogram executions in StreamArray. To fix it, the path now includes the target index whenever there is one, which is the case for parallel executions. For any other existing case the behavior remains the same.
  [#1074](https://github.com/qilimanjaro-tech/qililab/pull/1074)
