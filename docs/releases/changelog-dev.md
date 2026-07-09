# Release dev (development release)

### New features since last release

### Improvements

- Migrated `QbloxCompiler` to the redesigned `qpysequence` API (version 1.0.0). The compiler now uses the new `Compiler` class (`qpysequence.compiler.Compiler`) to lower and compile Q1ASM programs, replacing the old `program.compile()` call. Program construction now uses `block.add()` throughout, programs have an explicit `setup` block followed by `main`, loop sweeps use the new `SweepSpec`-based `IterativeLoop` API with `ConversionInstruction` subclasses (`SetNormalisedOffs`, `SetNormalisedGain`, `SetFrequencyHz`, `SetPhaseRad`) for automatic physical-unit-to-integer scaling, and label references no longer require the `@` prefix. `Sequence.todict()` is replaced by `Sequence.to_dict()` throughout. Several responsibilities have shifted from `qililab` to `qpysequence`:
  - **`nop` insertion**: qililab no longer emits `nop` instructions manually; qpysequence's compiler handles read-after-write hazard guards automatically. Duplicate parameter instructions (e.g. double `set_awg_gain` or `set_freq`) that were previously emitted as a workaround are no longer needed.
  - **Physical-unit-to-integer conversion**: scaling of physical-unit values (normalised gain/offset, Hz frequency, radian phase) to Q1ASM integers is now fully owned by qpysequence via `ConversionInstruction.scale_factor`.
  - **Long-wait handling**: durations exceeding `INST_MAX_WAIT` are now managed by qpysequence's `LongWait` instruction rather than qililab.
  - **Adjacent wait merging**: consecutive `wait` instructions are now combined by qpysequence's compiler rather than by qililab.
  - The Q1ASM output is functionally equivalent but may differ structurally from previous versions; see the qpysequence changelog for a full description.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)
  
- Updated `QbloxDraw` to iterate over all program blocks (`setup` and `main`) to match the new multi-block program structure.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)
  
- `QbloxCompiler` now emits a warning and clamps to 4 ns when a `wait`, `wait_trigger`, or `play` duration, or a hardware loop's start or stop value, is below the Q1ASM minimum of 4 ns.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)
  
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

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed incorrect Q1ASM emitted when a long wait (> `INST_MAX_WAIT`) follows a pending `upd_param`: the pending-instruction branch now uses `LongWait` consistently with the no-pending branch.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)
  
- Fixed numpy scalar passthrough in `QProgram` operations: `wait`, `wait_trigger`, `set_phase`, `set_frequency`, `set_gain`, `set_offset`, `set_trigger`, `for_loop`, and `average` parameters now call `_to_scalar()` to convert numpy integer/float types to native Python scalars before constructing operations, preventing type errors downstream.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)

- Fixed `wait_trigger` overshooting the requested duration by tens of thousands of ns whenever it exceeded `INST_MAX_WAIT`: `_handle_add_trigger_waits` now emits `LongWait`, like its sibling `_handle_add_waits`, instead of a manual splitting loop that always rounded up to a whole number of `INST_MAX_WAIT` chunks and dropped the remainder.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)

- Fixed a hardware loop's `wait` domain not clamping the `stop` value to the Q1ASM minimum of 4 ns: only `start` was previously clamped, so a descending `for_loop`/`parallel` sweep over `wait` durations could reach an invalid (< 4 ns) final register value with no warning.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)

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
