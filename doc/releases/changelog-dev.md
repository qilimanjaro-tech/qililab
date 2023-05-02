# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added `pulse/pulse_distortion/` module, which contains a base class to distort envelopes in PulseEvent, and two examples of distortion child classes to apply, for example:

  ```python
  pulse_event = PulseEvent(
      pulse="example_pulse",
      start_time="example_start",
      distortions=[
          BiasTeeCorrection(tau_bias_tee=1.0),
          BiasTeeCorrection(tau_bias_tee=0.8),
      ],
  )
  ```

  This would apply them like: BiasTeeCorrection_0.8(BiasTeeCorrection_1.0(original_pulse)), so the first one gets applied first and so on...
  (If you write their composition, it will be in reverse order respect the list)

  [#279](https://github.com/qilimanjaro-tech/qililab/pull/279)

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

- Added `CircuitTranspiler` class for calculating operation timings and transpiling quantum circuits into pulse operations. The `calculate_timings()` method annotates operations in the circuit with timing information by evaluating start and end times for each operation. The `remove_special_operations()` method removes special operations (Barrier, Wait, Passive Reset) from the circuit after the timings have been calculated. The `transpile_to_pulse_operations()` method then transpiles the quantum circuit operations into pulse operations, taking into account the calculated timings. Example usage:

  ```python
  # create the transpiler
  transpiler = CircuitTranspiler(settings=platform.settings)

  # calculate timings
  circuit_ir1 = transpiler.calculate_timings(circuit)

  # remove special operations
  circuit_ir2 = transpiler.remove_special_operations(circuit_ir1)

  # transpile operations to pulse operations
  circuit_ir3 = transpiler.transpile_to_pulse_operations(circuit_ir2)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

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

- Added `values` and `channel_id` attribute to the `Loop` class.
  Here is an example on how a loop is created now:

  ```python
  new_loop = Loop(alias="loop", parameter=Parameter.POWER, values=np.linspace(1, 10, 10))
  ```

  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

### Improvements

- Return an integer (instead of the `Port` class) when calling `Chip.get_port`. This is to avoid using the private
  `id_` attribute of the `Port` class to obtain the port index.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- The asynchronous data handling used to save results and send data to the live plotting has been improved. Now we are
  saving the results in a queue, and there is only ONE thread which retrieves the results from the queue, sends them to
  the live plotting and saves them to a file.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

### Breaking changes

- `draw()` method of `Circuit` uses Graphviz internally. To be able to call the method Graphviz must be installed. In Ubuntu-based distros a simple `sudo apt-get install graphviz` is sufficient. For detailed installation information for your OS please consult Graphviz's [installation page](https://graphviz.org/download/).
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

### Deprecations / Removals

- The `Execution` class has been removed. Its functionality is now added to the `ExecutionManager` class.
  Please use `ExecutionManager`instead. The `ExecutionBuilder` returns now an instance of `ExecutionManager`.
  [#246](https://github.com/qilimanjaro-tech/qililab/pull/246)

- The `LoopOptions` class has been removed. It was used to create a numpy array and store this array in the `values`
  attribute which is now in the `Loop` class.
  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- The `plot_y_label` argument of the `ExperimentOptions` class has been removed.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

### Documentation

### Bug fixes

- Fixed bug where acquisition data was not deleted when compiling the same sequence twice.
  [#264](https://github.com/qilimanjaro-tech/qililab/pull/264)

- Fixed bug where the live plotting created a new plot when using parallel loops.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)
