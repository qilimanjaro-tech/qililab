# Release dev (development release)

### New features since last release

- Introduced the possibility to run multiple shots and averages at the same time for `execute_anneal_program` method.
  [#797](https://github.com/qilimanjaro-tech/qililab/pull/797)

- Introduced the `Experiment` class, which inherits from `StructuredProgram`. This new class enables the ability to set parameters and execute quantum programs within a structured experiment. Added the `set_parameter` method to allow setting platfform parameters and `execute_qprogram` method to facilitate the execution of quantum programs within the experiment.
  [#782](https://github.com/qilimanjaro-tech/qililab/pull/782)

- Introduced the `ExperimentExecutor` class to manage and execute quantum experiments within the Qililab framework. This class provides a streamlined way to handle the setup, execution, and results retrieval of experiments.

  Temporary Constraints:

  - The experiment must contain only one `QProgram`.
  - The `QProgram` must contain a single measure operation.
  - Parallel loops are not supported.
    [#790](https://github.com/qilimanjaro-tech/qililab/pull/790)

- Introduced the `platform.execute_experiment()` method for executing experiments. This method simplifies the interaction with the ExperimentExecutor by allowing users to run experiments with a single call.

  Example:

  ```Python
  # Define the QProgram
  qp = QProgram()
  gain = qp.variable(label='resonator gain', domain=Domain.Voltage)
  with qp.for_loop(gain, 0, 10, 1):
      qp.set_gain(bus="readout_bus", gain=gain)
      qp.measure(bus="readout_bus", waveform=IQPair(I=Square(1.0, 1000), Q=Square(1.0, 1000)), weights=IQPair(I=Square(1.0, 2000), Q=Square(1.0, 2000)))

  # Define the Experiment
  experiment = Experiment()
  bias_z = experiment.variable(label='bias_z voltage', domain=Domain.Voltage)
  frequency = experiment.variable(label='LO Frequency', domain=Domain.Frequency)
  experiment.set_parameter(alias="drive_q0", parameter=Parameter.VOLTAGE, value=0.5)
  experiment.set_parameter(alias="drive_q1", parameter=Parameter.VOLTAGE, value=0.5)
  experiment.set_parameter(alias="drive_q2", parameter=Parameter.VOLTAGE, value=0.5)
  with experiment.for_loop(bias_z, 0.0, 1.0, 0.1):
      experiment.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=bias_z)
      with experiment.for_loop(frequency, 2e9, 8e9, 1e9):
          experiment.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=frequency)
          experiment.execute_qprogram(qp)

  # Execute the Experiment and display the progress bar.
  # Results will be streamed to an h5 file. The path of this file is returned from the method.
  path = platform.execute_experiment(experiment=experiment, results_path="/tmp/results/")

  # Load results
  results, loops = load_results(path)
  ```

  [#790](https://github.com/qilimanjaro-tech/qililab/pull/790)

- Introduced a robust context manager `platform.session()` for managing platform lifecycle operations. The manager automatically calls `platform.connect()`, `platform.initial_setup()`, and `platform.turn_on_instruments()` to set up the platform environment before experiment execution. It then ensures proper resource cleanup by invoking `platform.turn_off_instruments()` and `platform.disconnect()` after the experiment, even in the event of an error or exception during execution. If multiple exceptions occur during cleanup (e.g., failures in both `turn_off_instruments()` and `disconnect()`), they are aggregated into a single `ExceptionGroup` (Python 3.11+) or a custom exception for earlier Python versions.

  Example:

  ```Python
  with platform.session():
    # do stuff...
  ```

  [#792](https://github.com/qilimanjaro-tech/qililab/pull/792)

- Add crosstalk compensation to `AnnealingProgram` workflow. Add methods to `CrosstalkMatrix` to ease crosstalk compensation in the annealing workflow
  [#775](https://github.com/qilimanjaro-tech/qililab/pull/775)

- Add default measurement to `execute_anneal_program()` method. This method takes now a calibration file and parameters
  to add the dispersive measurement at the end of the annealing schedule.
  [#778](https://github.com/qilimanjaro-tech/qililab/pull/778)

- Added a try/except clause when executing a QProgram on Quantum Machines cluster that controls the execution failing to perform a turning off of the instrument so the \_qm object gets
  removed. This, plus setting the close_other_machines=True by default allows to open more than one QuantumMachines VM at the same time to allow more than one experimentalist to work at the same time in the cluster.
  [#760](https://github.com/qilimanjaro-tech/qililab/pull/760/)

- Added `__str__` method to qprogram. The string is a readable qprogram.
  [#767](https://github.com/qilimanjaro-tech/qililab/pull/767)

- Added workflow for the execution of annealing programs.

  Example:

  ```Python
  import qililab as ql

  platform = ql.build_platform("examples/runcards/galadriel.yml")
  anneal_program_dict = [
    {qubit_0": {"sigma_x" : 0, "sigma_y": 0, "sigma_z": 1, "phix":1, "phiz":1},
      "qubit_1": {"sigma_x" : 0.1, "sigma_y": 0.1, "sigma_z": 0.1},
      "coupler_0_1": {"sigma_x" : 1, "sigma_y": 0.2, "sigma_z": 0.2}
     },
    {"qubit_0": {"sigma_x" : 0.1, "sigma_y": 0.1, "sigma_z": 1.1},
      "qubit_1": {"sigma_x" : 0.2, "sigma_y": 0.2, "sigma_z": 0.2},
      "coupler_0_1": {"sigma_x" : 0.9, "sigma_y": 0.1, "sigma_z": 0.1}
     },
     {"qubit_0": {"sigma_x" : 0.3, "sigma_y": 0.3, "sigma_z": 0.7},
      "qubit_1": {"sigma_x" : 0.5, "sigma_y": 0.2, "sigma_z": 0.01},
      "coupler_0_1": {"sigma_x" : 0.5, "sigma_y": 0, "sigma_z": -1}
      }
  ]

  results = platform.execute_anneal_program(anneal_program_dict=anneal_program_dict, transpiler=lambda delta, epsilon: (delta, epsilon), averages=100_000)
  ```

  Alternatively, each step of the workflow can be executed separately i.e. the following is equivalent to the above:

  ```python
  import qililab as ql

  platform = ql.build_platform("examples/runcards/galadriel.yml")
  anneal_program_dict = [...]  # same as in the above example
  # intialize annealing program class
  anneal_program = ql.AnnealingProgram(
      platform=platform, anneal_program=anneal_program_dict
  )
  # transpile ising to flux, now flux values can be accessed same as ising coeff values
  # eg. for phix qubit 0 at t=1ns anneal_program.anneal_program[1]["qubit_0"]["phix"]
  anneal_program.transpile(lambda delta, epsilon: (delta, epsilon))
  # get a dictionary {control_flux: (bus, waveform) from the transpiled fluxes
  anneal_waveforms = anneal_program.get_waveforms()
  # from here on we can create a qprogram to execute the annealing schedule
  ```

  [#767](https://github.com/qilimanjaro-tech/qililab/pull/767)

- Added `CrosstalkMatrix` class to represent and manipulate a crosstalk matrix, where each index corresponds to a bus. The class includes methods for initializing the matrix, getting and setting crosstalk values, and generating string representations of the matrix.

  Example:

  ```Python
  # Create an empty crosstalk matrix
  crosstalk_matrix = CrosstalkMatrix()

  # Add crosstalk values, where the keys are in matrix shape [row][column]
  crosstalk_matrix["bus1"]["bus2"] = 0.9
  crosstalk_matrix["bus2"]["bus1"] = 0.1

  # Alternatively, create a matrix from a collection of buses.
  # All crosstalk values are initialized to 1.0
  crosstalk_matrix = CrosstalkMatrix.from_buses({"bus1", "bus2", "bus3"})

  # Get a formatted string representation of the matrix
  #        bus1     bus2     bus3
  # bus1   \        1.0      1.0
  # bus2   1.0      \        1.0
  # bus3   1.0      1.0      \

  print(crosstalk_matrix)
  ```

- Added the Qblox-specific `set_markers()` method in `QProgram`. This method takes a 4-bit binary mask as input, where `0` means that the associated marker will be open (no signal) and `1` means that the associated marker will be closed (signal). The mapping between bit indexes and markers depends on the Qblox module that the compiled `QProgram` will run on.

  Example:

  ```Python
  qp = QProgram()
  qp.qblox.set_markers(bus='drive_q0', mask='0111')
  ```

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `set_markers_override_enabled_by_port` and `set_markers_override_value_by_port` methods in `QbloxModule` to set markers through QCoDeS, overriding Q1ASM values.
  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `from_qprogram` method to the `Counts` class to compute the counts of quantum states obtained from a `QProgram`. The `Counts` object is designed to work for circuits that have only one measurement per bus at the end of the circuit execution. It is the user's responsibility to ensure that this method is used appropriately when it makes sense to compute the state counts for a `QProgram`. Note that probabilities can easily be obtained by calling the `probabilities()` method. See an example below.

  Example:

  ```Python
  from qililab.result.counts import Counts

  qp = QProgram()
  # Define instructions for QProgram
  # ...
  qp_results = platform.execute_qprogram(qp)  # Platform previously defined
  counts_object = Counts.from_qprogram(qp_results)
  probs = counts_object.probabilities()
  ```

  [#743](https://github.com/qilimanjaro-tech/qililab/pull/743)

- Added `threshold_rotations` argument to `compile()` method in `QProgram`. This argument allows to use rotation angles on measurement instructions if not specified. Currently used to use the angle rotations specified on the runcard (if any) so the user does not have to explicitly pass it as argument to the measure instruction.  Used for classification of results in Quantum Machines's modules. The following example shows how to specify this value on the runcard.

  Example:

  ```JSON
  buses:
  - alias: readout_q0_bus
    system_control:
      name: readout_system_control
      instruments: [QMM]
    port: readout_line_q0
    distortions: []
  ...
  instruments:
    - name: quantum_machines_cluster
      alias: QMM
      firmware: ...
      ...
      elements:
      - bus: readout_q0_bus
        rf_inputs:
          octave: octave1
          port: 1
        rf_outputs:
          octave: octave1
          port: 1
        time_of_flight: 160
        smearing: 0
        intermediate_frequency: 10.0e+6
        threshold_rotation: 0.5
        threshold: 0.03
      ...
  ```

  [#759](https://github.com/qilimanjaro-tech/qililab/pull/759)

- Added `thresholds` argument to `_execute_qprogram_with_quantum_machines` method in `Platform`. This argument allows to threshold results after the execution of the `QProgram`. It is also a new parameter that can be specified on the runcard for each readout bus. An example of the configuration of this parameter on the runcard can be found above.
  [#762](https://github.com/qilimanjaro-tech/qililab/pull/762)

- Added `filter` argument inside the qua config file compilation from runcards with qm clusters. This is an optional element for distorsion filters that includes feedforward and feedback, two distorion lists for distorsion compensation and fields in qua config filter. These filters are calibrated and then introduced as compensation for the distorsions of the pulses from external sources such as Bias T. The runcard now might include the new filters (optional):

  Example:

  ```
  instruments:
  - name: quantum_machines_cluster
    alias: QMM
    firmware: 0.7.0
    ...
    controllers:
        - name: con1
          analog_outputs:
          - port: 1
            offset: 0.0
            filter:
              feedforward: [0.1,0.1,0.1]
              feedback: [0.1,0.1,0.1]
    ...
  ```

  [#768](https://github.com/qilimanjaro-tech/qililab/pull/768)

- Added loopbacks in the octave config file for qua following the documentation at https://docs.quantum-machines.co/1.2.0/qm-qua-sdk/docs/Guides/octave/?h=octaves#setting-the-octaves-clock. By default only port 1 of the octave is linked with a local demodulator, to work with the rest of the ports at the back ports must be connected based on the Octave Block Diagram \[https://docs.quantum-machines.co/1.2.0/qm-qua-sdk/docs/Hardware/octave/#octave-block-diagram\]. Where `Synth` is one of the possible 3 synths and `Dmd` is one of the 2 demodulators.

  Example:

  ```
  - name: quantum_machines_cluster
      alias: QMM
      ...
      octaves:
        - name: octave1
          port: 11252
          ...
          loopbacks:
            Synth: Synth2 # Synth1, Synth2, Synth3
            Dmd: Dmd2LO # Dmd1LO, Dmd2LO
  ```

  [#770](https://github.com/qilimanjaro-tech/qililab/pull/770)

### Improvements

- Improve Crosstalk matrix `from_buses` method so it can be a dictionary of buses and crosstalks coefficients.
  \[#784\]https://github.com/qilimanjaro-tech/qililab/pull/784

- Now platform.get_parameter works for QM without the need of connecting to the machine.

- Added the option to get the time of flight and smearing information from the QM cluster
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.
  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Automatic method to implement the correct `upsampling_mode` when the output mode is selected as `amplified` (fluxes), the `upsampling_mode` is automatically defined as `pulse`. In this mode, the upsampling is optimized to produce cleaner step responses.
  [#783](https://github.com/qilimanjaro-tech/qililab/pull/783)

- Automatic method for `execute_qprogram` in quantum machines to restart the measurement in case the `StreamProcessingDataLossError` is risen by `qua-qm`, the new feature allows to try again the measurement a number of times equal to the value of `dataloss_tries` (default of three). We can define this value at `execute_qprogram(..., dataloss_tries = N)` and will only do its intended job in case of working with QM.
  [#788](https://github.com/qilimanjaro-tech/qililab/pull/788)

### Breaking changes

- Big code refactor for the `calibration` module/directory, where all `comparisons`, `check_parameters`, `check_data()`,
  `check_state()`, `maintain()`, `diagnose()` and other complex unused methods have been deleted, leaving only linear calibration.

  Also some other minor improvements like:

  - `drift_timeout` is now a single one for the full controller, instead of a different one for each node.
  - Notebooks without an export are also accepted now (we will only raise error for multiple exports in a NB).
  - Extended/Improved the accepted type for parameters to input/output in notebooks, thorught json serialization.
    [#746](https://github.com/qilimanjaro-tech/qililab/pull/746)

- Variables in `QProgram` and `Experiment` now require a label.

  ```Python
  qp = QProgram()
  gain = qp.variable(label="gain", domain=Domain.Voltage)
  ```

  [#790](https://github.com/qilimanjaro-tech/qililab/pull/790)

### Deprecations / Removals

- Deleted all the files in `execution` and `experiment` directories (Already obsolete).
  [#749](https://github.com/qilimanjaro-tech/qililab/pull/749)

### Documentation

### Bug fixes

- get_parameter for QM did not work due to the lack of the variable `bus_alias in self.system_control.get_parameter`. The variable has been added to the function and now get parameter does not return a crash.
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- set_parameter for intermediate frequency in quantum machines has been adapted for both OPX+ and OPX1000 following the new requirements for OPX1000 with qm-qua job.set_intermediate_frequency.
  [#764](https://github.com/qilimanjaro-tech/qililab/pull/764)
