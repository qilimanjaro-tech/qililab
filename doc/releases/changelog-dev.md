# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added new methods to `CircuitTranspiler` class for transpiling `Circuit` to `PulseSchedule`. The complete transpilation flow, that can be run by calling `transpile()` method, consists of the following steps:

  1: \_calculate_timings()
  2: \_remove_special_operations()
  3: \_transpile_to_pulse_operations()
  4: \_generate_pulse_schedule()

  The `_calculate_timings()` method annotates operations in the circuit with timing information by evaluating start and end times for each operation. The `_remove_special_operations()` method removes special operations (Barrier, Wait, Passive Reset) from the circuit after the timings have been calculated. The `_transpile_to_pulse_operations()` method then transpiles the quantum circuit operations into pulse operations, taking into account the calculated timings. The `_generate_pulse_schedule()` method produces the equivalent `PulseSchedule`. Example usage:

  ```python
  # create the transpiler
  transpiler = CircuitTranspiler(settings=platform.settings)

  # calculate timings
  circuit_ir1 = transpiler._calculate_timings(circuit)

  # remove special operations
  circuit_ir2 = transpiler._remove_special_operations(circuit_ir1)

  # transpile operations to pulse operations
  circuit_ir3 = transpiler._transpile_to_pulse_operations(circuit_ir2)

  # transpile to PulseSchedule
  pulse_schedule = transpiler._generate_pulse_schedule(circuit_ir3)

  # Alternatively, if you don't need inspection of intermediate representations you can run all steps with transpile
  pulse_schedule = transpiler.transpile(circuit)
  ```

  [#267](https://github.com/qilimanjaro-tech/qililab/pull/267)

- Experiment can now accept both Qibo circuits and Qililab circuits.
  [#267](https://github.com/qilimanjaro-tech/qililab/pull/267)

- Added `get_port_from_qubit_idx` method to `Chip` class. This method takes the qubit index and the line type as arguments and returns the associated port.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

- Added `pulse.pulse_distortion` package, which contains a module `pulse_distortion.py` with the base class to distort envelopes in `PulseEvent`, and two modules `bias_tee_correction.py` and `exponential_decay_correction.py`, each containing examples of distortion child classes to apply. This new feature can be used in two ways, directly from the class itself:

  ```python
  distorted_envelope = BiasTeeCorrection(tau_bias_tee=1.0).apply(original_envelope)
  ```

  or from the class PulseEvent (which ends up calling the previous one):

  ```python
  pulse_event = PulseEvent(
      pulse="example_pulse",
      start_time="example_start",
      distortions=[
          BiasTeeCorrection(tau_bias_tee=1.0),
          BiasTeeCorrection(tau_bias_tee=0.8),
      ],
  )
  distorted_envelope = pulse_event.envelope()
  ```

  This would apply them like: BiasTeeCorrection_0.8(BiasTeeCorrection_1.0(original_pulse)), so the first one gets applied first and so on...
  (If you write their composition, it will be in reverse order respect the list)

  Also along the way modified/refactored the to_dict() and from_dict() and envelope() methods of PulseEvent, Pulse, PulseShape... since they had some bugs, such as:

  - the dict() methods edited the external dictionaries making them unusable two times.
  - the maximum of the envelopes didn't correspond to the given amplitude.

  [#294](https://github.com/qilimanjaro-tech/qililab/pull/294)

- The `QbloxQCMRF` module has been added. To use it, please use the `QCM-RF` name inside the runcard:

  ```yaml
  - name: QCM-RF
    alias: QCM-RF0
    id_: 2
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    out0_lo_freq: 3700000000  # <-- new line
    out0_lo_en: true  # <-- new line
    out0_att: 10  # <-- new line
    out0_offset_path0: 0.2  # <-- new line
    out0_offset_path1: 0.07  # <-- new line
    out1_lo_freq: 3900000000  # <-- new line
    out1_lo_en: true  # <-- new line
    out1_att: 6  # <-- new line
    out1_offset_path0: 0.1  # <-- new line
    out1_offset_path1: 0.6  # <-- new line
    awg_sequencers:
      ...
  ```

  [#327](https://github.com/qilimanjaro-tech/qililab/pull/327)

- The `QbloxQRMRF` module has been added. To use it, please use the `QRM-RF` name inside the runcard:

  ```yaml
  - name: QRM-RF
    alias: QRM-RF0
    id_: 0
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    out0_in0_lo_freq: 3000000000  # <-- new line
    out0_in0_lo_en: true  # <-- new line
    out0_att: 34  # <-- new line
    in0_att: 28  # <-- new line
    out0_offset_path0: 0.123  # <-- new line
    out0_offset_path1: 1.234  # <-- new line
    acquisition_delay_time: 100
    awg_sequencers:
      ...
  ```

  [#330](https://github.com/qilimanjaro-tech/qililab/pull/330)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
