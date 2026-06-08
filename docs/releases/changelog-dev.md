# Release dev (development release)

### New features since last release

- Extended `VariableExpression` capabilities (Qblox backend only)
  The capabilities of `VariableExpression` have been extended, and remain exclusive to the Qblox backend. 

  Previously, this type of expression was only supported in the Time Domain. It is now also available in the Voltage Domain, where it can be used to modify values in `qprogram` via the offset or the gain.
  The Time Domain behavior is unchanged. The updates described below therefore apply only to Voltage Domain operations.

  A combination of variables is now possible (Voltage Domain only), as shown below.
    ```
    qp = ql.Qprogram()
    gain1 = qp.variable("gain1", ql.Domain.Voltage)
    gain2 = qp.variable("gain2", ql.Domain.Voltage)
    qp.set_gain("bus", gain1 + gain2)
    
    ```
    These expressions are subject to some restrictions:
    - Expression chaining is not supported: at most two components (a variable and a constant, or two variables) are allowed. For example, the following code will raise a `NotImplementedError`:
        ```
      qp = ql.Qprogram(
      gain1 = qp.variable("gain1", ql.Domain.Voltage)
      qp.set_gain("bus", 10 + gain1 + 30)
      )
      ```
      Note: unary negation of a variable (e.g. `- gain`) counts as two components (it is rewritten as `0 - gain`), so combining it with an additional term (e.g. `- gain - 10`) is also expression chaining and raises `NotImplementedError`.
    - Only addition (`+`) and subtraction (`-`) are supported. The following raise a `TypeError`: `*`, `@`, `/`, `//`, `%`, `**`, `&`, `|`, `^`, `<<`, `>>`, `>`, `<`, `>=`, `<=`, `+=`, `-=`, `*=`, `/=`. Boolean constants also raise a `ValueError`. Taking `abs()` of a variable raises a `NotImplementedError`.
    - Mixing variables of different domains (e.g. `gain + freq`) raises a `ValueError`.
    - Using a `VariableExpression` in `set_offset` with independent I and Q paths raises a `NotImplementedError`.
    - Using a `VariableExpression` with crosstalk compensation across multiple hardware loops raises a `NotImplementedError` (`"Double Hardware loops are not yet implemented with the crosstalk."`). This will be supported in a future PR.
    - To facilitate the `Q1ASM` implementation, some expressions are internally reorganized in the `Variable` class without changing their semantics:
      ```
      gain + (-10) -> gain - abs(10)
      - 10 + gain  -> gain - abs(10)
      gain - (-10) -> gain + abs(10)
      - gain       -> 0 - gain

      ```
  [#1057](https://github.com/qilimanjaro-tech/qililab/pull/1057)


- Implemented QBlox and QDAC-II automatic crosstalk compensation for `Qprogram`. The compiler automatically detects if there is a crosstalk matrix inside platform and implements the crosstalk for any bus inside the `Crosstalk` class. To do so, either use `platform.set_crosstalk(crosstalk)` or define a crosstalk inside `calibration` and use it through `execute_qprogram(..., calibration)`.
With `execute_qprogram(..., crosstalk= True / False)` the parameter introduced is a trigger that activates the crosstalk, the user can deactivate crosstalk compensation by setting this flag as False. The flag is True by default but if no crosstalk has been introduce through `platform.set_crosstalk(crosstalk)` or `execute_qprogram(..., calibration)` no crosstalk will be applied as none exists.

  - For QDAC-II:
    The crosstalk modifies the internal structure of the `QProgram`, it changes any play or set offset into a set of plays and offsets of each bus of the crosstalk. It also takes into account different loops.
    With crosstalk, this example qprogram:

    ```
    r_wf = ql.Square(amplitude=1.0, duration=1000)
    flux_wf = ql.Arbitrary(
        samples=np.array([0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3, 0.2, 0.1, 0])
    )
    qp_qdac = ql.QProgram()

    freq = qp_qdac.variable(label="frequency", domain=ql.Domain.Frequency)

    with qp_qdac.average(10):
        qp_qdac.set_offset(bus="qdac_flux2", offset_path0=0.3)
        with qp_qdac.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):

            # QDAC TRIGGER GENERATION
            qp_qdac.qdac.play(bus="qdac_flux1", waveform=flux_wf, dwell=2)
            qp_qdac.set_offset(bus="qdac_flux2", offset_path0=-0.2)
            qp_qdac.set_trigger(bus="qdac_flux1", duration=10e-6, outputs=1, position="start")

            # QBLOX WAIT TRIGGER
            qp_qdac.wait_trigger(bus="readout", duration=4)

            qp_qdac.set_frequency(bus="readout", frequency=freq)
            qp_qdac.sync()
            qp_qdac.measure(
                bus="readout",
                waveform=ql.IQPair(I=r_wf, Q=r_wf),
                weights=ql.IQPair(I=r_wf, Q=r_wf),
            )

            qp_qdac.wait(bus="readout", duration=100)
    ```

    Turns internally into this (for a crosstalk matrix only including `qdac_flux1` and `qdac_flux2`):

    ```
    ...

    with qp_qdac.average(10):
        qp_qdac.set_offset(bus="qdac_flux2", offset_path0=offset_2_compensated)
        qp_qdac.set_offset(bus="qdac_flux1", offset_path0=offset_1_compensated)
        with qp_qdac.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):

            # QDAC TRIGGER GENERATION
            qp_qdac.qdac.play(bus="qdac_flux2", waveform=flux_wf_crosstalk_compensated_2, dwell=2)
            qp_qdac.qdac.play(bus="qdac_flux1", waveform=flux_wf_crosstalk_compensated_1, dwell=2)
            qp_qdac.set_trigger(bus="qdac_flux1", duration=10e-6, outputs=1, position="start")

            # QBLOX WAIT TRIGGER
            qp_qdac.wait_trigger(bus="readout", duration=4)

            qp_qdac.set_frequency(bus="readout", frequency=freq)
            qp_qdac.sync()
            qp_qdac.measure(
                bus="readout",
                waveform=ql.IQPair(I=r_wf, Q=r_wf),
                weights=ql.IQPair(I=r_wf, Q=r_wf),
            )

            qp_qdac.wait(bus="readout", duration=100)
    ```

  - For QBlox:
    The `QProgram` structures affected by the crosstalk are `qp.set_offset(...)`, `qp.set_gain(...)` and `qp.play(...)` for flux buses. The behavior is similar to the `QdacCompiler` but accounting for the complexity of Qblox compilation.
    With crosstalk, the qprogram structure will look the same as usual, but for each bus inside the crosstalk matrix, the machine will send a flux pulse / offset to compensate the crosstalk.
    Parallel loops are also available .

    IMPORTANT: there is a limitation when trying to use a combination of play with different amplitudes and different `set_gain`. Since the output is a combination of $amplitude*gain$, the crosstalk would be incorrectly applied if we translate directly. Therefore the gain takes priority when applying the crosstalk.

  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

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

- Modified database manager's `load_by_id` to allow a list of ids to return a list of the measurements with said ids. Also added function `db_manager.get_dc_offsets(id)`, for recent addition to the measurements database, `dc_offsets`.
  [#1097](https://github.com/qilimanjaro-tech/qililab/pull/1097)

### Breaking changes

- `VariableExpression.extract_variables()` and `VariableExpression.extract_constants()` have been removed. They are replaced by `VariableExpression.variables` (list of all `Variable` instances in the expression) and `VariableExpression.constant` (the constant term, or `None`).
  [#1057](https://github.com/qilimanjaro-tech/qililab/pull/1057)

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `platform._execute_qblox_compilation_output` where a program with N acquisitions on the same bus returned N² results instead of N. A nested loop incorrectly paired every hardware result with every acquisition slot; replaced with `zip` pairing.

- Fixed a register explosion in `QbloxCompiler` for programs with more than 32 separate average blocks (exceeds-depth path): a new bin register was incorrectly created for each average block, causing every block to write to hardware bin 0. A single shared bin register is now initialised once and incremented after each block.

- Fixed `QbloxCompiler._acquisition_metadata` not being reset between `compile()` calls on the same compiler instance. Stale metadata from a previous compilation could inflate the total acquisition count and incorrectly route a subsequent program to the exceeds-depth path.

- Fixed a bug in `set_offset` where using a `Variable` on one path and a negative static value on the other would generate a `move` instruction with a negative immediate, which is invalid Q1ASM.
  [#1113](https://github.com/qilimanjaro-tech/qililab/pull/1113)

- Fixed a bug where `qp.qblox.play` with `wait_time=0` was treated as no `wait_time` provided, producing incorrect Q1ASM. The wait time is now correctly clamped to the minimum valid value of 4 ns.
  [#1114](https://github.com/qilimanjaro-tech/qililab/pull/1114)

- The save_platform function was not saving bus distortions because it wasn't added to the Bus.to_dict after the refactor. The property has been added.
  [#1100](https://github.com/qilimanjaro-tech/qililab/pull/1100)

- Fixed a bug for function Platform.set_bias_to_zero(bus_list) where the flux vector was not updated correctly from bias.
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

- Fixed a bug for qdac execution order, the positions were inverted causing issues with the triggering.
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

- Fixed a bug at the QdacCompiler where the dwell time was converted to us twice turning any value to the minimum dwell possible.
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

- Fixed a bug in the Qblox compiler where the bin acquisition index was not incrementing correctly when multiple `measure` calls are used sequentially inside an `average` block with an outer sweep loop.  Each sequential acquire now gets its own bin register initialised to its position offset, and the bin register is advanced by the total number of acquires per sweep step (instead of always 1), so that consecutive acquires write to consecutive bins and the full acquisition matrix is filled correctly.
  [#1098](https://github.com/qilimanjaro-tech/qililab/pull/1098

- Fixed a bug where the qblox instrument controller parameter `ext_trigger` and the qdac instrument controller parameter `reference_clock` where not correctly translated to dictionary from the runcard and therefore not saved with `ql.save_platform(platform)`.
  [#1104](https://github.com/qilimanjaro-tech/qililab/pull/1104)
