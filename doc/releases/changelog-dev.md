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

- Added support for changing operation's settings.

  ```python
  experiment.set_parameter(alias="Measure", parameter=Parameter.DURATION, value=1000)
  ```

  [#287](https://github.com/qilimanjaro-tech/qililab/pull/287)

- Added support for looping over the values of a specific group of operations in the circuit. The group is identified by the alias set when added the operation in the circuit. If more than one operations have the same alias, their values will change in sync.

  Example:

  ```python
  circuit = Circuit(1)
  circuit.add(0, X())
  circuit.add(0, Wait(t=0), alias="wait_operation")
  circuit.add(0, X())
  circuit.add(0, Wait(t=0), alias="wait_operation")
  circuit.add(0, Measure())

  loop = Loop(
      alias="wait_operation.t",
      parameter=Parameter.OPERATION_PARAMETER,
      values=np.linspace(0, 1000, 10),
  )
  ```

  [#287](https://github.com/qilimanjaro-tech/qililab/pull/287)

### Improvements

- Arbitrary mapping of I/Q channels to outputs is now possible with the Qblox driver. When using a mapping that is not
  possible in hardware, the waveforms of the corresponding paths are swapped (in software) to allow it. For example,
  when loading a runcard with the following sequencer mapping a warning should be raised:

  ```yaml
  awg_sequencers:
  - identifier: 0
    output_i: 1
    output_q: 0
  ```

  ```pycon
  >>> platform = build_platform(name=runcard_name)
  [qililab] [0.16.1|WARNING|2023-05-09 17:18:51]: Cannot set `output_i=1` and `output_q=0` in hardware. The I/Q signals sent to sequencer 0 will be swapped to allow this setting.
  ```

  Under the hood, the driver maps `path0 -> output0` and `path1 -> output1`.
  When applying an I/Q pulse, it sends the I signal through `path1` and the Q signal through `path0`.

### Breaking changes

### Deprecations / Removals

- Remove the `awg_iq_channels` from the `AWG` class. This mapping was already done within each sequencer.
  [#323](https://github.com/qilimanjaro-tech/qililab/pull/323)

### Documentation

### Bug fixes
