# Release dev (development release)

### New features since last release
- Hardware Loop over the time domain has been implemented for Qblox backend in `QProgram`.
This allows sweeping wait times entirely in hardware, eliminating the need of software loops (which require uploading multiple Q1ASM).
The implementation leverages the different Q1ASM jump instructions to ensure correct execution of the `QProgram` sync operation.

- Variable expressions for time domain
Variable expressions are now supported in `QProgram` for the time domain.
The supported formats are given in ns: 
    - `constant + time variable`
    - `time variable + constant`
    - `constant - time variable`
    - `time variable - constant`

Code example:
```
qp = QProgram()
duration = qp.variable(label="time", domain=Domain.Time)
with qp.for_loop(variable=duration, start=100, stop=200, step=10):
  qp.wait(bus="drive", duration)
  qp.sync()
  qp.wait(bus="drive", duration - 50)
```
  [#950](https://github.com/qilimanjaro-tech/qililab/pull/950)

- QbloxDraw: Replaced the fixed qualitative palette (10 colors) with the continuous "Turbo" colorscale. Previously, plotting more than 10 buses caused an index error due to the palette’s limited size. The new implementation samples the continuous colorscale at evenly spaced positions based on the number of buses.
[#1039](https://github.com/qilimanjaro-tech/qililab/pull/1039)


- **Active reset for transmon qubits in QBlox**

  Implemented a feedback-based reset for QBlox: measure the qubit, and if it is in the \|1⟩ state apply a corrective DRAG pulse; if it is already in \|0⟩ (ground state), do nothing. This replaces the relaxation time at the end of each experiment with a much faster, conditional reset.
  This has been implemented as: **`qprogram.qblox.measure_reset(bus: str, waveform: IQPair, weights: IQPair, control_bus: str, reset_pulse: IQPair, trigger_address: int = 1, save_adc: bool = False)`** 

  It is compiled by the QBlox compiler as:
    1. `latch_rst 4` on the control_bus
    2. play readout pulse 
    3. acquire
    4. sync the readout and control buses
    5. wait 400 ns on the control bus (trigger-network propagation)
    6. `set_conditional(1, mask, 0, duration of the reset pulse)` → enable the conditional
    7. Play the reset pulse on the control bus
    8. `set_conditional(0, 0, 0, 4)` → disable the conditional  
    For the control bus, `latch_en 4` is added to the top of the Q1ASM to enable trigger latching.
  
  `MeasureResetCalibrated` has been implemented to enable the use of active reset with a calibration file. 
  After retrieving the waveforms and weights from the calibration file, the measure reset can be called with: **`qprogram.qblox.measure_reset(bus='readout_bus', waveform='Measure', weights='Weights', control_bus='drive_bus', reset_pulse='Drag')`**. Unlike other methods, this one does not allow a mix of calibrated and non-calibrated parameters is not allowed. This method requires the calibration file to be used consistently across `waveform`, `weight`, and `reset_pulse`; either for all three or for none. An error is raised if this condition is not met.

  Notes:
    - The 400 ns wait inside `measure_reset` is the propagation delay of the Qblox trigger network. This figure is conservative as the official guideline is 388ns.
    - Users may supply any IQPair for the reset_pulse, though DRAG pulses are recommended to minimize leakage.
    - After `measure_reset`, users should insert a further wait as needed to allow the readout resonator to ring down before subsequent operations.
    - On compilation, `cluster.reset_trigger_monitor_count(address)` is applied to zero the module’s trigger counter. And the qcodes parameters required to set up the trigger network are implemented by the QbloxQRM class.
    - The Qblox Draw class has been modified so that `latch_rst` instructions are interpreted as a `wait`, and all `set_conditional` commands are ignored.
[#955](https://github.com/qilimanjaro-tech/qililab/pull/955)
[#1042](https://github.com/qilimanjaro-tech/qililab/pull/1042)

- Introduced `electrical_delay` as a new setting for the E5080b VNA driver. It is a pure software setting to be used in autoplotting and not a physical parameter of the device.
[#1037](https://github.com/qilimanjaro-tech/qililab/pull/1037)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

- Added the return typings and missing docstring elements for the DatabaseManager class.
  [#1036](https://github.com/qilimanjaro-tech/qililab/pull/1036)

### Bug fixes

- QbloxDraw: Variable offsets can now be plotted.
[#1049](https://github.com/qilimanjaro-tech/qililab/pull/1049)
