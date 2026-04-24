# Release dev (development release)

### New features since last release

- Added `NonLinearCrosstalkMatrix` class extending `CrosstalkMatrix` to support nonlinear flux crosstalk correction between buses. The  nonlinear correction models SQUID-mediated coupling using a Bessel-series expansion of the periodic SQUID nonlinearity:

  $$\delta\phi_i = 2 \cdot \text{amp}_{ij} \sum_{k=1}^{K} \frac{J_k(k\beta_{ij})}{k\beta_{ij}} \sin(2\pi k \phi_j)$$

  where $\beta_{ij}$ and $\text{amp}_{ij}$ are per-bus-pair parameters stored in `beta_c_matrix` and `non_lin_amp_matrix` respectively. Entries set to `None` indicate no nonlinear coupling for that pair.

  Key additions:
  - `set_non_linear_params(bus_i, bus_j, beta_c, amplitude)`: sets the Bessel modulation parameter and amplitude for a given bus pair.
  - `get_non_linear_flux_terms(flux)`: computes the nonlinear correction vector for a given flux operating point.
  - `flux_to_bias(flux)`: converts target flux values to hardware bias values including nonlinear corrections, applying the inverse of the linear crosstalk matrix on top.
  - `from_linear(linear_crosstalk_matrix)`: creates a `NonLinearCrosstalkMatrix` from an existing `CrosstalkMatrix`, copying all linear parameters and initializing nonlinear entries to `None`.

  Usage example:

```python
  xtalk = NonLinearCrosstalkMatrix.from_linear(existing_crosstalk)

  xtalk.set_non_linear_params("qubit_flux_0", "coupler_flux_2", beta_c=-0.234, amplitude=-0.021)
  xtalk.set_non_linear_params("qubit_flux_3", "coupler_flux_2", beta_c=-0.253, amplitude=-0.021)

  bias = xtalk.flux_to_bias({"qubit_flux_0": 0.1, "qubit_flux_3": 0.2, "coupler_flux_2": 0.05})
```

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
