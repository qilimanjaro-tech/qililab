# Release dev (development release)

### New features since last release

### Improvements

- Added support for QPrograms with more than 32 distinct acquisition blocks on the same bus (e.g. a Python `for` loop creating N separate `average` blocks each containing one `acquire`). The compiler detects this case during a pre-traversal pass and maps all acquisitions to hardware slot 0 with N bins — one bin per block. The platform then unpacks the single hardware result into N separate `QbloxMeasurementResult` objects, so `len(results["bus"]) == N` as expected.

  The typical use case is sweeping over a non-linear (arbitrary) set of values — not expressible as a hardware `for_loop` — while keeping full averaging in hardware:

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

  The following limitations apply when the number of distinct acquisition blocks exceeds 32:
  - All acquisition blocks must be at **the same nesting depth**. Mixed depths (e.g. some acquires inside a `for_loop` and some directly inside `average`) raise `NotImplementedError`.
  - Each block must contain **exactly one acquisition**. Multiple acquires inside the same block raise `NotImplementedError`.
  - The blocks must be **separate Python-level blocks** (e.g. separate `average` contexts). A single `average` block iterated by a hardware `for_loop` is not affected by this path — the hardware loop handles repetition correctly regardless of count.

- `QbloxCompiler._handle_acquire` has been refactored into three methods — `_handle_acquire` (dispatcher), `_handle_acquire_exceeds_depth`, and `_handle_acquire_per_depth` — making the two acquisition paths independent and easier to maintain. Acquisition depth is now stored alongside the per-block count in a single `_acquisition_metadata` dict, eliminating the redundant `_acquire_depths` dict.


### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `platform._execute_qblox_compilation_output` where a program with N acquisitions on the same bus returned N² results instead of N. A nested loop incorrectly paired every hardware result with every acquisition slot; replaced with `zip` pairing.
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

- Fixed a register explosion in `QbloxCompiler` for programs with more than 32 separate average blocks (exceeds-depth path): a new bin register was incorrectly created for each average block, causing every block to write to hardware bin 0. A single shared bin register is now initialised once and incremented after each block.
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

- Fixed `QbloxCompiler._acquisition_metadata` not being reset between `compile()` calls on the same compiler instance. Stale metadata from a previous compilation could inflate the total acquisition count and incorrectly route a subsequent program to the exceeds-depth path.
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)
