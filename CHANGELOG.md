# CHANGELOG

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
