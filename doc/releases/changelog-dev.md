# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added `experiment/portfolio/` submodule, which will contain pre-defined experiments and their analysis.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `ExperimentAnalysis` class, which contains methods used to analyze the results of an experiment.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `Rabi` portfolio experiment. Here is a usage example:

  ```python
  loop_options = LoopOptions(start=0, stop=1, step=0.1)
  rabi = Rabi(platform=platform, qubit=0, loop_options=loop_options)
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

### Improvements

- Return an integer (instead of the `Port` class) when calling `Chip.get_port`. This is to avoid using the private
  `id_` attribute of the `Port` class to obtain the port index.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
