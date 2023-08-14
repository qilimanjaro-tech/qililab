# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Delete `Schema` class from `Platform` and `RuncardSchema` classes (and from the rest of qililab).

  Also `RuncardSchema` is now called simply `Runcard` (since its the class that maps our runcard files).

  This PR brings importants simplifications to the full qililab structure, now the runcard will have the following structure:

  ```yaml
  name: "str: name of platform"

  device_id: "in: device id of platform"

  gates_settings:   # Old `settings`` without name & device_id
    ...

  chip:
    ...

  buses:
    ...

  instruments:
    ...

  instrument_controllers:
    ...
  ```

  instead than the previous:

  ```yaml
  settings:
    name: "str: name of platform"
    device_id: "int: device id of platform "
    ...

  schema:   # Schema disappears from the platform.
    chip:
      ...

    buses:
      ...

    instruments:
      ...

    instrument_controllers:
      ...
  ```

  Notice also how `settings` (and his respective class `PlatformSettings`) has changed to `gates_settings` (and the class to `GatesSettings` having the runcard string and the class the same name now, before they didn't).

  [#475](https://github.com/qilimanjaro-tech/qililab/pull/475)
  [#505](https://github.com/qilimanjaro-tech/qililab/pull/505)

- Simplify circuit gate to pulse transpilation.
  Previous hardware gates are removed. Now gates can be defined in the runcard as a list of
  `GateEvent` items with bus, wait time (optional) and pulse information. This allows more
  customization and freedom of what a certain gate does. The gate will be transpiled as long
  as the circuit gate's name and qubits match those of the gate in the runcard.
  An example of a custom gate for the circuit X gate at qubit 0 and a CZ gate at (0,1)

  ```yml
  X(0):
  - bus: drive_line_q0_bus  # alias of the bus
    wait_time: 200
    pulse:
      amplitude: 0.5
      phase: 0
      duration: 200
      frequency: 0
      shape:
        name: drag
        drag_coefficient: 1
        num_sigmas: 2
  - bus: flux_line_q0_bus  # alias of the bus
    pulse:
      amplitude: 1.0
      phase: 0
      duration: 200
      frequency: 0
      shape:
        name: rectangular

  CZ(0,1):
  - bus: flux_line_q0_bus  # park pulse
    pulse:
      amplitude: 0.5
      phase: 0
      duration: 241
      frequency: 0
      shape:
        name: rectangular
  - bus: flux_line_q1_bus  # snz
    wait_time: 40 # wait 40ns after start of the park pulse
    pulse:
      amplitude: 1
      phase: 0
      duration: 201
      frequency: 0
      shape:
        name: snz
        b: 0.5
        t_phi: 1
  ```

  Experiments can access `GateEvent` items by using the gate and qubit `alias` like previously
  and adding `_item` to access a `GateEvent` that is not the first event of the gate.
  For example, `set_parameter(parameter='amplitude', value=0.8, alias='X(0)')` will set the amplitude
  in the gate setting above from 0.5 to 0.8. This is equivalent to `alias='X(0)_0'`. However
  `alias='X(0)_1'` sets instead the amplitude of the second event (`bus=flux_line_q0_bus`) from
  1.0 to 0.8
  [#472](https://github.com/qilimanjaro-tech/qililab/pull/472)

- Rename Experiment and CircuitExperiment classes and dependencies:
  This branch renames the Experiment class to BaseExperiment and CircuitExperiment to Experiment.
  [#482](https://github.com/qilimanjaro-tech/qililab/pull/482)

- Add a new Factory for the Buses and registered the current ones
  [#487](https://github.com/qilimanjaro-tech/qililab/pull/487)

- Add the NEW_DRIVERS flag to choose between old and new instruments and bus drivers.
  [#486](https://github.com/qilimanjaro-tech/qililab/pull/486)

- Add a new Factory for the InstrumentDrivers and registered the current ones
  [#473](https://github.com/qilimanjaro-tech/qililab/pull/473)

- Add interfaces and drivers for Flux bus:
  This PR brings the qililab implementation of the Flux bus driver and unittests.
  [#469](https://github.com/qilimanjaro-tech/qililab/pull/469)

- Add ReadoutBus class.
  [#465](https://github.com/qilimanjaro-tech/qililab/pull/465)

- Fix: check whether cluster has submodules not present at init time.
  [#477](https://github.com/qilimanjaro-tech/qililab/pull/477)

- Add interfaces and drivers for Voltage and Current sources:
  This PR brings the qililab implementation of the Keithly2600 and Yokowaga QCodes drivers and unittests.
  [#438](https://github.com/qilimanjaro-tech/qililab/pull/438)

- Fix: add acquisitions and weights to Sequencer QRM
  [#461](https://github.com/qilimanjaro-tech/qililab/pull/461)

- Add DriveBus and its interface for the new bus structure.
  [457](https://github.com/qilimanjaro-tech/qililab/pull/457)

- Add QProgram for developing quantum programs in the bus level, the operations `Play`, `Sync`, `Wait`, `Acquire`, `SetGain`, `SetOffset`, `SetFrequency`, `SetPhase`, `ResetPhase`, and the iteration blocks `AcquireLoop` and `Loop`.
  [452](https://github.com/qilimanjaro-tech/qililab/pull/452)

- Add QBloxCompiler for compiling QProgram into QPySequence.
  [481](https://github.com/qilimanjaro-tech/qililab/pull/481)

- Add waveforms for the new QProgram
  [456](https://github.com/qilimanjaro-tech/qililab/pull/456)

- Add interface for Voltage and Current sources
  [#448](https://github.com/qilimanjaro-tech/qililab/pull/448)

- New AWG Interface + SequencerQCM, Pulsar, QCM-QRM drivers
  [#442](https://github.com/qilimanjaro-tech/qililab/pull/442)

- New Digitiser interface + SequencerQRM driver
  [#443](https://github.com/qilimanjaro-tech/qililab/pull/442)

- Add interface for the Attenuator.
  This is part of the "Promoting Modular Autonomy" epic.
  [#432](https://github.com/qilimanjaro-tech/qililab/pull/432)

- Added new drivers for Local Oscillators inheriting from QCoDeS drivers and Local Oscillator interface.
  This is part of the "Promoting Modular Autonomy" epic.
  [#437](https://github.com/qilimanjaro-tech/qililab/pull/437)

- Add qcodes_contrib_drivers (0.18.0) to requierements
  [#440](https://github.com/qilimanjaro-tech/qililab/pull/440)

- Update qcodes to latest current version (0.38.1)
  [#431](https://github.com/qilimanjaro-tech/qililab/pull/431)

- Added hotfix for bus delay issue from Hardware:
  This fix adds a delay for each pulse on a bus
  [#439](https://github.com/qilimanjaro-tech/qililab/pull/439)

- Added `T1` portfolio experiment
  [#409](https://github.com/qilimanjaro-tech/qililab/pull/409)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- Added `T2Echo` portfolio experiment
  [#415](https://github.com/qilimanjaro-tech/qililab/pull/415)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- The `Experiment` class has been changed to support a more general definition of experiment by removing the
  `circuits` and `pulse_schedules`. A new class `CircuitExperiment` inherits from the new `Experiment` class has the previous attributes and all the functionality the old `Experiment` had.

  ```python
  experiment = Experiment(platform=platform, options=options)
  experiment_2 = CircuitExperiment(platform=platform, options=options, circuits=[circuit])
  ```

  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

- Added `threshold_rotation` parameter to `AWGADCSequencer`. This adds a new parameter to the runcard of sequencers of that type, QRM sequencers in the case of Qblox. This value is an angle expressed in degrees from 0.0 to 360.0.

  ```yml
  awg_sequencers:
    - identifier: 0
      chip_port_id: 1
      intermediate_frequency: 1.e+08
      weights_path0: [0.98, ...]
      weights_path1: [0.72, ...]
      weighed_acq_enabled: true
      threshold: 0.5
      threshold_rotation: 45.0 # <-- new line
  ```

  [#417](https://github.com/qilimanjaro-tech/qililab/pull/417)

### Improvements

- Add `ForLoop` iteration method to QProgram.
  [481](https://github.com/qilimanjaro-tech/qililab/pull/481)

- Add `Parallel` block to QProgram to allow parallel loops, and compilation support to QBloxCompiler.
  [496](https://github.com/qilimanjaro-tech/qililab/pull/496)

- Allow CZ gates to use different pulse shapes
  [#406](https://github.com/qilimanjaro-tech/qililab/pull/406)

- Add support for the `Wait` gate

- Addeds support for the `Wait` gate
  [#405](https://github.com/qilimanjaro-tech/qililab/pull/405)

- Added support for `Parameter.Gate_Parameter` in `experiment.set_parameter()` method. In this case, alias is a, convertable to integer, string that denotes the index of the parameter to change, as returned by `circuit.get_parameters()` method.
  [#404](https://github.com/qilimanjaro-tech/qililab/pull/404)

### Breaking changes

- Old scripts using `Experiment` with circuits should be changed and use `CircuitExperiment` instead.
  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

### Deprecations / Removals

### Documentation

### Bug fixes