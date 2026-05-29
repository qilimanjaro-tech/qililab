# Release dev (development release)

### New features since last release

- Added Qblox automatic non-linear crosstalk compensation inside qprogram. This feature requires a `NonLinearCrosstalkMatrix` as the input crosstalk matrix and it makes use of the features given by `NonLinearFluxVector`. 

It functions much like the linear crosstalk compensation as it modifies the qprogram to adjust the flux buses into their correct bias, in this case the compensation is non-linear.

As the conversion to the new bias is non-linear, the loops given to the qblox Q1ASM cannot be linear and are therefore unpacked limiting the amount of instructions to be given to the Q1ASM sequencer. As well as the `qp.play` waveforms given, if those are arbitrary and inside a loop, it can lead to a waveform memory limitation. Square pulses and `qp.set_offset` does not have this limitation.

  [#1118](https://github.com/qilimanjaro-tech/qililab/pull/1118)

- Added `NonLinearFluxVector` class for managing per-bus flux offsets and gain values with crosstalk compensation across multi-loop sweeps.

  Unlike `FluxVector`, `NonLinearFluxVector` works directly with `Variable` and `VariableExpression` objects so that offsets and gains can sweep over loop dimensions without materialising large arrays up front. It is designed to be driven by a compiler that calls `set_loop` / `exit_loop` as it walks a `QProgram` block tree.

  Usage example:

  ```python
  import numpy as np

  from qililab.core.variables import Domain, Variable
  from qililab.qprogram.blocks import ForLoop, Parallel
  from qililab.qprogram.crosstalk_matrix import NonLinearCrosstalkMatrix
  from qililab.qprogram.flux_vector import NonLinearFluxVector
  from qililab.qprogram.operations import SetGain, SetOffset
  from qililab.waveforms import Square

  nlxtalk = NonLinearCrosstalkMatrix.from_array(...)
  # (...set up xtalk...)

  phi   = Variable("phi",   Domain.Voltage)
  theta = Variable("theta", Domain.Voltage)

  nlfv = NonLinearFluxVector()
  nlfv.set_crosstalk_from_bias(nlxtalk, {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.3})

  nlfv.set_loop(ForLoop(variable=phi,   start=0.0, stop=1.0, step=0.5))  # 3 steps → loop_1
  nlfv.set_loop(ForLoop(variable=theta, start=0.0, stop=4.0, step=1.0))  # 5 steps → loop_2

  nlfv.set_element(SetOffset(bus="flux_0", offset_path0=phi))
  nlfv.set_element(SetGain(bus="flux_1", gain=theta))

  offsets = nlfv.get_corrected_offsets()   # shape (5, 3) per bus
  plays   = nlfv.get_corrected_play({"flux_0": Square(0.5, 100)})  # shape (5, 3) per bus
  ```

  [#1115](https://github.com/qilimanjaro-tech/qililab/pull/1115)

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
[#1102](https://github.com/qilimanjaro-tech/qililab/pull/1102)

- Added `NonLinearFluxVector` class for managing per-bus flux offsets and gain values with crosstalk compensation across multi-loop sweeps. This class is in qililab.qprogram.flux_vector. The original `FluxVector` has been moved to this module.

  Unlike `FluxVector`, `NonLinearFluxVector` works directly with `Variable` and `VariableExpression` objects so that offsets and gains can sweep over loop dimensions without materialising large arrays up front. It is designed to be driven by a compiler that calls `set_loop` / `exit_loop` as it walks a `QProgram` block tree.

  Usage example:

  ```python
  import numpy as np

  from qililab.core.variables import Domain, Variable
  from qililab.qprogram.blocks import ForLoop, Parallel
  from qililab.qprogram.crosstalk_matrix import NonLinearCrosstalkMatrix
  from qililab.qprogram.flux_vector import NonLinearFluxVector
  from qililab.qprogram.operations import SetGain, SetOffset
  from qililab.waveforms import Square

  nlxtalk = NonLinearCrosstalkMatrix.from_array(...)
  # (...set up xtalk...)

  phi   = Variable("phi",   Domain.Voltage)
  theta = Variable("theta", Domain.Voltage)

  nlfv = NonLinearFluxVector()
  nlfv.set_crosstalk_from_bias(nlxtalk, {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.3})

  nlfv.set_loop(ForLoop(variable=phi,   start=0.0, stop=1.0, step=0.5))  # 3 steps → loop_1
  nlfv.set_loop(ForLoop(variable=theta, start=0.0, stop=4.0, step=1.0))  # 5 steps → loop_2

  nlfv.set_element(SetOffset(bus="flux_0", offset_path0=phi))
  nlfv.set_element(SetGain(bus="flux_1", gain=theta))

  offsets = nlfv.get_corrected_offsets()   # shape (5, 3) per bus
  plays   = nlfv.get_corrected_play({"flux_0": Square(0.5, 100)})  # shape (5, 3) per bus
  ```

  [#1115](https://github.com/qilimanjaro-tech/qililab/pull/1115)

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

- Allowing for multiple hardware loops for gain and offset with crosstalk compensation, such as flux vs flux measurements. This is possible due to the `VariableExpression` with crosstalk compensation.  Removed raised `NotImplementedError` (`"Double Hardware loops are not yet implemented with the crosstalk."`). Example qprograms:

    ```
    ...
    square_wf = Square(amplitude=0.1, duration=50)
    qp = QProgram()
    offset_1 = qp.variable(label="offset_1", domain=Domain.Voltage)
    offset_2 = qp.variable(label="offset_2", domain=Domain.Voltage)
    with qp.for_loop(variable=offset_1, start=0, stop=0.1, step=0.01):
        with qp.for_loop(variable=offset_2, start=0.1, stop=0, step=-0.01):
            qp.set_offset(bus="flux1", offset_path0=offset_1)
            qp.set_offset(bus="flux2", offset_path0=offset_2)
            ...
    ```
And after the crosstalk compensation has been applied the qprogram will look internally like this: 
    ```
    ...
    square_wf = Square(amplitude=0.1, duration=50)
    qp = QProgram()
    flux_offset_1_1 = qp.variable(label="flux_offset_1_1", domain=Domain.Voltage)  # Flux 1 to itself
    flux_offset_1_2 = qp.variable(label="flux_offset_1_2", domain=Domain.Voltage)  # Flux 2 to flux 1
    flux_offset_2_1 = qp.variable(label="flux_offset_2_1", domain=Domain.Voltage)  # Flux 1 to flux 2
    flux_offset_2_2 = qp.variable(label="flux_offset_2_2", domain=Domain.Voltage)  # Flux 2 to itself
    with qp.parallel([ForLoop(flux_offset_1_1, 0, 0.1, 0.01), ForLoop(flux_offset_1_2, 0, 0.1, 0.01)]):
        with qp.parallel([ForLoop(flux_offset_2_1, 0.1, 0, -0.01), ForLoop(flux_offset_2_2, 0.1, 0, -0.01)]):
            qp.set_offset(bus="flux1", offset_path0=flux_offset_1_1 + flux_offset_1_2)  # Here we require variable extension
            qp.set_offset(bus="flux2", offset_path0=flux_offset_2_1 + flux_offset_2_2)
            ...
    ```

  [#1109](https://github.com/qilimanjaro-tech/qililab/pull/1109)

- Modified database manager's `load_by_id` to allow a list of ids to return a list of the measurements with said ids. Also added function `db_manager.get_dc_offsets(id)`, for recent addition to the measurements database, `dc_offsets`.
  [#1097](https://github.com/qilimanjaro-tech/qililab/pull/1097)

### Breaking changes

- `VariableExpression.extract_variables()` and `VariableExpression.extract_constants()` have been removed. They are replaced by `VariableExpression.variables` (list of all `Variable` instances in the expression) and `VariableExpression.constant` (the constant term, or `None`).
  [#1057](https://github.com/qilimanjaro-tech/qililab/pull/1057)

### Deprecations / Removals

### Documentation

### Bug fixes

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
  [#1098](https://github.com/qilimanjaro-tech/qililab/pull/1098)

- Fixed a bug where the qblox instrument controller parameter `ext_trigger` and the qdac instrument controller parameter `reference_clock` where not correctly translated to dictionary from the runcard and therefore not saved with `ql.save_platform(platform)`.
  [#1104](https://github.com/qilimanjaro-tech/qililab/pull/1104)

- Fixed bug were the RSWU_SP16TR `Instrument` and `InstrumentController` wouldn't be registred causing `build_platform` to fail.
  [#1120](https://github.com/qilimanjaro-tech/qililab/pull/1120)