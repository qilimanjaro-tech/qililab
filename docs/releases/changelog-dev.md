# Release dev (development release)

### New features since last release
- Updated `electrical_delay` to be a changeable parameter for the keysight E5080b and not just a software setting used in the auto-ploting.
  [#1047](https://github.com/qilimanjaro-tech/qililab/pull/1047)

- Added bus_mapping to measurement database table `Measurement`. Bus mapping is necessary for live plot drawing of the qprogram and it has been information missing in the database. StreamArray already has the bus_mapping as an input, this input is the dictionary that will be saved in the database.
  [#1136](https://github.com/qilimanjaro-tech/qililab/pull/1136)

- Added `sort_buses` and `argsort_buses` to `qililab.utils`, utilities that order bus identifiers into a stable, easy to read order:
    1. Count of integers in the name; single-index qubit buses (one number) sort
       before two-index couplers, e.g. "flux q9" before "coupler 0 1".
    2. The integers themselves, compared numerically; so "drive q2" sorts before
       "drive q10" (plain alphabetical order would put q10 first).
    3. Bus type: readout < drive < flux < unspecified.
    4. Loop type: z < x < unspecified (x and z are only identified if there are no surrounding letters).
    5. The raw string, as a final alphabetical tiebreak for full determinism.
  `argsort_buses` also returns the sort permutation, so a matrix and its bus labels can be reordered together.
  [#1161](https://github.com/qilimanjaro-tech/qililab/pull/1161)

### Improvements

- `CrosstalkMatrix.to_array` and its `__str__` representation now order buses with `sort_buses`, so multi-digit bus names are shown in natural order (`flux q2` before `flux q10`) instead of lexicographically.
  [#1161](https://github.com/qilimanjaro-tech/qililab/pull/1161)

- Fixed `test_data_management.py` and `test_slurm.py` failing on local Windows dev environments: `save_platform()`'s return path is now compared as a `Path` instead of a raw string (Windows uses backslash separators), and `TestSubmitJob` (which relies on `submitit`'s POSIX-only local executor) is now skipped on Windows.
  [#1158](https://github.com/qilimanjaro-tech/qililab/pull/1158)

- Pin qpysequence==0.10.8
  [#1155](https://github.com/qilimanjaro-tech/qililab/pull/1155)

- Added a `ValueError` while creating the `DatabaseManager` (for example with `get_db_manager`) checking for `user`, `passwd`, `host`, `port` or `database` inside the database.ini config file, if any of these parameters is missing an error is thrown.
  [#1152](https://github.com/qilimanjaro-tech/qililab/pull/1152)

- Added `NonLinearFlagState` to qprogram qblox crosstalk handler. This class controls the behavior of `play`, `set_offset`, `set_gain` and loop unpacking of the handler.
  [#1149](https://github.com/qilimanjaro-tech/qililab/pull/1149)

- Added support for QPrograms with more than 32 distinct acquisitions in different blocks on the same bus. The compiler detects this case during a pre-traversal pass and maps all acquisitions to hardware index 0 with N bins, one bin per block. The platform then unpacks the single hardware result into N separate `QbloxMeasurementResult` objects, so `len(results["bus"]) == N` as expected.

  The typical use case is sweeping over a non-linear (arbitrary) set of values, not expressible as a hardware `for_loop`:

  ```python
  freq_array = [4.85e9, 4.91e9, 5.02e9, ...]  # arbitrary, non-linear spacing
  weights = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
  readout_wf = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))

  qp = QProgram()
  for freq in freq_array:
      with qp.average(shots=1000):
          qp.set_frequency(bus="readout", frequency=freq)
          qp.play(bus="readout", waveform=readout_wf)
          qp.qblox.acquire(bus="readout", weights=weights)

  results = platform.execute_qprogram(qp)
  # len(results.results["readout"]) == len(freq_array)
  ```

  The following limitations apply when the number of distinct acquisitions in different blocks exceed 32:
  - All acquisition blocks must be at **the same nesting depth**. Mixed depths (e.g. some acquires inside a `for_loop` and some directly inside `average`) raise `NotImplementedError`.
  - Each block must contain **exactly one acquisition**. Multiple acquires inside the same block raise `NotImplementedError`.
  - All blocks must be `average` blocks. Using `for_loop` blocks raises `NotImplementedError`.

  `QbloxCompiler._handle_acquire` has been refactored into three methods: `_handle_acquire` (dispatcher), `_handle_acquire_exceeds_depth`, and `_handle_acquire_per_depth`, making the two acquisition paths independent. Acquisition depth is now stored alongside the per-block count in a single `_acquisition_metadata` dict. This dict is now also reset at the start of each `compile()` call, ensuring correctness when the same compiler instance is reused.
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

### Breaking changes

- Added `timeout_repetitions` parameter for QRM and QRM-RF instruments sequencers inside the runcard. This parameter controls how many (if any) executions of the same qblox qprogram execution must be done after an acquisition `TimeoutError`. Defaults to no repetitions.
In the runcard this parameter is located inside the instruments sequencer for QRM and QRM-RF modules.

  ```
    - name: QRM-RF
    alias: QRM-RF1
    ...
    awg_sequencers:
    - identifier: 0
      ...
      acquisition_timeout: 1  # In minutes
      timeout_repetitions: 3  # Optional parameter, defaults to None
      ...
  ```

  [#1106](https://github.com/qilimanjaro-tech/qililab/pull/1106)

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a race condition, introduced in [#1154](https://github.com/qilimanjaro-tech/qililab/pull/1154), where triggered `Qblox` executions using a `QDAC-II` could hang forever waiting for a trigger that was already cancelled. `qdac.start()` only issues a non-blocking SCPI command; the QDAC's trigger pulse to `Qblox` fires later, on the instrument's own internal timing. The post-execution `qdac.clear_cache()` ran immediately after `start()` and zeroed the same marker register that routes that pulse, so if the register was cleared before the instrument's internal clock reached the marker event, the pulse never went out and `Qblox` stayed armed indefinitely. `Platform._execute_qblox_compilation_output` now defers that cleanup until after results are acquired, since `acquire_qprogram_results` can only return once `Qblox`'s `wait_trigger` has unblocked, which guarantees the physical pulse already fired.
  [#1164](https://github.com/qilimanjaro-tech/qililab/pull/1164)

- Fixed `CrosstalkMatrix` row/column ordering being inconsistent between `to_array` (ordered with `sort_buses`) and `inverse`/`from_array` (raw insertion order). For any matrix whose buses were not stored in natural order e.g. a system with ≥10 buses saved alphabetically (`flux q0, flux q1, flux q10, flux q2`); the inverse was mislabeled and `flux_to_bias` returned wrong bias values, and `Calibration.add_intra_crosstalk`/`add_inter_crosstalk` corrupted the stored matrix and offsets. `inverse`, the calibration updates and their `from_array` calls now share the canonical `sort_buses` ordering. Also added `qililab.utils.argsort_buses`, which returns the sort permutation so an array and its bus labels can be reordered together.
  [#1161](https://github.com/qilimanjaro-tech/qililab/pull/1161)

- Fixed the default value for QDAC's voltage list dwell time. Before, it was set to 1 us but the [QDAC documentation page 76](https://qm.quantum-machines.co/hubfs/QDAC%20II%20-%20User%20manual%20v2.2%20(2024-01-17).pdf) states that the minimum is 2 us. If a user states a number smaller than 2 us, the qdac automatically sets the dwell time as the minimum (2 us).
  [#1154](https://github.com/qilimanjaro-tech/qililab/pull/1154)

- Fixed the QDAC-II trigger network breaking when multiple users are connected to the same instrument. Each qililab instance allocated internal trigger numbers from its own driver-side pool, with no way of knowing which numbers other Python processes were already using. When two instances picked the same number, their triggers fired through each other's networks, interfering with both experiments.

  Internal triggers in use are now read directly from the instrument's marker registers before every allocation, so a new trigger always takes the lowest number that is actually free on the hardware. Related behavior changes:
  - `QDevilQDac2.start()` now starts only the DC lists and AWG waveforms uploaded by this instance, instead of `start_all()`, which also fired generators armed by other users.
  - `QDevilQDac2.clear_trigger()` now frees the triggers created by this instance from the instrument (previously `free_all_triggers()` released the triggers set by `QCodes`, not affecting the instrument).
  - `Platform.execute_qprogram` now clears each QDAC-II's trigger network and generator caches after every execution, so consecutive executions always start from a clean trigger state.
  - Allocating a trigger when all 14 internal triggers are busy raises a `ValueError` including other users triggers.
  [#1154](https://github.com/qilimanjaro-tech/qililab/pull/1154)

- Fixed the folder shape at `add_measurement` and `add_results` to take into account us intervals of time. This will solve any issue with parallelization while creating more than one folder in less than a second.
  [#1152](https://github.com/qilimanjaro-tech/qililab/pull/1152)

- Fixed some bugs with the automatic non-linear crosstalk compensation at the `QbloxCompiler`:
  - The offset was set unnecessary times whenever a play followed a set offset in a qprogram, now the amount of set offsets are reduced on the Q1ASM sequencer.
  - A sequence of offset loops using the same variable did not update the offset value correctly, now the variables are set correctly. For example:

    ```
    with qp_qblox.for_loop(variable=offset, start=0, stop=0.9, step=0.1):
        qp_qblox.set_offset(bus="qblox_flux1", offset_path0=offset)
        qp_qblox.set_offset(bus="qblox_flux2", offset_path0=0.1)
    with qp_qblox.for_loop(variable=offset, start=0.9, stop=0, step=-0.1):
        qp_qblox.set_offset(bus="qblox_flux1", offset_path0=offset)
        qp_qblox.set_offset(bus="qblox_flux2", offset_path0=0.1)
    ```

  - An offset set after a loop containing `qprogram.set_offset` was not updated, now it sets correctly after a loop. For example:

    ```
    with qp_qblox.for_loop(variable=offset, start=0, stop=0.9, step=0.1):
        qp_qblox.set_offset(bus="qblox_flux1", offset_path0=offset)
        qp_qblox.set_offset(bus="qblox_flux2", offset_path0=0.1)
    qp_qblox.set_offset(bus="qblox_flux1", offset_path0=0)
    qp_qblox.set_offset(bus="qblox_flux2", offset_path0=0)
    ```

  [#1149](https://github.com/qilimanjaro-tech/qililab/pull/1149)

- Fixed `ExperimentExecutor` not generating the loop shape correctly for data coming from a `QProgram` hardware loop, breaking the execution whenever the data does not fit with .h5 loop shape. This has been fixed by setting the same data size from `ExperimentExecutor` class axis generation as the output shape from the Qblox.
  [#1153](https://github.com/qilimanjaro-tech/qililab/pull/1153)

- Fixed `ExperimentExecutor` not allocating result datasets for `Acquire` (`qp.qblox.acquire`) and `MeasureReset` operations. Previously only `Measure` operations were counted as measurements, so a QProgram that read out via `qp.qblox.acquire` produced no result datasets and `ExperimentResults.get()` raised `KeyError`. The executor now counts the same `(Acquire, Measure, MeasureReset)` set as the `QbloxCompiler`.
  [#1148](https://github.com/qilimanjaro-tech/qililab/pull/1148)

- Fixed issue where `Platform.set_parameter` using the alias of a "rswu-sp16tr" instrument would raise an error.
  [#1130](https://github.com/qilimanjaro-tech/qililab/pull/1130)

- Fixed a bug for Rohde & Schwarz SGS100A instrument class where the module SGS-B106V did not apply the iq_wideband at the initial_setup.
  [#1144](https://github.com/qilimanjaro-tech/qililab/pull/1144)

- Fixed a bug in `platform._execute_qblox_compilation_output` where a program with N acquisitions on the same bus returned N² results instead of N. A nested loop incorrectly paired every hardware result with every acquisition slot; replaced with `zip` pairing. This was triggered by any QProgram with acquires at more than one nesting depth on the same bus (e.g. two separate `average` blocks each containing one `acquire`).
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

- Fixed `QbloxQRM.acquire_qprogram_results` uploading an empty sequence after each individual acquisition deletion, which wiped the hardware acquisition table mid-loop and caused subsequent deletions to fail. The empty-sequence upload now happens once after all acquisitions have been deleted. This was triggered by any QProgram that produced more than one named acquisition on the same sequencer (e.g. two separate `average` blocks each containing one `acquire` on the same bus).
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)
 
- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
  [#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
