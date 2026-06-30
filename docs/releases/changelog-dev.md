# Release dev (development release)

### New features since last release

- Added `NonLinearState` to qprogram qblox crosstalk handler. This class controls the behavior of `play`, `set_offset`, `set_gain` and loop unpacking of the handler.
  [#1149](https://github.com/qilimanjaro-tech/qililab/pull/1149)

### Improvements

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
