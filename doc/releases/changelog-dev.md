# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- The `Experiment`class has been changed to support a more general definition of experiment by removing the
  `circuits` and `pulse_schedules`. A new class `CircuitExperiment` inherits from the new `Experiment` class has the previous attributes and all the functionality the old `Experiment` had.

  ```python
  experiment = Experiment(platform=platform, options=options)
  experiment_2 = CircuitExperiment(platform=platform, options=options, circuits=[circuit])
  ```

  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

- The `VectorNetworkAnalizer` instrument is now implemented into the workflow of qililab.
  The user can now create an `Experiment` and use all qililab features. The results of experiments using the VNA will now be saved into three different files: File containing the runcard, file containing the raw data (data saved in real time) and a file containing the metadata (experiment options and loops). Here is an example of a simple experiment using the `VectorNetworkAnalizer`:

  ```python
  platform = build_platform(name="sauron_vna")  # Load the platform
  platform.connect()
  # Set some values for the VNA
  platform.set_parameter(alias="VNA", parameter=Parameter.POWER, value=-20.0)
  platform.set_parameter(
      alias="VNA", parameter=Parameter.SCATTERING_PARAMETER, value="S21"
  )
  # Define loops and options for the experiment
  loop = Loop(
      alias="vna_readout_bus", parameter=Parameter.IF_BANDWIDTH, values=[100.0, 200.0]
  )
  options = ExperimentOptions(loops=[loop], name="test_vna")
  # Create the `Experiment`
  experiment = Experiment(platform=platform, options=options)
  # Build execution (needed) and run
  experiment.build_execution()
  experiment.run()
  # Access the results
  res = experiment.results
  ```

  [#360](https://github.com/qilimanjaro-tech/qililab/pull/360)

### Improvements

- The `VNAResult` class now holds the parameters `i` and `q` obtained from the trace of the
  `VectorNetworkAnalyzer` instrument.
  [#360](https://github.com/qilimanjaro-tech/qililab/pull/360)

### Breaking changes

- Old scripts using `Experiment` with circuits should be changed and use `CircuitExperiment` instead.
  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

### Deprecations / Removals

### Documentation

### Bug fixes
