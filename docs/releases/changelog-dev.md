# Release dev (development release)

### New features since last release

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

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- The save_platform function was not saving bus distortions because it wasn't added to the Bus.to_dict after the refactor. The property has been added.
  [#1100](https://github.com/qilimanjaro-tech/qililab/pull/1100)

- Fixed a bug for function Platform.set_bias_to_zero(bus_list) where the flux vector was not updated correctly from bias.
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

- Fixed a bug for qdac execution order, the positions were inverted causing issues with the triggering.
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

- Fixed a bug at the QdacCompiler where the dwell time was converted to us twice turning any value to the minimum dwell possible.
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)
