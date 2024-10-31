# Release dev (development release)

### New features since last release

- A new `GetParameter` operation has been added to the Experiment class, accessible via the `.get_parameter()` method. This allows users to dynamically retrieve parameters during experiment execution, which is particularly useful when some variables do not have a value at the time of experiment definition but are provided later through external operations. The operation returns a `Variable` that can be used seamlessly within `SetParameter` and `ExecuteQProgram`.

  Example:

  ```
  experiment = Experiment()

  # Get a parameter's value
  amplitude = experiment.get_parameter(bus="drive_q0", parameter=Parameter.AMPLITUDE)

  # The returned value is of type `Variable`. It's value will be resolved during execution.
  # It can be used as usual in operations.

  # Use the variable in a SetOperation.
  experiment.set_parameter(bus="drive_q1", parameter=Parameter.AMPLITUDE, value=amplitude)

  # Use the variable in an ExecuteQProgram with the lambda syntax.
  def get_qprogram(amplitude: float, duration: int):
    square_wf = Square(amplitude=amplitude, duration=duration)

    qp = QProgram()
    qp.play(bus="readout", waveform=square_wf)
    return qp

  experiment.execute_qprogram(lambda: amplitude=amplitude: get_qprogram(amplitude, 2000))
  ```

  [#814](https://github.com/qilimanjaro-tech/qililab/pull/814)

- Added offset set and get for quantum machines (both OPX+ and OPX1000). For hardware loops there is `qp.set_offset(bus: str, offset_path0: float, offset_path1: float | None)` where `offset_path0` is a mandatory field (for flux, drive and readout lines) and `offset_path1` is only used when changing the offset of buses that have to IQ lines (drive and readout). For software loops there is `platform.set_parameter(alias=bus_name, parameter=ql.Parameter.OFFSET_PARAMETER, value=offset_value)`. The possible arguments for `ql.Parameter` are: `DC_OFFSET` (flux lines), `OFFSET_I` (I lines for IQ buses), `OFFSET_Q` (Q lines for IQ buses), `OFFSET_OUT1` (output 1 lines for readout lines), `OFFSET_OUT2` (output 2 lines for readout lines).
  [#791](https://github.com/qilimanjaro-tech/qililab/pull/791)

- Added the `Ramp` class, which represents a waveform that linearly ramps between two amplitudes over a specified duration.

  ```python
  from qililab import Ramp

  # Create a ramp waveform from amplitude 0.0 to 1.0 over a duration of 100 units
  ramp_wf = Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100)
  ```

  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- Added the `Chained` class, which represents a waveform composed of multiple waveforms chained together in time.

  ```python
  from qililab import Ramp, Square, Chained

  # Create a chained waveform consisting of a ramp up, a square wave, and a ramp down
  chained_wf = Chained(
      waveforms=[
          Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100),
          Square(amplitude=1.0, duration=200),
          Ramp(from_amplitude=1.0, to_amplitude=0.0, duration=100),
      ]
  )
  ```

  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- Added `add_block()` and `get_block()` methods to the `Calibration` class. These methods allow users to store a block of operations in a calibration file and later retrieve it. The block can be inserted into a `QProgram` or `Experiment` by calling `insert_block()`.

  ```python
  from qililab import QProgram, Calibration

  # Create a QProgram and add operations
  qp = QProgram()
  # Add operations to qp...

  # Store the QProgram's body as a block in the calibration file
  calibration = Calibration()
  calibration.add_block(name="qp_as_block", block=qp.body)

  # Retrieve the block by its name
  calibrated_block = calibration.get_block(name="qp_as_block")

  # Insert the retrieved block into another QProgram
  another_qp = QProgram()
  another_qp.insert_block(block=calibrated_block)
  ```

  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- Added routing algorithms to `qililab` in function of the platform connectivity. This is done passing `Qibo` own `Routers` and `Placers` classes,
  and can be called from different points of the stack.

The most common way to route, will be automatically through `qililab.execute_circuit.execute()`, or also from `qililab.platform.execute/compile()`. Another way, would be doing the transpilation/routing directly from an instance of the Transpiler, with: `qililab.digital.circuit_transpiler.transpile/route_circuit()` (with this last one, you can route with a different topology from the platform one, if desired, defaults to platform)

Example:

````
```python
from qibo import gates
from qibo.models import Circuit
from qibo.transpiler.placer import ReverseTraversal, Trivial
from qibo.transpiler.router import Sabre
from qililab import build_platform
from qililab.circuit_transpiler import CircuitTranspiler

# Create circuit:
c = Circuit(5)
c.add(gates.CNOT(1, 0))

### From execute_circuit:
# With defaults (ReverseTraversal placer and Sabre routing):
probabilities = ql.execute(c, runcard="./runcards/galadriel.yml", placer= Trivial, router = Sabre, routing_iterations: int = 10,)
# Changing the placer to Trivial, and changing the number of iterations:
probabilities = ql.execute(c, runcard="./runcards/galadriel.yml",

### From the platform:
# Create platform:
platform = build_platform(runcard="<path_to_runcard>")
# With defaults (ReverseTraversal placer, Sabre routing)
probabilities = platform.execute(c, num_avg: 1000, repetition_duration: 1000)
# With non-defaults, and specifying the router with kwargs:
probabilities = platform.execute(c, num_avg: 1000, repetition_duration: 1000,  placer= Trivial, router = (Sabre, {"lookahead": 2}), routing_iterations: int = 20))
# With a router instance:
router = Sabre(connectivity=None, lookahead=1) # No connectivity needed, since it will be overwritten by the platform's one
probabilities = platform.execute(c, num_avg: 1000, repetition_duration: 1000, placer=Trivial, router=router)

### Using the transpiler directly:
### (If using the routing from this points of the stack, you can route with a different topology from the platform one)
# Create transpiler:
transpiler = CircuitTranspiler(platform)
# Default Transpilation (ReverseTraversal, Sabre and Platform connectivity):
routed_circ, final_layouts = transpiler.route_circuit([c])
# With Non-Default Trivial placer, specifying the kwargs, for the router, and different coupling_map:
routed_circ, final_layouts = transpiler.route_circuit([c], placer=Trivial, router=(Sabre, {"lookahead": 2}, coupling_map=<some_different_topology>))
# Or finally, Routing with a concrete Routing instance:
router = Sabre(connectivity=None, lookahead=1) # No connectivity needed, since it will be overwritten by the specified in the Transpiler:
routed_circ, final_layouts = transpiler.route_circuit([c], placer=Trivial, router=router, coupling_map=<connectivity_to_use>)
```
````

[#821](https://github.com/qilimanjaro-tech/qililab/pull/821)

### Improvements

- Legacy linting and formatting tools such as pylint, flake8, isort, bandit, and black have been removed. These have been replaced with Ruff, a more efficient tool that handles both linting and formatting. All configuration settings have been consolidated into the `pyproject.toml` file, simplifying the project's configuration and maintenance. Integration config files like `pre-commit-config.yaml` and `.github/workflows/code_quality.yml` have been updated accordingly. Several rules from Ruff have also been implemented to improve code consistency and quality across the codebase. Additionally, the development dependencies in `dev-requirements.txt` have been updated to their latest versions, ensuring better compatibility and performance. [#813](https://github.com/qilimanjaro-tech/qililab/pull/813)

- `platform.execute_experiment()` and the underlying `ExperimentExecutor` can now handle experiments with multiple qprograms and multiple measurements. Parallel loops are also supported in both experiment and qprogram. The structure of the HDF5 results file as well as the functionality of `ExperimentResults` class have been changed accordingly. [#796](https://github.com/qilimanjaro-tech/qililab/pull/796)

- Added pulse distorsions in `execute_qprogram` for QBlox in a similar methodology to the distorsions implemented in pulse circuits. The runcard needs to contain the same structure for distorsions as the runcards for circuits and the code will modify the waveforms after compilation (inside `platform.execute_qprogram`).

  Example (for Qblox)

  ```
  buses:
  - alias: readout
    ...
    distortions:
      - name: exponential
        tau_exponential: 1.
        amp: 1.
        sampling_rate: 1.  # Optional. Defaults to 1
        norm_factor: 1.  # Optional. Defaults to 1
        auto_norm: True  # Optional. Defaults to True
      - name: bias_tee
        tau_bias_tee: 11000
        sampling_rate: 1.  # Optional. Defaults to 1
        norm_factor: 1.  # Optional. Defaults to 1
        auto_norm: True  # Optional. Defaults to True
      - name: lfilter
        a: []
        b: []
        norm_factor: 1.  # Optional. Defaults to 1
        auto_norm: True  # Optional. Defaults to True
  ```

  [#779](https://github.com/qilimanjaro-tech/qililab/pull/779)

- The execution of `QProgram` has been split into two distinct steps: **compilation** and **execution**.

  1. **Compilation**: Users can now compile a `QProgram` by calling:

  ```python
  platform.compile_qprogram(
    qprogram: QProgram,
    bus_mapping: dict[str, str] | None = None,
    calibration: Calibration | None = None
  )
  ```

  This method can be executed without being connected to any instruments. It returns either a `QbloxCompilationOutput` or a `QuantumMachinesCompilationOutput`, depending on the platform setup.

  2. **Execution**: Once the compilation is complete, users can execute the resulting output by calling:

  ```python
  platform.execute_compilation_output(
    output: QbloxCompilationOutput | QuantumMachinesCompilationOutput,
    debug: bool = False
  )
  ```

  If desired, both steps can still be combined into a single call using the existing method:

  ```python
  platform.execute_qprogram(
    qprogram: QProgram,
    bus_mapping: dict[str, str] | None = None,
    calibration: Calibration | None = None,
    debug: bool = False
  )
  ```

  [#817](https://github.com/qilimanjaro-tech/qililab/pull/817)

- Introduced settable attributes `experiment_results_base_path` and `experiment_results_path_format` in the `Platform` class. These attributes determine the directory and file structure for saving experiment results during execution. By default, results are stored within `experiment_results_base_path` following the format `{date}/{time}/{label}.h5`. [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

- Added a `save_plot=True` parameter to the `plotS21()` method of `ExperimentResults`. When enabled (default: True), the plot is automatically saved in the same directory as the experiment results. [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

### Breaking changes

- Renamed the platform's `execute_anneal_program()` method to `execute_annealing_program()` and updated its parameters. The method now expects `preparation_block` and `measurement_block`, which are strings used to retrieve blocks from the `Calibration`. These blocks are inserted before and after the annealing schedule, respectively.
  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- **Major reorganization of the library structure and runcard functionality**. Key updates include:

  - Removed obsolete instruments, such as VNAs.
  - Removed the `drivers` module.
  - Simplified the `Qblox` sequencer class hierarchy into two main classes: `QbloxSequencer` and `QbloxADCSequencer`.
  - Removed `SystemController` and `ReadoutSystemController`; buses now interface directly with instruments.
  - Introduced a new `channels` attribute to the `Bus` class, allowing specification of channels for each associated instrument.
  - Removed the `Chip` class and its related runcard settings.
  - Eliminated outdated settings, such as instrument firmware.
  - Refactored runcard settings into a modular structure with four distinct groups:
    - `instruments` and `instrument_controllers` for lab instrument setup.
    - `buses` for grouping instrument channels.
    - `digital` for digital compilation settings (e.g., Qibo circuits).
    - `analog` for analog compilation settings (e.g., annealing programs).

[#820](https://github.com/qilimanjaro-tech/qililab/pull/820)

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed typo in ExceptionGroup import statement for python 3.11+ [#808](https://github.com/qilimanjaro-tech/qililab/pull/808)

- Fixed serialization/deserialization of lambda functions, mainly used in `experiment.execute_qprogram()` method. The fix depends on the `dill` library which is added as requirement. [#815](https://github.com/qilimanjaro-tech/qililab/pull/815)
