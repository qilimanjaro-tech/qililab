# Release dev (development release)

### New features since last release

### Improvements

- Removed unnecessary wait_syncs created by `qp.wait_trigger` when the instrument has only one sequencer.
  Now for one sequencer it will behave like this:

    ```
        qp.set_frequency(bus="drive", frequency=1e6)
        qp.wait_trigger(bus="drive", duration=1_000, port=1)
      ---            
        set_freq         4000000
        set_freq         4000000
        upd_param        4
        wait_trigger     1, 4
        wait             992
    ```

  Whereas with two buses there will be an extra wait_sync in the Q1ASM (also compensated by duration):

    ```
        qp.set_frequency(bus="drive", frequency=1e6)
        qp.set_frequency(bus="readout", frequency=1e6)
        qp.wait_trigger(bus="drive", duration=1_000, port=1)
      ---
      drive sequencer:
        set_freq         4000000        
        set_freq         4000000        
        wait_trigger     1, 4           
        wait_sync        4              
        upd_param        4              
        wait             996            

      readout sequencer:
        set_freq         4000000        
        set_freq         4000000        
        wait_sync        4 
    ```

  [#1099](https://github.com/qilimanjaro-tech/qililab/pull/1099)

- Added `wait_trigger` to the qblox drawer. The drawer shows the wait duration stated in `wait_trigger`, although the duration of this wait is non deterministic (as it is waiting for an external source to send a pulse).
  [#1099](https://github.com/qilimanjaro-tech/qililab/pull/1099)

- Removed `external_trigger` parameter from within the runcard's qblox controller instrument. Now the function `QbloxClusterController.set_ext_trigger` is risen internally every time a qprogram contains a `wait_trigger` using the trigger channel 15 (last one).
  [#1112](https://github.com/qilimanjaro-tech/qililab/pull/1112)

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

- Fixed a bug for wait trigger in the qblox compiler using a single sequencer because it created an unnecessary wait_sync (without any other sequencers to sync). Now the Qblox compiler checks for the amount of buses with a sequencer.
  [#1099](https://github.com/qilimanjaro-tech/qililab/pull/1099)

- Fixed a bug for `wait_trigger` where for large durations the waiting time was not correctly implemented. Now it uses `_handle_add_waits` like `wait`.
  These are some examples of uses:
  - Duration of 4 creates a simple Q1ASM with the wait trigger with the minimal wait duration, not defining a port defaults to port 15:

    ```
        qp.wait_trigger(bus="drive", duration=4)
      ---
        wait_trigger     15, 4
    ```

  - Duration of 70,000 (and any duration bigger than 8) will execute `_handle_add_waits` and create waits with duration minus 4 ns (from the wait trigger):

    ```
        qp.wait_trigger(bus="drive", duration=70_000, port=1)
      ---
        wait_trigger     1, 4
        wait             65532
        wait             4464
    ```

  - If the wait_trigger is set before any parameter update qprogram defines an `upd_param` of 4 ns (adding this value to the total time):

    ```
        qp.set_frequency(bus="readout", frequency=1e6)
        qp.wait_trigger(bus="drive", duration=1_000, port=1)
      ---
        upd_param        4
        wait_trigger     1, 4
        wait             992
    ```

  [#1099](https://github.com/qilimanjaro-tech/qililab/pull/1099)

- Fixed a bug in `platform._execute_qblox_compilation_output` where a program with N acquisitions on the same bus returned N² results instead of N. A nested loop incorrectly paired every hardware result with every acquisition slot; replaced with `zip` pairing. This was triggered by any QProgram with acquires at more than one nesting depth on the same bus (e.g. two separate `average` blocks each containing one `acquire`).
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

- Fixed `QbloxQRM.acquire_qprogram_results` uploading an empty sequence after each individual acquisition deletion, which wiped the hardware acquisition table mid-loop and caused subsequent deletions to fail. The empty-sequence upload now happens once after all acquisitions have been deleted. This was triggered by any QProgram that produced more than one named acquisition on the same sequencer (e.g. two separate `average` blocks each containing one `acquire` on the same bus).
  [#1117](https://github.com/qilimanjaro-tech/qililab/pull/1117)

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
  [#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
