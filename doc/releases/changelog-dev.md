# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added `T1` portfolio experiment
  [#409](https://github.com/qilimanjaro-tech/qililab/pull/409)

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

### Improvements

- Addeds support for the `Wait` gate
  [#405](https://github.com/qilimanjaro-tech/qililab/pull/405)

- Added support for `Parameter.Gate_Parameter` in `experiment.set_parameter()` method. In this case, alias is a, convertable to integer, string that denotes the index of the parameter to change, as returned by `circuit.get_parameters()` method.
  [#404](https://github.com/qilimanjaro-tech/qililab/pull/404)

### Breaking changes

- Old scripts using `Experiment` with circuits should be changed and use `CircuitExperiment` instead.
  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

### Deprecations / Removals

### Documentation

### Bug fixes
