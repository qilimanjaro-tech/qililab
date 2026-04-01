# Release dev (development release)

### New features since last release

- Previously, `QProgram.set_offset` required both I and Q offsets (`offset_path0` and `offset_path1`) to be of the same type (either both constants or both variables).
 This restriction has been removed: it is now possible to mix constants and variables between I and Q.

  ```
  qp = ql.QProgram()
  offset = qp.variable(label="offset", domain=ql.Domain.Voltage)
  with qp.for_loop(variable=offset, start=0, stop=1, step=0.1):
      qp.set_offset(bus="drive", offset_path0= offset, offset_path1=0.5)
      qp.set_offset(bus="drive", offset_path0=0.1, offset_path1=offset)
  ```

  [#1024](https://github.com/qilimanjaro-tech/qililab/pull/1024)

- This release introduces a significant architectural refactor of the digital and pulse-related layers, removes legacy dependencies, and aligns naming and abstractions with established superconducting-qubit literature.

  All references to **Qibo** have been removed from the codebase, along with the complete removal of the **pulse** module. The **digital** module has been fully restructured around a new, self-contained compilation and transpilation pipeline. This includes the introduction of a native **CircuitTranspiler** and **CircuitToQProgramCompiler**. The new **CircuitTranspiler** is responsible for decomposing circuits into the native gate set, managing logical and physical qubit layouts, and applying optimizations. It is implemented as a linear pipeline of `CircuitTranspilerPass` objects, replacing the previous Router, Placer, and Optimizer components that depended on Qibo-based implementations. Each transpiler pass now has a concrete, narrowly defined responsibility.

  The following transpiler passes are now implemented and available: `CancelIdentityPairsPass`, `CircuitToCanonicalBasisPass`, `FuseSingleQubitGatesPass`, `CustomLayoutPass`, `SabreLayoutPass`, `SabreSwapPass`, `CanonicalBasisToNativeSetPass`, and `AddPhasesToDragsFromRZAndCZPass`.

  The IQ waveform class hierarchy has been refactored and unified. A new abstract base class, **IQWaveform**, has been introduced, from which **IQPair** now inherits. The `DRAG` class method has been removed from **IQPair** and replaced by a dedicated **IQDrag** class. This change ensures consistent handling of all IQ waveforms and enables correct and robust serialization.

  Finally, the `Drag` gate has been renamed to `Rmw` to better reflect standard terminology in the literature and to avoid confusion with pulse-level DRAG correction schemes, which are now explicitly implemented via **IQDrag**.
  [#991](https://github.com/qilimanjaro-tech/qililab/pull/991)

- Implemented QBlox and QDAC-II automatic crosstalk compensation for `Qprogram`. The compiler automatically detects if there is a crosstalk matrix inside platform and implements the crosstalk for any bus inside the `Crosstalk` class. To do so, either use `platform.set_crosstalk(crosstalk)` or define a crosstalk inside `calibration` and use it through `execute_qprogram(..., calibration)`.

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
    With crosstalk, the qprogram structure will look the same as usual, but for each bus inside the crosstalk matrix, the machine will send a flux pulse / offset to compensate the crosstalk. The Qprogram is now able to sum variables so this implementation allows for a whole flux vs flux run in a single `Q1ASM`.
    Parallel loops are also available .

    IMPORTANT: there is a limitation when trying to use a combination of play with different amplitudes and different `set_gain`. Since the output is a combination of $amplitude*gain$, the crosstalk would be incorrectly applied if we translate directly. Therefore the gain takes priority when applying the crosstalk.

  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

- Added resistances inside `CrosstalkMatrix()` they can be set by `crosstalk.set_resistances()` in the same way as `crosstalk.set_offset`. Also they can be set inside the calibration file as resistances.
  [#1077](https://github.com/qilimanjaro-tech/qililab/pull/1077)

- Added crosstalk history element within Calibration. The crosstalk history describes the state of the crosstalk at each iteration of the crosstalk calibration, each time a crosstalk calibration is done the user can add an element to the list with `add_intra_crosstalk(flux_offsets, block_diag_xt_matrix)` and `add_inter_crosstalk(full_crosstalk_matrix)` at every step of the calibration to update the `crosstalk_history["history"]`. The user can remove any element on the history that was not correctly implemented with `remove_history_step`.

The crosstalk history contains the index, the previous matrix and offsets, the updated offsets, block diagonal matrix and full matrix, and the results from intra and inter crosstalk calibration.

As an example of the code the user might run:

```
calibration = Calibration()
calibration.crosstalk_matrix = crosstalk_matrix

# Intra qubit experiments
   calibration.add_intra_crosstalk(flux_offsets, block_diag_xt_matrix)

# Inter qubit experiments
   calibration.add_inter_crosstalk(full_crosstalk_matrix)

calibration.save_history()
```

  [#1079](https://github.com/qilimanjaro-tech/qililab/pull/1079)

### Improvements

- For Qblox, the acquisition matrix needs to be reset at each `initial_setup` and `acquire_qprogram_results` call for QRM and QRM-RF instruments. The reset is performed by uploading an empty sequence. This ensures that users do not encounter limitations on the number of available bins due to previously run experiments.

  The empty sequence uploaded is:

  ```
  empty_sequence = {
              "waveforms": {},
                  "weights": {},
                  "acquisitions": {},
                  "program": "",
          }
  ```

  [#1082](https://github.com/qilimanjaro-tech/qililab/pull/1082)

- Previously, the software filters in the `PulseDistortion` module were normalised by default.
This PR changes the default value of `auto_norm` to False, as the previous behaviour was considered counterintuitive.
  [#1075](https://github.com/qilimanjaro-tech/qililab/pull/1075)

- Implemented a new driver for the Becker Nachrichtentechnik RSWU-SP16TR
  [#1020](https://github.com/qilimanjaro-tech/qililab/pull/1020)

- For Autocalibration database, moved `sample_name` and `cooldown` from `AutocalMeasurement` (independent experiment) to `CalibrationRun` (full calibration tree). This way the database does not include redundant information, as these variables do not change from one measurement to another, only in different calibration runs.
  [#1053](https://github.com/qilimanjaro-tech/qililab/pull/1053)

- Added sequence run table to measurements database. This table works similar to calibration run and is intended to store a series of experiment runs one after the other. Added `add_sequence_run` to database manager to operate it. Also modified the quibit index on the autocalibration database from integer to string to take into account two qubit gate experiments.
  [#1070](https://github.com/qilimanjaro-tech/qililab/pull/1070)

- Changed internal structure of waveform generation on the qblox compiler.
Added a check in the platform for QCM and QRM modules with only one channel.
Now whenever a single waveform is given instead of giving this waveform to I and creating an empty Q, it checks first how many channels does it have based on platform:
  - If it has 2 channels the behavior is the same (waveform to I and an empty Q)
  - If it has 1 channel, I and Q are identical waveforms and register as one single waveform (effectively doubling the Q1ASM waveform compilation available size and setting the correct amplitude). If the user gives an IQPair regardless, the behavior remains unchanged and a Q wave will be saved in memory but never sent through the machine.

This check is automatic and requires no input from the user aside from setting the runcard correctly.
  [#1076](https://github.com/qilimanjaro-tech/qililab/pull/1076)

### Breaking changes

- All references to **Qibo** have been removed, and any functionality relying on Qibo-based components has been eliminated.
  [#991](https://github.com/qilimanjaro-tech/qililab/pull/991)

- The **pulse** module has been removed entirely.
  [#991](https://github.com/qilimanjaro-tech/qililab/pull/991)

- The **digital** module has been restructured, replacing the previous Router, Placer, and Optimizer with a new **CircuitTranspiler** pipeline and **CircuitToQProgramCompiler**, which may require updates to downstream integrations.
  [#991](https://github.com/qilimanjaro-tech/qililab/pull/991)

- The IQ waveform hierarchy has changed: **IQWaveform** is now the abstract base class, the `DRAG` method has been removed from **IQPair**, and users must migrate to **IQDrag** where applicable.
  [#991](https://github.com/qilimanjaro-tech/qililab/pull/991)

- The `Drag` gate has been renamed to `Rmw`, requiring updates to any code referencing the old gate name.
  [#991](https://github.com/qilimanjaro-tech/qililab/pull/991)

### Deprecations / Removals

### Documentation

### Bug fixes

- [BUG] - VNA E5080B Driver. Enum Parameters were passing the entire Enum to the device causing an error when setting the parameter. Now the value of the Enum is passed to the device.
  [#1072](https://github.com/qilimanjaro-tech/qililab/pull/1072)

- Calibration file: The `with_calibration` method in `qprogram` was not storing the needed information to import blocks, this information is now being stored.
  The `insert_block` method in `structured_qprogram` has been modified such that the block is flattened, hence each element is added separately, rather than adding the block. Adding the block directly was causing problems at compilation because adding twice in a single `qprogram` the same block meant they shared the same UUID.
  [#1050](https://github.com/qilimanjaro-tech/qililab/pull/1050)

- QbloxDraw: Fixed two acquisition-related bugs:.

  1. Acquisition-only programs are now displayed correctly.
  1. Acquisition timing issues caused by wait instructions have been fixed.
     [#1051](https://github.com/qilimanjaro-tech/qililab/pull/1051)

- QbloxDraw: Variable offsets can now be plotted.
  [#1049](https://github.com/qilimanjaro-tech/qililab/pull/1049)

- Removed threading for `ExperimentExecutor()`. This feature caused a deadlock on the execution if any error is raised inside it (mainly involving the ExperimentsResultsWriter). The threading has been removed as it was only necessary for parallel time tracking.
[#1055](https://github.com/qilimanjaro-tech/qililab/pull/1055)
