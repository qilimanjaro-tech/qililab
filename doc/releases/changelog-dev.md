# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added `experiment/portfolio/` submodule, which will contain pre-defined experiments and their analysis.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `ExperimentAnalysis` class, which contains methods used to analyze the results of an experiment.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `Rabi` portfolio experiment. Here is a usage example:

  ```python
  loop_range = np.linspace(start=0, stop=1, step=0.1)
  rabi = Rabi(platform=platform, qubit=0, range=loop_range)
  rabi.turn_on_instruments()

  bus_parameters = {Parameter.GAIN: 0.8, Parameter.FREQUENCY: 5e9}
  rabi.bus_setup(bus_parameters, control=True)  # set parameters of control bus
  x_parameters = {Parameter.DURATION: 40}
  rabi.gate_setup(x_parameters, gate="X")  # set parameters of X gate

  rabi.build_execution()
  results = rabi.run()  # all the returned values are also saved inside the `Rabi` class!
  post_processed_results = rabi.post_process_results()
  fitted_parameters = rabi.fit()
  fig = rabi.plot()
  ```

  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `FlippingSequence` portfolio experiment.
  [#245](https://github.com/qilimanjaro-tech/qililab/pull/245)

- Added `get_bus_by_qubit_index` method to the `Platform` class.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `circuit` module, which contains everything related to Qililab's internal circuit representation.

  The module contains the following submodules:

  - `circuit/converters`: Contains classes that can convert from external circuit representation to Qililab's internal circuit representation and vice versa.
  - `circuit/nodes`: Contains classes representing graph nodes that are used in circuit's internal graph data structure.
  - `circuit/operations`: Contains classes representing operations that can be added to the circuit.
    [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `Circuit` class for representing quantum circuits. The class stores the quantum circuit as a directed acyclic graph (DAG) using the `rustworkx` library for manipulation. It offers methods to add operations to the circuit, calculate the circuit's depth, and visualize the circuit. Example usage:

  ```python
  # create a Circuit with two qubits
  circuit = Circuit(2)

  # add operations
  for qubit in [0, 1]:
      circuit.add(qubit, X())
  circuit.add(0, Wait(t=100))
  circuit.add(0, X())
  circuit.add((0, 1), Measure())

  # print depth of circuit
  print(f"Depth: {circuit.depth}")

  # print circuit
  circuit.print()

  # draw circuit's graph
  circuit.draw()
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `OperationFactory` class to register and retrieve operation classes based on their names.
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `CircuitTranspiler` class for transpiling `Circuit` to `PulseSchedule`. The complete transpilation flow, that can be run by calling `transpile()` method, consists of the following steps:

  1. \_calculate_timings()
  1. \_remove_special_operations()
  1. \_transpile_to_pulse_operations()
  1. \_generate_pulse_schedule()

  The `_calculate_timings()` method annotates operations in the circuit with timing information by evaluating start and end times for each operation. The `_remove_special_operations()` method removes special operations (Barrier, Wait, Passive Reset) from the circuit after the timings have been calculated. The `_transpile_to_pulse_operations()` method then transpiles the quantum circuit operations into pulse operations, taking into account the calculated timings. The `_generate_pulse_schedule()` method produces the equivalent `PulseSchedule`. Example usage:

  ```python
  # create the transpiler
  transpiler = CircuitTranspiler(settings=platform.settings)

  # calculate timings
  circuit_ir1 = transpiler._calculate_timings(circuit)

  # remove special operations
  circuit_ir2 = transpiler._remove_special_operations(circuit_ir1)

  # transpile operations to pulse operations
  circuit_ir3 = transpiler._transpile_to_pulse_operations(circuit_ir2)

  # transpile to PulseSchedule
  pulse_schedule = transpiler._generate_pulse_schedule(circuit_ir3)

  # Alternatively, if you don't need inspection of intermediate representations you can run all steps with transpile
  pulse_schedule = transpiler.transpile(circuit)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)
  [#267](https://github.com/qilimanjaro-tech/qililab/pull/267)

- Added `QiliQasmConverter` class to convert a circuit from/to QiliQASM, an over-simplified QASM version. Example usage:

  ```python
  # Convert to QiliQASM
  qasm = QiliQasmConverter.to_qasm(circuit)
  print(qasm)

  # Parse from QiliQASM
  parsed_circuit = QiliQasmConverter.from_qasm(qasm)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Pulses with different frequencies will be automatically sent and read by different sequencers (multiplexed readout).
  [#242](https://github.com/qilimanjaro-tech/qililab/pull/242)

- Added an optional parameter "frequency" to the "modulated_waveforms" method of the Pulse and PulseEvent classes, allowing for specification of a modulation frequency different from that of the Pulse.
  [#242](https://github.com/qilimanjaro-tech/qililab/pull/242)

- Experiment can now accept both Qibo circuits and Qililab circuits.
  [#267](https://github.com/qilimanjaro-tech/qililab/pull/267)

- Added `values` and `channel_id` attribute to the `Loop` class.
  Here is an example on how a loop is created now:

  ```python
  new_loop = Loop(alias="loop", parameter=Parameter.POWER, values=np.linspace(1, 10, 10))
  ```

  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- Added support for changing operation's settings.

  ```python
  experiment.set_parameter(alias="Measure", parameter=Parameter.DURATION, value=1000)
  ```

  [#286](https://github.com/qilimanjaro-tech/qililab/issues/286)

- Added support for looping over the values of a specific group of operations in the circuit. The group is identified by the alias set when added the operation in the circuit. If more than one operations have the same alias, their values will change in sync. Example:

  ```python
  circuit = Circuit(1)
  circuit.add(0, X())
  circuit.add(0, Wait(t=0), alias="wait_operation")
  circuit.add(0, X())
  circuit.add(0, Wait(t=0), alias="wait_operation")
  circuit.add(0, Measure())

  loop = Loop(
      alias="wait_operation.t",
      parameter=Parameter.OPERATION_PARAMETER,
      values=np.linspace(0, 1000, 10),
  )
  ```

  [#286](https://github.com/qilimanjaro-tech/qililab/issues/286)

- Gate settings can be set for each qubit individually, or tuple of qubits in case of two-qubit gates.
  Example of updated runcard schema:

  ```yaml
  gates:
    0:
      - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
      - name: X
        amplitude: 1.0
        phase: 0
        duration: 100
        shape:
          name: gaussian
          num_sigmas: 4
    1:
      - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
      - name: X
        amplitude: 1.0
        phase: 0
        duration: 100
        shape:
          name: gaussian
          num_sigmas: 4
    (0,1):
      - name: CPhase
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
  ```

  To change settings with set_parameter methods, use the alias format "GATE(QUBITs)". For example:

  ```python
  platform.set_parameter(alias="X(0)", parameter=Parameter.DURATION, value=40)
  platform.set_parameter(alias="CPhase(0,1)", parameter=Parameter.DURATION, value=80)
  ```

  [#292](https://github.com/qilimanjaro-tech/qililab/pull/292)

- Weighted acquisition is supported. The weight arrays are set as sequencer parameters `weights_path0` and `weights_path1`, and the weighed acquisition can be enabled setting the sequencer parameter `weighed_acq_enabled` to `true`. Note: the `integration_length` parameter will be ignored if `weighed_acq_enabled` is set to `true`, and the length of the weights arrays will be used instead.

```yaml
awg_sequencers:
  - identifier: 0
    chip_port_id: 1
    intermediate_frequency: 1.e+08
    weights_path0: [0.98, ...]  # <-- new line
    weights_path1: [0.72, ...]  # <-- new line
    weighed_acq_enabled: true   # <-- new line
    threshold: 0.5              # <-- new line
```

[#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

- `Result`, `Results` and `Acquisitions` classes implement the `counts` method, which returns a dictionary-like object containing the counts of each measurement based in the discretization of the instrument via the `threshold` sequencer parameter. Alternatively, the `probabilities` method can also be used, which returns a normalized version of the same counts object.

  ```python
  counts = result.counts()
  probabilities = result.probabilities()

  print(f"Counts: {counts}")
  print(f"Probabilities: {probabilities}")
  ```

  Output:

  ```
  > Counts: {'00': 502, '01': 23, '10': 19, '11': 480}
  > Probabilities: {'00': 0.49023438, '01': 0.02246094, '10': 0.01855469, '11': 0.46875}
  ```

  [#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

### Improvements

- Return an integer (instead of the `Port` class) when calling `Chip.get_port`. This is to avoid using the private
  `id_` attribute of the `Port` class to obtain the port index.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- The asynchronous data handling used to save results and send data to the live plotting has been improved. Now we are
  saving the results in a queue, and there is only ONE thread which retrieves the results from the queue, sends them to
  the live plotting and saves them to a file.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

- The asynchronous data handling used to save results and send data to the live plotting has been improved.
  Previously we only had ONE active thread retrieving the results and saving them but was created and killed after processing one result of the total `Results` object. Now we are creating the thread just ONCE, so threading is handled at the `Experiment` level instead of what was done previously at the `Exution_Manager` level.
  [#298](https://github.com/qilimanjaro-tech/qililab/pull/298)

### Breaking changes

- `draw()` method of `Circuit` uses Graphviz internally. To be able to call the method Graphviz must be installed. In Ubuntu-based distros a simple `sudo apt-get install graphviz` is sufficient. For detailed installation information for your OS please consult Graphviz's [installation page](https://graphviz.org/download/).
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- `gates` property of runcard must be updated to provide a list of gate settings for each qubit individually.
  [#292](https://github.com/qilimanjaro-tech/qililab/pull/292)

### Deprecations / Removals

- The `Execution` class has been removed. Its functionality is now added to the `ExecutionManager` class.
  Please use `ExecutionManager`instead. The `ExecutionBuilder` returns now an instance of `ExecutionManager`.
  [#246](https://github.com/qilimanjaro-tech/qililab/pull/246)

- The `LoopOptions` class has been removed. It was used to create a numpy array and store this array in the `values`
  attribute which is now in the `Loop` class.
  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- The `plot_y_label` argument of the `ExperimentOptions` class has been removed.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

- All the `probabilities` methods that returned a `pandas.DataFrame` return now a `dict[str, float]`. All the methods related to the construction of such dataframes have been removed.
  [#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

### Documentation

### Bug fixes

- Fixed bug where acquisition data was not deleted when compiling the same sequence twice.
  [#264](https://github.com/qilimanjaro-tech/qililab/pull/264)

- Fixed bug where the live plotting created a new plot when using parallel loops.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)
