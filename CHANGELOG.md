# CHANGELOG

## 0.24.3 (2024-03-05)

### New features since last release

- Introduced a new parameter, `disable_autosync`, to the `QProgram` constructor. This parameter allows users to control the automatic synchronization behavior of loops within their quantum programs. By default, the parameter is set to `False`, enabling the compiler to automatically insert synchronization operations at the conclusion of each loop. Users have the option to set `disable_autosync` to `True` to indicate that they prefer to manage loop timing manually. This feature is particularly useful for operations on Qblox hardware, due to its constraints on dynamic synchronization. It's important to note that Quantum Machines will disregard this setting and adhere to the default synchronization behavior.
  [#694](https://github.com/qilimanjaro-tech/qililab/pull/694)

### Breaking changes

- The unit of measurement for phases within QProgram has been updated from degrees to radians.
  [#695](https://github.com/qilimanjaro-tech/qililab/pull/695)

### Bug fixes

- Resolved an issue encountered during the retrieval of results from QProgram executions on Qblox hardware, where acquisition data from other sequencers would unintentionally be deleted.
  [#691](https://github.com/qilimanjaro-tech/qililab/pull/691)

## 0.23.3 (2024-02-19)

### Bug fixes

- Fixed an issue when serializing / deserializing a QProgram so results are returned in a standard results class.
  [#688](https://github.com/qilimanjaro-tech/qililab/pull/688)

## 0.23.2 (2024-02-13)

### Bug fixes

- Fixed an issue when serializing / deserializing a QProgram that contained an Arbitrary waveform or a DRAG pulse.
  [#686](https://github.com/qilimanjaro-tech/qililab/pull/686)

## 0.23.1 (2024-02-09)

### Bug fixes

- Fixes an equality issue of QProgram's variables that resulted in a slightly different QProgram when serializing and then deserializing.
  [#684](https://github.com/qilimanjaro-tech/qililab/pull/684)

## 0.23.0 (2024-02-09)

### New features since last release

- Allow execution of `QProgram` through `platform.execute_qprogram` method for Quantum Machines hardware.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Allow multiple measurements of the same qubit in a single circuit. Also allow measurements in the middle of a circuit.
  [#674](https://github.com/qilimanjaro-tech/qililab/pull/674)

- Wait times longer than 2\*\*16-4 (QBLOX maximum wait time in a Q1ASM wait instruction) are now allowed in the middle of
  a circuit.
  [#674](https://github.com/qilimanjaro-tech/qililab/pull/674)

- Add method to get sequencer channel id from qubit index and bus alias
  [#678](https://github.com/qilimanjaro-tech/qililab/pull/678)

### Improvements

- Added `bus_mapping` parameter in `QbloxCompiler.compile` method to allow changing the bus names of the compiled output.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Improved `QuantumMachinesCluster` instrument functionality.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Improved execution times of `QProgram` when used inside a software loop by using caching mechanism.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Added `DictSerializable` protocol and `from_dict` utility function to enable (de)serialization (from)to dictionary for any class.
  [#659](https://github.com/qilimanjaro-tech/qililab/pull/659)

- Added method to get the QRM `channel_id` for a given qubit.
  [#664](https://github.com/qilimanjaro-tech/qililab/pull/664)

- Added Domain restrictions to `Drag` pulse, `DragCorrection` waveform and `Gaussian` waveform.
  [#679](https://github.com/qilimanjaro-tech/qililab/pull/679)

- Compilation for pulses is now done at platform instead of being delegated to each bus pointing to an awg instrument. This allows easier
  communication between `pulse_bus_schedules` so that they can be handled at the same time in order to tackle more complex tasks which were
  not possible otherwise. It also decouples, to a great extent, the instruments and instrument controllers (hardware) from higher level processes more typical of quantum control, which are involved in the pulse compilation to assembly program steps.
  [#651](https://github.com/qilimanjaro-tech/qililab/pull/651)

- Changed save and load methods using `PyYAML` to `ruamel.YAML`.
  [#661](https://github.com/qilimanjaro-tech/qililab/pull/661)

- Qprogram's qblox compiler now allows iterations over variables even if these variables do nothing. (eg. iterate over nshots)
  [#666](https://github.com/qilimanjaro-tech/qililab/pull/666)

### Bug fixes

- Added the temporary parameter `wait_time` to QProgram's `play` method. This allows the user to emulate a `time_of_flight` duration for measurement until this is added as a setting in runcard.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Fixed issue with Yokogawa GS200 instrument, that raised an error during initial_setup when the instrument's output was on.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

## 0.22.2 (2024-01-04)

### New features since last release

- Added Yokogawa `GS200` instrument and associated istrument controller.
  [#619](https://github.com/qilimanjaro-tech/qililab/pull/619)

- Added QDevil `QDAC-II` instrument and associated istrument controller.
  [#634](https://github.com/qilimanjaro-tech/qililab/pull/634)

- `set_parameter()` can now be used without being connected to the instruments.
  [#647](https://github.com/qilimanjaro-tech/qililab/pull/647)

### Improvements

- `QuantumMachinesCluster` can be created by translating the runcard into the equivelant QUA config dictionary. `initial_setup`, `turn_on` and `turn_off` methods have been edited to properly instatiate and calibrate the instrument.
  [#620](https://github.com/qilimanjaro-tech/qililab/pull/620)

### Breaking changes

- `QuantumMachinesManager` has been renamed to `QuantumMachinesCluster` and `QMMController` to `QuantumMachinesClusterController`.
  [#620](https://github.com/qilimanjaro-tech/qililab/pull/620)

### Bug fixes

- Fixed [bug #653](https://github.com/qilimanjaro-tech/qililab/issues/635), where saving the runcard would not include the reset parameter in the instrument controllers.
  [#653](https://github.com/qilimanjaro-tech/qililab/pull/653)

## 0.22.1 (2023-12-05)

### Bug fixes

- Fixed [bug #635](https://github.com/qilimanjaro-tech/qililab/issues/635), where trying to read/set the Intermediate
  frequency parameter was failing for Qblox RF modules.
  [#635](https://github.com/qilimanjaro-tech/qililab/pull/635)

## 0.22.0 (2023-11-27)

### New features since last release

- Added real time results saving capability.
  [#598](https://github.com/qilimanjaro-tech/qililab/pull/598)

- Raise an error if a user requests to run a circuit that is longer than `repetition_duration`
  [#621](https://github.com/qilimanjaro-tech/qililab/pull/621)

- Add parameter to the SLURM magic method to configure the time limit of a job.
  [#608](https://github.com/qilimanjaro-tech/qililab/pull/608)

- Add magic method to run python code as slurm jobs from Jupyter Notebooks.
  [#600](https://github.com/qilimanjaro-tech/qililab/pull/600)

- Implemented `QuantumMachinesCompiler` class to compile QPrograms to QUA programs.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Implemented `platform.execute_qprogram()` method to execute a qprogram on Qblox hardware.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Added the two main classes need for automatic-calibration, `CalibrationController` and `CalibrationNode`
  [#554](https://github.com/qilimanjaro-tech/qililab/pull/554)

- Added the driver for Quantum Machines Manager and a new QuantumMachinesResult class to handle Quantum Machines instruments.
  [#568](https://github.com/qilimanjaro-tech/qililab/pull/568)

- Implemented the `QuantumMachinesMeasurementResult` class to store data acquired from a single instrument.
  [#596](https://github.com/qilimanjaro-tech/qililab/pull/596)

### Improvements

- Improved the UX for circuit transpilation by unifying the native gate and pulse transpiler under one `CircuitTranspiler` class, which has 3 methods:

  - `circuit_to_native`: transpiles a qibo circuit to native gates (Drag, CZ, Wait, M) and optionally RZ if optimize=False (optimize=True by default)
  - `circuit_to_pulses`: transpiles a native gate circuit to a `PulseSchedule`
  - `transpile_circuit`: runs both of the methods above sequentially
    `Wait` gate moved from the `utils` module to `circuit_transpilation_native_gates`
    [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

- Added `infinite_loop()` method to QProgram.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Added `measure()` method to QProgram.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Various improvements in the compilation flow of `QbloxCompiler`.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Updated `qm-qua` library to latest `1.1.5.1`.
  [#596](https://github.com/qilimanjaro-tech/qililab/pull/596)

### Breaking changes

- Changed `resolution` parameter of waveforms' `envelope()` method to integer.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Changed the way variables work within a QProgram. Variables are now instantiated based on the physical domain they affect.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

### Deprecations / Removals

- Removed the park gate since it is no longer needed
  [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

### Bug fixes

- Fixed [bug #626](https://github.com/qilimanjaro-tech/qililab/issues/626), where a regression bug was introduced by adding empty schedules to all flux buses, not only the ones with an AWG registered instrument, as it was intended originally.
  [#628](https://github.com/qilimanjaro-tech/qililab/pull/628)

- Fixed [bug #579](https://github.com/qilimanjaro-tech/qililab/issues/579), were now all `yaml.dumps` are done with [ruamel](https://yaml.readthedocs.io/en/latest/#changelog), for not losing decimals precisons, and also following the previous bug due to the elimination of `ruamel.yaml.round_trip_dump`, the version of ruamel in qililab got fixed, and imports where rewritten for more clarity
  [#577](https://github.com/qilimanjaro-tech/qililab/pull/578)

## 0.21.1 (2023-10-31)

### New features since last release

- Enums for gate options
  [#589](https://github.com/qilimanjaro-tech/qililab/pull/589)

- Two new enums for SNZ gate
  [#587](https://github.com/qilimanjaro-tech/qililab/pull/587)

### Bug fixes

- Fixed [bug](https://github.com/qilimanjaro-tech/qililab/issues/584) where executing multiple circuits with each measuring different qubits would launch measurements for previously measured
  qubits even if those did not have measurements on the circuit currently being executed.
  [#576](https://github.com/qilimanjaro-tech/qililab/pull/576)

- [ruamel 0.18.0](https://yaml.readthedocs.io/en/latest/#changelog) eliminated `ruamel.yaml.round_trip_dump`, so we changed its usage to the recommended version:  `ruamel.yaml.YAML().dump` [#577](https://github.com/qilimanjaro-tech/qililab/pull/577)

## 0.21.0 (2023-10-20)

### New features since last release

- Changed gate settings serialization so that fields with None values are not in the resulting dictionary
  [#562](https://github.com/qilimanjaro-tech/qililab/pull/562)

- Update qiboconnection to 0.12.0
  [#559](https://github.com/qilimanjaro-tech/qililab/pull/559)

- Added phase correction for CZ gates to the optimize step of translate circuit in `qililab.transpiler.transpiler`. Gates now can accept an optional dicionary with additional settings.
  As an example, the CZ phase correction can be added at options for each qubit:

  ```yaml
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

  ```yaml
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

  ```yaml
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

- Documentation for the Chip module: \[#553\] (<https://github.com/qilimanjaro-tech/qililab/pull/553>)

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

## 0.20.0 (2023-05-26)

### New features since last release

- Added hotfixes for several issues encountered during the hackathon:
  [#413](https://github.com/qilimanjaro-tech/qililab/pull/413)

  - Save experiments flag for experiments execute method

  ```python
  # Option 1 (Default, save_experiment=True)
  experiment = Experiment(platform=platform, circuits=circuits, options=options)
  experiment.execute()

  # Option 2 (Equivalent to option 1, save_experiment=False)
  experiment = Experiment(platform=platform, circuits=circuits, options=options)
  experiment.execute(save_experiment=False)
  ```

  - Empty sequences to avoid creating repeated programs.
  - Create empty programs for all qubit flux lines to activate calibrated offsets.
  - Added method to get qubits from the chip

  ```python
  qubits = ql.Chip.qubits()
  ```

- Added to the `draw()` method the option  of specifying if you want:

  - modulation or not,
  - plot the real, iamginary, absolute or any combination of these options
  - specify the type of plotline to use, such as "-", ".", "--", ":"...
    for the classes `Experimental` and `ExecutionManager`, like:

  ```python
  # Option 1 (Default)
  figure = sample_experiment.draw(
      real=True, imag=True, abs=False, modulation=True, linestyle="-"
  )

  # Option 2 (Equivalent to option 1)
  figure = sample_experiment.draw()

  # Option 3 (something different, only plotting the envelopes without modulation)
  figure = sample_experiment.draw(modulation=False, linestyle=".")

  plt.show()
  ```

  [#383](https://github.com/qilimanjaro-tech/qililab/pull/383)

- Added `lambda_2` attribute to the `cosine.py` module containing the `Cosine` pulse_shape, modifying the previous A/2\*(1-cos(x)).
  Into a more general A/2\*(1-lambda_1*cos(phi)-lambda_2*cos(2phi)), giving a modified sinusoidal-gaussian.

  - lambda_1 cosine A/2\*(1-cos(x)): Starts at height 0 (phase=0), maximum height A (phase=pi)
    and ends at height 0 (phase=2pi). Which is a sinusoidal like gaussian.

  - lambda_2 cosine A/2\*(1-cos(2x)): Starts at height 0 (phase=0), maximum height A (phase=pi/2)
    then another height 0 in the middle at phase=pi, then another maximum height A (phase=3/2pi)
    and ends at height 0 (phase=2pi).

  For more info check the docstring and the following references:

  - Supplemental material B. "Flux pulse parametrization" at \[<https://arxiv.org/abs/1903.02492%5C%5D>\],
  - OPTIMAL SOLUTION: SMALL CHANGE IN θ at \[<https://arxiv.org/abs/1402.5467%5C%5D>\]

  [#385](https://github.com/qilimanjaro-tech/qililab/pull/385)

- Added user integration for `pulse_distortions`. Now they can be used writing them in the Buses of the runcards:

  ```python
  buses:
    - id_: 0
      category: bus
      alias: feedline_bus
      system_control:
        id_: 0
        name: readout_system_control
        category: system_control
        instruments: [QRM1, rs_1]
      port: 100
      distortions: # <-- new line
        - name: bias_tee # <-- new line
          tau_bias_tee: 1.0 # <-- new line
        - name: lfilter # <-- new line
          a: [0.1, 1.1] # <-- new line
          b: [1.1, 1.3] # <-- new line
    - id_: 10
      category: bus
      alias: drive_line_q0_bus
      system_control:
        id_: 10
        name: system_control
        category: system_control
        instruments: [QCM-RF1]
      port: 10
      distortions: [] # <-- new line
  ```

  [#372](https://github.com/qilimanjaro-tech/qililab/pull/372)

- Added CZ gate support, 2 qubit gate support to `circuit_to_pulse` and corresponding definitions to the runcard.

  CZ implements a Sudden Net Zero (SNZ) pulse through the flux line as well as a parking gate (if defined in the runcard)
  to adjacent qubits with lower frequency than CZ's target qubit.
  For the parking gate, if the time is greater than the CZ pulse, the extra time is added as padding at the beginning/end
  of the pulse.
  The parameters for the CZ in the runcard are amplitude, duration *of the halfpulse*; and for the CZ's snz pulse b
  (impulse between halfpulses) and t_phi (time between halfpulses without accounting for b)

  Example:

  ```yaml
  gates:
   1:
     - name: Park
       amplitude: 1.0
       phase: 0
       duration: 103
       shape:
         name: rectangular

   (0,2):
     - name: CZ
       amplitude: 1.0
       phase:
       duration: 40
       shape:
         name: snz
         b: 0.5
         t_phi: 1
  ```

  In the example above, if qubit 1 is connected to 2 and has lower frequency, there will be an attempt to apply a parking
  pulse. If a Park gate definition is found for qubit 1, then a parking pulse will be applied.
  The total duration of the CZ gate above will be 2\*duration + t_phi + 2 = 83 (each b has 1ns duration and there are 2 bs).
  Thus the parking gate lasts for some extra 20ns which will result in 10ns 'pad time' in the parking gate before and after
  the SNZ pulse.
  Note that the order of the qubits in the CZ is important even if the gate is symmetric, because the second qubit will be
  the target for the SNZ pulse.
  [#369](https://github.com/qilimanjaro-tech/qililab/pull/369/)

- Added `cosine.py` module containing a `Cosine` child class of `pulse_shape`, which gives a sinusoidal like gaussian A/2\*(1-cos(x)).
  The shape starts at height 0 (phase=0), maximum height A (phase=pi) and ends at height 0 (phase=2pi)

  ```python
  pulse = Pulse(
      amplitude=...,
      phase=...,
      duration=...,
      frequency=...,
      pulse_shape=Cosine(),
  )
  ```

  [#376](https://github.com/qilimanjaro-tech/qililab/pull/376)

- Added `pulse.pulse_distortion.lfilter_correction.py` module, which is another child class for the `pulse.pulse_distortion` package.

  ```python
  distorted_envelope = LFilter(norm_factor=1.2, a=[0.7, 1.3], b=[0.5, 0.6]).apply(
      original_envelopes
  )
  ```

  Also adds a phase property to `PulseEvent` and implements `Factory.get` directly in the `from_dict()` method of the parent class `PulseDistortion`.

  [#354](https://github.com/qilimanjaro-tech/qililab/pull/354)

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

- The `get_bus_by_qubit_index` method of `Platform` class now returns a tuple of three buses: `flux_bus, control_bux, readout_bus`.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

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
  [#324](https://github.com/qilimanjaro-tech/qililab/pull/324)

- The versions of the `qblox-instruments` and `qpysequence` requirements have been updated to `0.9.0`
  [#337](https://github.com/qilimanjaro-tech/qililab/pull/337)

- Allow uploading negative envelopes on the `QbloxModule` class.
  [#356](https://github.com/qilimanjaro-tech/qililab/pull/356)

- The parameter `sync_en` of the Qblox sequencers is now updated automatically when uploading a program to a sequencer.
  This parameter can no longer be set using `set_parameter`.
  [#353](https://github.com/qilimanjaro-tech/qililab/pull/353)

- The Qblox RF modules now support setting their LO frequency using the generic `Parameter.LO_FREQUENCY` parameter.
  [#455](https://github.com/qilimanjaro-tech/qililab/pull/455)

### Deprecations / Removals

- Remove the `awg_iq_channels` from the `AWG` class. This mapping was already done within each sequencer.
  [#323](https://github.com/qilimanjaro-tech/qililab/pull/323)

- Remove the `get_port` method from the `Chip` class.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

### Bug fixes

- Add `_set_markers` method to the `QbloxModule` class and enable all markers. For the RF modules, this command
  enables the outputs/inputs of the instrument. We decided to enable all markers by default to be able to use them
  later if needed.
  [#361](https://github.com/qilimanjaro-tech/qililab/pull/361)

## 0.19.0 (2023-05-08)

### New features since last release

- Added Drag gate support to `circuit_to_pulse` so that Drag gates are implemented as drag pulses
  [#312](https://github.com/qilimanjaro-tech/qililab/pull/312)

- Added `experiment/portfolio/` submodule, which will contain pre-defined experiments and their analysis.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `ExperimentAnalysis` class, which contains methods used to analyze the results of an experiment.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `Rabi` portfolio experiment. Here is a usage example:

  ```python
  loop_range = np.linspace(start=0, stop=1, step=0.1)
  rabi = Rabi(platform=platform, qubit=0, range=loop_range)
  rabi.turn_on_instruments()

  bus_parameters = {Parameter.GAIN: 0.8, Parameter.FREQUENCY: 5e9}
  rabi.bus_setup(bus_parameters, control=True)  # set parameters of control bus
  x_parameters = {Parameter.DURATION: 40}
  rabi.gate_setup(x_parameters, gate="X")  # set parameters of X gate

  rabi.build_execution()
  results = rabi.run()  # all the returned values are also saved inside the `Rabi` class!
  post_processed_results = rabi.post_process_results()
  fitted_parameters = rabi.fit()
  fig = rabi.plot()
  ```

  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `FlippingSequence` portfolio experiment.
  [#245](https://github.com/qilimanjaro-tech/qililab/pull/245)

- Added `get_bus_by_qubit_index` method to the `Platform` class.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `circuit` module, which contains everything related to Qililab's internal circuit representation.

  The module contains the following submodules:

  - `circuit/converters`: Contains classes that can convert from external circuit representation to Qililab's internal circuit representation and vice versa.
  - `circuit/nodes`: Contains classes representing graph nodes that are used in circuit's internal graph data structure.
  - `circuit/operations`: Contains classes representing operations that can be added to the circuit.
    [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `Circuit` class for representing quantum circuits. The class stores the quantum circuit as a directed acyclic graph (DAG) using the `rustworkx` library for manipulation. It offers methods to add operations to the circuit, calculate the circuit's depth, and visualize the circuit. Example usage:

  ```python
  # create a Circuit with two qubits
  circuit = Circuit(2)

  # add operations
  for qubit in [0, 1]:
      circuit.add(qubit, X())
  circuit.add(0, Wait(t=100))
  circuit.add(0, X())
  circuit.add((0, 1), Measure())

  # print depth of circuit
  print(f"Depth: {circuit.depth}")

  # print circuit
  circuit.print()

  # draw circuit's graph
  circuit.draw()
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `OperationFactory` class to register and retrieve operation classes based on their names.
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `CircuitTranspiler` class for calculating operation timings and transpiling quantum circuits into pulse operations. The `calculate_timings()` method annotates operations in the circuit with timing information by evaluating start and end times for each operation. The `remove_special_operations()` method removes special operations (Barrier, Wait, Passive Reset) from the circuit after the timings have been calculated. The `transpile_to_pulse_operations()` method then transpiles the quantum circuit operations into pulse operations, taking into account the calculated timings. Example usage:

  ```python
  # create the transpiler
  transpiler = CircuitTranspiler(settings=platform.settings)

  # calculate timings
  circuit_ir1 = transpiler.calculate_timings(circuit)

  # remove special operations
  circuit_ir2 = transpiler.remove_special_operations(circuit_ir1)

  # transpile operations to pulse operations
  circuit_ir3 = transpiler.transpile_to_pulse_operations(circuit_ir2)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `QiliQasmConverter` class to convert a circuit from/to QiliQASM, an over-simplified QASM version. Example usage:

  ```python
  # Convert to QiliQASM
  qasm = QiliQasmConverter.to_qasm(circuit)
  print(qasm)

  # Parse from QiliQASM
  parsed_circuit = QiliQasmConverter.from_qasm(qasm)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Pulses with different frequencies will be automatically sent and read by different sequencers (multiplexed readout).
  [#242](https://github.com/qilimanjaro-tech/qililab/pull/242)

- Added an optional parameter "frequency" to the "modulated_waveforms" method of the Pulse and PulseEvent classes, allowing for specification of a modulation frequency different from that of the Pulse.
  [#242](https://github.com/qilimanjaro-tech/qililab/pull/242)

- Added `values` and `channel_id` attribute to the `Loop` class.
  Here is an example on how a loop is created now:

  ```python
  new_loop = Loop(alias="loop", parameter=Parameter.POWER, values=np.linspace(1, 10, 10))
  ```

  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- Gate settings can be set for each qubit individually, or tuple of qubits in case of two-qubit gates.
  Example of updated runcard schema:

  ```yaml
  gates:
    0:
      - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
      - name: X
        amplitude: 1.0
        phase: 0
        duration: 100
        shape:
          name: gaussian
          num_sigmas: 4
    1:
      - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
      - name: X
        amplitude: 1.0
        phase: 0
        duration: 100
        shape:
          name: gaussian
          num_sigmas: 4
    (0,1):
      - name: CPhase
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
  ```

  To change settings with set_parameter methods, use the alias format "GATE(QUBITs)". For example:

  ```python
  platform.set_parameter(alias="X(0)", parameter=Parameter.DURATION, value=40)
  platform.set_parameter(alias="CPhase(0,1)", parameter=Parameter.DURATION, value=80)
  ```

  [#292](https://github.com/qilimanjaro-tech/qililab/pull/292)

- Weighted acquisition is supported. The weight arrays are set as sequencer parameters `weights_i` and `weights_q`, and the weighed acquisition can be enabled setting the sequencer parameter `weighed_acq_enabled` to `true`. Note: the `integration_length` parameter will be ignored if `weighed_acq_enabled` is set to `true`, and the length of the weights arrays will be used instead.

```yaml
awg_sequencers:
  - identifier: 0
    chip_port_id: 1
    intermediate_frequency: 1.e+08
    weights_i: [0.98, ...]  # <-- new line
    weights_q: [0.72, ...]  # <-- new line
    weighed_acq_enabled: true   # <-- new line
    threshold: 0.5              # <-- new line
```

[#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

- `Result`, `Results` and `Acquisitions` classes implement the `counts` method, which returns a dictionary-like object containing the counts of each measurement based in the discretization of the instrument via the `threshold` sequencer parameter. Alternatively, the `probabilities` method can also be used, which returns a normalized version of the same counts object.

  ```pycon
  >>> counts = result.counts()
  Counts: {'00': 502, '01': 23, '10': 19, '11': 480}
  >>> probabilities = result.probabilities()
  Probabilities: {'00': 0.49023438, '01': 0.02246094, '10': 0.01855469, '11': 0.46875}
  ```

  [#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

### Improvements

- Return an integer (instead of the `Port` class) when calling `Chip.get_port`. This is to avoid using the private
  `id_` attribute of the `Port` class to obtain the port index.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- The asynchronous data handling used to save results and send data to the live plotting has been improved. Now we are
  saving the results in a queue, and there is only ONE thread which retrieves the results from the queue, sends them to
  the live plotting and saves them to a file.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

- The asynchronous data handling used to save results and send data to the live plotting has been improved.
  Previously we only had ONE active thread retrieving the results and saving them but was created and killed after processing one result of the total `Results` object. Now we are creating the thread just ONCE, so threading is handled at the `Experiment` level instead of what was done previously at the `Exution_Manager` level.
  [#298](https://github.com/qilimanjaro-tech/qililab/pull/298)

### Breaking changes

- `draw()` method of `Circuit` uses Graphviz internally. To be able to call the method Graphviz must be installed. In Ubuntu-based distros a simple `sudo apt-get install graphviz` is sufficient. For detailed installation information for your OS please consult Graphviz's [installation page](https://graphviz.org/download/).
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- `gates` property of runcard must be updated to provide a list of gate settings for each qubit individually.
  [#292](https://github.com/qilimanjaro-tech/qililab/pull/292)

### Deprecations / Removals

- The `Execution` class has been removed. Its functionality is now added to the `ExecutionManager` class.
  Please use `ExecutionManager`instead. The `ExecutionBuilder` returns now an instance of `ExecutionManager`.
  [#246](https://github.com/qilimanjaro-tech/qililab/pull/246)

- The `LoopOptions` class has been removed. It was used to create a numpy array and store this array in the `values`
  attribute which is now in the `Loop` class.
  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- The `plot_y_label` argument of the `ExperimentOptions` class has been removed.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

- All the `probabilities` methods that returned a `pandas.DataFrame` return now a `dict[str, float]`. All the methods related to the construction of such dataframes have been removed.
  [#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

### Documentation

### Bug fixes

- Fixed bug where acquisition data was not deleted when compiling the same sequence twice.
  [#264](https://github.com/qilimanjaro-tech/qililab/pull/264)

- Fixed bug where the live plotting created a new plot when using parallel loops.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

## 0.18.0 (2023-04-11)

### New features since last release

- Added `Experiment.compile` method, which return the compiled experiment for debugging purposes.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

  ```pycon
  >>> sequences = experiment.compile()
  ```

  This method returns a list of dictionaries (one dictionary per circuit executed in the experiment). Each dictionary
  contains the sequences uploaded for each bus:

  ```pycon
  >>> sequences[0]
  {'drive_line_bus': [qpysequence_1], 'feedline_input_output_bus': [qpysequence_2]}
  ```

  This experiment is using two buses (`drive_line_bus` and `feedling_input_output_bus`), which have a list of the uploaded sequences
  (in this case only 1).

  We can then obtain the program of such sequences:

  ```pycon
  >>> sequences[0]["drive_line_bus"][0]._program
  setup:
    move             1000, R0
    wait_sync        4
  average:
    reset_ph
    play             0, 1, 4
    long_wait_1:
        move             3, R1
        long_wait_1_loop:
            wait             65532
            loop             R1, @long_wait_1_loop
        wait             3400

    loop             R0, @average
  stop:
    stop
  ```

- Added support for setting output offsets of a qblox module.
  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

- Added gate to native gate transpiler. Contains method `translate_circuit` which translates a qibo.Circuit to a qibo.Circuit with
  native gates (Drag pulses, C-phase), virtual Zs and measurement gates only.
  [#244](https://github.com/qilimanjaro-tech/qililab/pull/244)

- Added optimizer for the native gate transpiler. Shifts all Z, RZ gates to the left and removes them before measurement.
  [#269](https://github.com/qilimanjaro-tech/qililab/pull/269)

### Improvements

- Added support for the execution of pulses with durations that are not multiples of 4. For this, a new
  `minimum_clock_time` attribute has been added to the runcard:

  ```yaml
  settings:
    id_: 0
    category: platform
    name: spectro_v_flux
    device_id: 9
    minimum_clock_time: 4  # <-- new line!
  ```

  When a pulse has a duration that is not a multiple of the `minimum_clock_time`, a padding of 0s is added after the pulse to make sure the next pulse falls within a multiple of 4.
  [#227](https://github.com/qilimanjaro-tech/qililab/pull/227)

- Change name `PulseScheduledBus` to `BusExecution`.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

- Separate `generate_program_and_upload` into two methods: `compile` and `upload`. From now on, when executing a
  single circuit, all the pulses of each bus will be compiled first, and then uploaded to the instruments.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

- Make `nshots` and `repetition_duration` dynamic attributes of the `QbloxModule` class. When any of these two settings
  changes, the cache is emptied to make sure new programs are compiled.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

- Added methods to `PulseBusSchedule` for multiplexing: [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)

  - `frequencies()` returns a list of the frequencies in the schedule.
  - `with_frequency(frequency: float)` returns a new `PulseBusSchedule` containing only those events at that frequency.

- `Pulse`, `PulseEvent`, `PulseShapes` and child classes are now immutable.
  [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)

### Breaking changes

- An `out_offsets` attribute has been added to the settings of a `QbloxModule` object. This attribute contains a list
  of the offsets applied to each output. The runcard should be updated to contain this new information:

  ```yaml
  instruments:
    - name: QRM
    alias: QRM
    id_: 1
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    acquisition_delay_time: 100
    out_offsets: [0.3, 0, 0, 0]  # <-- this new line needs to be added to the runcard!
    awg_sequencers:
      ...
  ```

  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

### Deprecations / Removals

- Removed the `AWG.frequency` attribute because it was not used.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)
- Removed `ReadoutPulse` and `ReadoutEvent`. `Pulse` and `PulseEvent` have to be used instead.
  [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)
- Removed `add(Pulse)` method from `PulseBusSchedule` and `PulseSchedule`. `add_event(PulseEvent)` has to be used instead.
  [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)

### Bug fixes

- Fixed a bug in `PulseBusSchedule.waveforms` where the pulse time was recorded twice.
  [#227](https://github.com/qilimanjaro-tech/qililab/pull/227)

- Fixed bug where the `QbloxModule` uploaded the same sequence to all the sequencers.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

## 0.17.0 (2023-03-27)

### New features since last release

- Added new ChangeLog!
  [#170](https://github.com/qilimanjaro-tech/qililab/pull/170)

- Added rf_on property to SignalGenerator
  [#186](https://github.com/qilimanjaro-tech/qililab/pull/186)

### Improvements

- Cast `chip` dictionary into the `ChipSchema` class and remove unused `InstrumentControllerSchema` class.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

- Upload sequence directly to Qblox instruments, without having to save & load a `json` file.
  [#197](https://github.com/qilimanjaro-tech/qililab/pull/197)

- Changed `schedule_index_to_load` argument to `idx` for more readability.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Refactored the `Experiment` class, creating a method for each step of the workflow. The `Experiment.execute` method will run all these methods in order:
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

  - `connect`: Connect to the instruments and block the device.
  - `initial_setup`: Apply runcard settings to the instruments.
  - `build_execution`:
    - Translate the circuit into pulses.
    - Create the `Execution` class (which contains all the buses with the pulses to execute).
    - Initialize the live plotting.
    - Create the `Results` class and the `results.yml` file (where the results will be stored).
  - `turn_on_instruments`: Turn on the instruments (if necessary).
  - `run`: Iterate over all the loop values, and for each step:
    - Generate the program.
    - Upload the program.
    - Execute the program.
    - Save the result to the `results.yml` file.
    - Send data to live plotting.
    - Save the result to the `Experiment.results` attribute.
  - `turn_off_instruments`: Turn off the instruments (if necessary).
  - `disconnect`: Disconnect from the platform and release the device.
  - `remote_save_experiment`: If `remote_save = True`, save the experiment and the results to the database.

- When translating a Circuit into pulses, the target qubit/resonator frequency is now used to initialize the
  corresponding pulse.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/209)

### Breaking changes

- Removed context manager from `Execution` class. Users will be responsible for turning off and disconnecting the
  instruments when not using the `execute` method directly!
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed the `ExecutionOptions` class. Now the user can freely choose which steps of the workflow to execute.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed the `Platform.connect_and_initial_setup` method.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Move `connection` and `device_id` information into the `Platform` class. Now users should add `device_id` inside
  the runcard and add a `connection` argument when calling `build_platform`:
  [#211](https://github.com/qilimanjaro-tech/qililab/pull/211)

  ```python
  platform = build_platform(name=runcard_name, connection=connection)
  platform.connect(manual_override=False)
  ```

- Removed the frequency argument from the `Pulse.modulated_waveforms` method (and all the methods that uses this method
  internally). Remove `frequency` property from certain buses.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/209)

- The `Pulse.frequency` argument is now mandatory to initialize a pulse.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/209)

### Deprecations / Removals

- Removed the `ExecutionPreparation` class and the `results_data_management.py` file, and replace it with a
  `prepare_results` method inside the `Experiment` class.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed unused `connect`, `disconnect` and `setup` methods from the `Execution` class. These are used in the
  `Experiment` class, which call the corresponding methods of the `Platform` class.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed the `RemoteAPI` class. This class didn't add any functionality.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed all the `Bus` and `SystemControl` types. Now there is only a generic `Bus`, that can contain a
  `SystemControl`, `ReadoutSystemControl` (which contain a list of instruments to control) or `SimulatedSystemControl`,
  which is used to control simulated quantum systems.
  [#210](https://github.com/qilimanjaro-tech/qililab/pull/210)

### Bug fixes

- Fixed wrong timing calculation in Q1ASM generation
  [#186](https://github.com/qilimanjaro-tech/qililab/pull/186)

- Fix bug where calling `set_parameter` with `Parameter.DRAG_COEFFICIENT` would raise an error.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

- The `qibo` version has been downgraded to `0.1.10` to allow installation on Mac laptops.
  [#185](https://github.com/qilimanjaro-tech/qililab/pull/185)

- Fixed the `Platform.get_element` method:
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

  - Now calling `get_element` of a gate returns a `GateSettings` instance, instead of a `PlatformSettings` instance.
  - Add try/except over the `chip.get_node_from_alias` method to avoid getting an error if the node doesn't exist.

## 0.16.1 (2023-02-24)

### Fix

- Platform should be stateful for connections (#143)

## 0.16.0 (2023-02-07)

### Feat

- updates to Qibo v0.1.11, fixes breaking changes (#139)

## 0.15.1 (2023-01-26)

### Fix

- Duplicate hardware_average property & bus.run() in parallel error (#136)

## 0.15.0 (2023-01-24)

### Feat

- Experimentally validated & debugged Spectroscopy  (#134)

## 0.14.0 (2023-01-17)

### Feat

- **Experiment**: added remote experiment saving (#112)

## 0.13.0 (2023-01-17)

### Feat

- **enums**: transform them to string enums (#125)

### Fix

- remove hardcoded modulation from Pulse (#127)

## 0.12.0 (2023-01-17)

### Feat

- Update qblox and qpysequence

## 0.11.0 (2023-01-12)

### Feat

- custom exceptions

## 0.10.3 (2022-12-21)

### Fix

- **Results**: fixed no-results dataframe generation (#109)

## 0.10.2 (2022-12-14)

### Refactor

- \[qili-243\] sequence class (#104)

## 0.10.1 (2022-12-14)

### Fix

- negative-wait (#106)

## 0.10.0 (2022-12-13)

### Feat

- \[QILI-201\] multibus support (#101)

## 0.9.2 (2022-11-17)

### Fix

- remove master drag coefficient (#98)

## 0.9.1 (2022-11-17)

### Refactor

- pulse events (#93)

## 0.9.0 (2022-10-06)

### Feat

- qilisimulator integration (#79)

## 0.8.0 (2022-10-05)

### Feat

- qilisimulator integration (#77)

## 0.7.3 (2022-10-03)

### Fix

- \[QILI-169\] load 2D results (#69)

## 0.7.2 (2022-08-22)

### Fix

- \[QILI-187 \] :bug: loops minimum length taking the passed value instead of the self (#57)

## 0.7.1 (2022-08-19)

### Refactor

- \[QILI-186\] :recycle: renamed beta to drag_coefficient (#56)

## 0.7.0 (2022-08-19)

### Feat

- \[QILI-185\] add option to NOT reset an instrument (#54)

## 0.6.0 (2022-08-18)

### Feat

- \[QILI-184\] :sparkles: New daily directory generated for results data (#50)

## 0.5.9 (2022-08-18)

### Fix

- \[QILI-183\] :bug: accept float master duration gate (#49)

## 0.5.8 (2022-08-18)

### Fix

- \[QILI-182\] :bug: uses deepcopy before pop dict key (#48)

## 0.5.7 (2022-08-17)

### Fix

- set beta serialization correctly (#47)

## 0.5.6 (2022-08-17)

### Fix

- reference clock after reset and using only the necessary sequencers

## 0.5.5 (2022-07-27)

### Fix

- **setup**: versioning

## 0.5.4 (2022-07-26)

### Fix

- \[QILI-181\] :bug: fixed values types when they are numpy (#38)

## 0.5.3 (2022-07-26)

### Fix

- \[QILI-178\] set beta master (#37)

## 0.5.2 (2022-07-26)

### Fix

- \[QILI-180\] :bug: check for multiple loops correctly (#36)

## 0.5.1 (2022-07-25)

### Fix

- \[QILI-177\] :bug: make sure amplitude and duration are float or int (#35)

## 0.5.0 (2022-07-24)

### Feat

- \[QILI-174\] loop support multiple parameters (#34)

## 0.4.2 (2022-07-23)

### Fix

- \[QILI-176\] set master value for gate amplitude and duration (#33)

## 0.4.1 (2022-07-23)

### Fix

- \[QILI-168\] Set voltage normalization (#32)

## 0.4.0 (2022-07-20)

### Feat

- New features from TII trip (#31)

## 0.3.0 (2022-04-26)

### Feat

- \[QILI-81\] Implement schema class (#5)

## 0.2.0 (2022-04-19)

### Feat

- \[QILI-46\] Implement instrument classes (#9)

## 0.1.0 (2022-04-06)

### Feat

- \[QILI-48\] Implement platform, backend and settings classes (#8)

## 0.0.0 (2022-03-28)
