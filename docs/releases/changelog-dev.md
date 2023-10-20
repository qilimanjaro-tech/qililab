# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Changed gate settings serialization so that fields with None values are not in the resulting dictionary
  [#562](https://github.com/qilimanjaro-tech/qililab/pull/562)

- Update qiboconnection to 0.12.0
  [#559](https://github.com/qilimanjaro-tech/qililab/pull/559)

- Added phase correction for CZ gates to the optimize step of translate circuit in `qililab.transpiler.transpiler`. Gates now can accept an optional dicionary with additional settings.
  As an example, the CZ phase correction can be added at options for each qubit:

  ```yml
  CZ(0,2):
  - bus: flux_line_q2_bus
    pulse:
      amplitude: 1.0
      phase: 0
      duration: 101
      shape:
        name: snz
        t_phi: 1
        b: 0.5
      options:
        q0_phase_correction: 0.1
        q2_phase_correction: 0.2
  ```

  The default value for the `optimize` flag in qililab.transpiler.transpiler.translate_circuit has been changed from `False` to `True`

  [#552](https://github.com/qilimanjaro-tech/qililab/pull/552)

- build_platform() has been extended: [#533](https://github.com/qilimanjaro-tech/qililab/pull/533)

  Now appart from passing the runcard YAML file path, you can directly pass an already build dictionary.

  Also the argument has changed names from `path` to `runcard`.

- Buses serialization have been implemented: [#515](https://github.com/qilimanjaro-tech/qililab/pull/515)

  When printing the runcard, in the buses part we will now have the normal Buses serialization, plus the parameters of the instruments associated to that bus, with the `to_dict/from_dict` methods.\`

  Also the serialization includes using the `set/get_params` for setting/getting the instruments params.

- Distorsions and PulseShapes have been improved: [#512](https://github.com/qilimanjaro-tech/qililab/pull/512)

  They now work for `amplitude=0`, and for negative and `snz` envelopes (both positive and negatives)

  It now also adds the `norm_factor` parameter for manual normalization to all the distortions (previously only in the lfilter distortion)

  And finally we also have added the option to skip the automatic normalization that we do, setting the parameter `auto_norm` to `False`, (defaults to `True`).

  Plus, added a lots of tests and documentation to both classes.

- Fixed bug which did not allow gaussian waveforms to have amplitude 0
  [#471](https://github.com/qilimanjaro-tech/qililab/pull/471)

- Delete `Schema` class from `Platform` and `RuncardSchema` classes (and from the rest of qililab).

  Also `RuncardSchema` is now called simply `Runcard` (since its the class that maps our runcard files).

  This PR brings importants simplifications to the full qililab structure, now the runcard will have the following structure:

  ```yaml
  name: ...

  device_id: ...

  gates_settings:   # Old `settings` without name & device_id
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
    name: ...
    device_id: ...
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

- The `Chip` class now uses the `alias` of each node to define node connections.
  [#494](https://github.com/qilimanjaro-tech/qililab/pull/494)

  Before:

  ```yaml
  chip:
  nodes:
    - name: qubit
      alias: qubit_0
      id_: 0
      qubit_index: 0
      frequency: 4.92e+09
      nodes: [2, 10, 20, 30]
  ```

  Now:

  ```yaml
  chip:
  nodes:
    - name: qubit
      alias: qubit_0
      qubit_index: 0
      frequency: 4.92e+09
      nodes: [qubit_2, resonator_q0, drive_line_q0, flux_line_q0]
  ```

- `ql.execute` now accepts a list of circuits!
  [#549](https://github.com/qilimanjaro-tech/qililab/pull/549)

### Breaking changes

- Old scripts using `Experiment` with circuits should be changed and use `CircuitExperiment` instead.
  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

### Deprecations / Removals

- `id` and `category` attributes have been removed from `qililab`.
  [#494](https://github.com/qilimanjaro-tech/qililab/pull/494)

### Documentation

- Documentation for the Chip module: [#553] (https://github.com/qilimanjaro-tech/qililab/pull/553)

  Includes documentation for all public features of the Chip module

- Documentation for the Pulse module: [#532](https://github.com/qilimanjaro-tech/qililab/pull/532)

  Includes documentation for all public features of the Pulse module

- Added documentation for platform module and the tutorial sections of Platform and Runcards: [#531](https://github.com/qilimanjaro-tech/qililab/pull/531/files)

### Bug fixes

- Avoid creating empty sequences for buses that are no flux lines and do for flux ones that do not have any AWG instrument.
  [#556](https://github.com/qilimanjaro-tech/qililab/pull/bug-557)

- The `threshold` and `threshold_rotation` parameters of a `QbloxQRM` can now be set using `Platform.set_parameter`.
  [#534](https://github.com/qilimanjaro-tech/qililab/pull/534)

- The `QbloxQRMRF` and `QbloxQCMRF` do not save an empty list for the parameter `out_offsets` in the saved runcard.
  [#565](https://github.com/qilimanjaro-tech/qililab/pull/565)

- The `save_platform` now saves in the yaml file float values with the same precision as in the `Platform` object.
  [#565](https://github.com/qilimanjaro-tech/qililab/pull/565)
