# CHANGELOG

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
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/192)

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
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/192)

- The `Pulse.frequency` argument is now mandatory to initialize a pulse.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/192)

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
  [#210](https://github.com/qilimanjaro-tech/qililab/pull/192)

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
