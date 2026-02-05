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

- Added drivers to operate the Keithley 2400 through the runcard and run a measurement. Through the runcard the user can set the mode and a respective voltage or current. alternatively the user can sweep either current or voltage and retrieve the data of the other component.
[#1065](https://github.com/qilimanjaro-tech/qililab/pull/1065)

### Improvements

- Implemented a new driver for the Becker Nachrichtentechnik RSWU-SP16TR
  [#1020](https://github.com/qilimanjaro-tech/qililab/pull/1020)

- For Autocalibration database, moved `sample_name` and `cooldown` from `AutocalMeasurement` (independent experiment) to `CalibrationRun` (full calibration tree). This way the database does not include redundant information, as these variables do not change from one measurement to another, only in different calibration runs.
  [#1053](https://github.com/qilimanjaro-tech/qililab/pull/1053)

- Added sequence run table to measurements database. This table works similar to calibration run and is intended to store a series of experiment runs one after the other. Added `add_sequence_run` to database manager to operate it. Also modified the quibit index on the autocalibration database from integer to string to take into account two qubit gate experiments.
  [#1070](https://github.com/qilimanjaro-tech/qililab/pull/1070)

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
