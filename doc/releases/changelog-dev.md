# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Fix: add checking to add only present submodules in Cluster
  [#461](https://github.com/qilimanjaro-tech/qililab/pull/461)

- Fix: add acquisitions and weights to Sequencer QRM
  [#461](https://github.com/qilimanjaro-tech/qililab/pull/461)

- Add QProgram for developing quantum programs in the bus level, the operations `Play`, `Sync`, `Wait`, `Acquire`, `SetGain`, `SetOffset`, `SetFrequency`, `SetPhase`, `ResetPhase`, and the iteration blocks `AcquireLoop` and `Loop`.
  [452](https://github.com/qilimanjaro-tech/qililab/pull/452)

- Add waveforms for the new QProgram
  [456](https://github.com/qilimanjaro-tech/qililab/pull/456)

- Add interface for Voltage and Current sources
  [#448](https://github.com/qilimanjaro-tech/qililab/pull/448)

- New AWG Interface + SequencerQCM, Pulsar, QCM-QRM drivers
  [#442](https://github.com/qilimanjaro-tech/qililab/pull/442)

- New Digitiser interface + SequencerQRM driver
  [#443](https://github.com/qilimanjaro-tech/qililab/pull/442)

- Add interface for the Attenuator.
  This is part of the "Promoting Modular Autonomy" epic.
  [#432](https://github.com/qilimanjaro-tech/qililab/pull/432)

- Added new drivers for Local Oscillators inheriting from QCoDeS drivers and Local Oscillator interface.
  This is part of the "Promoting Modular Autonomy" epic.
  [#437](https://github.com/qilimanjaro-tech/qililab/pull/437)

- Add qcodes_contrib_drivers (0.18.0) to requierements
  [#440](https://github.com/qilimanjaro-tech/qililab/pull/440)

- Update qcodes to latest current version (0.38.1)
  [#431](https://github.com/qilimanjaro-tech/qililab/pull/431)

- Added hotfix for bus delay issue from Hardware:
  This fix adds a delay for each pulse on a bus
  [#439](https://github.com/qilimanjaro-tech/qililab/pull/439)

- Added `T1` portfolio experiment
  [#409](https://github.com/qilimanjaro-tech/qililab/pull/409)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- Added `T2Echo` portfolio experiment
  [#415](https://github.com/qilimanjaro-tech/qililab/pull/415)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- The `Experiment` class has been changed to support a more general definition of experiment by removing the
  `circuits` and `pulse_schedules`. A new class `CircuitExperiment` inherits from the new `Experiment` class has the previous attributes and all the functionality the old `Experiment` had.

  ```python
  experiment = Experiment(platform=platform, options=options)
  experiment_2 = CircuitExperiment(platform=platform, options=options, circuits=[circuit])
  ```

  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

- Added `threshold_rotation` parameter to `AWGADCSequencer`. This adds a new parameter to the runcard of sequencers of that type, QRM sequencers in the case of Qblox. This value is an angle expressed in degrees from 0.0 to 360.0.

  ```yml
  awg_sequencers:
    - identifier: 0
      chip_port_id: 1
      intermediate_frequency: 1.e+08
      weights_path0: [0.98, ...]
      weights_path1: [0.72, ...]
      weighed_acq_enabled: true
      threshold: 0.5
      threshold_rotation: 45.0 # <-- new line
  ```

  [#417](https://github.com/qilimanjaro-tech/qililab/pull/417)

### Improvements

- Allow CZ gates to use different pulse shapes
  [#406](https://github.com/qilimanjaro-tech/qililab/pull/406)

- Add support for the `Wait` gate

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
