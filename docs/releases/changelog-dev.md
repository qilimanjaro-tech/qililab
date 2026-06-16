# Release dev (development release)

### New features since last release

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

- Upgraded `qblox-instruments` dependency from `0.16.0` to `1.0.3`.
  [#1134](https://github.com/qilimanjaro-tech/qililab/pull/1134)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `platform._execute_qblox_compilation_output` where a program with N acquisitions on the same bus returned N² results instead of N. A nested loop incorrectly paired every hardware result with every acquisition slot; replaced with `zip` pairing. This was triggered by any QProgram with acquires at more than one nesting depth on the same bus (e.g. two separate `average` blocks each containing one `acquire`).
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

- Fixed `QbloxQRM.acquire_qprogram_results` uploading an empty sequence after each individual acquisition deletion, which wiped the hardware acquisition table mid-loop and caused subsequent deletions to fail. The empty-sequence upload now happens once after all acquisitions have been deleted. This was triggered by any QProgram that produced more than one named acquisition on the same sequencer (e.g. two separate `average` blocks each containing one `acquire` on the same bus).
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)
  
- Fixed a bug in `load_sequence_by_id` where measurements were returned in an undefined order, causing incorrect results when processing sequences. Measurements are now ordered by `measurement_id`.
  [#1132](https://github.com/qilimanjaro-tech/qililab/pull/1132)

- Pinned spirack to ==0.2.12 as some newer versions may cause an error when importing qblox-instruments.
  [#1135](https://github.com/qilimanjaro-tech/qililab/pull/1135)
 
- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
  [#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
