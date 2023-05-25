# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added `lambda_2` attribute to the `cosine.py` module containing the `Cosine` pulse_shape, modifying the previous A/2\*(1-cos(x)).
  Into a more general A/2\*(1-lambda_1*cos(phi)-lambda_2*cos(2phi)), giving a modified sinusoidal-gaussian.

  - lambda_1 cosine A/2\*(1-cos(x)): Starts at height 0 (phase=0), maximum height A (phase=pi)
    and ends at height 0 (phase=2pi). Which is a sinusoidal like gaussian.

  - lambda_2 cosine A/2\*(1-cos(2x)): Starts at height 0 (phase=0), maximum height A (phase=pi/2)
    then another height 0 in the middle at phase=pi, then another maximum height A (phase=3/2pi)
    and ends at height 0 (phase=2pi).

  For more info check the docstring and the following references:

  - Supplemental material B. "Flux pulse parametrization" at \[<https://arxiv.org/abs/1903.02492%5C%5D>\],
  - OPTIMAL SOLUTION: SMALL CHANGE IN θ at \[<https://arxiv.org/abs/1402.5467%5C%5D>\]

  [#385](https://github.com/qilimanjaro-tech/qililab/pull/385)

- Added user integration for `pulse_distortions`. Now they can be used writing them in the Buses of the runcards:

  ```python
  buses:
    - id_: 0
      category: bus
      alias: feedline_bus
      system_control:
        id_: 0
        name: readout_system_control
        category: system_control
        instruments: [QRM1, rs_1]
      port: 100
      distortions: # <-- new line
        - name: bias_tee # <-- new line
          tau_bias_tee: 1.0 # <-- new line
        - name: lfilter # <-- new line
          a: [0.1, 1.1] # <-- new line
          b: [1.1, 1.3] # <-- new line
    - id_: 10
      category: bus
      alias: drive_line_q0_bus
      system_control:
        id_: 10
        name: system_control
        category: system_control
        instruments: [QCM-RF1]
      port: 10
      distortions: [] # <-- new line
  ```

  [#372](https://github.com/qilimanjaro-tech/qililab/pull/372)

- Added CZ gate support, 2 qubit gate support to `circuit_to_pulse` and corresponding definitions to the runcard.

  CZ implements a Sudden Net Zero (SNZ) pulse through the flux line as well as a parking gate (if defined in the runcard)
  to adjacent qubits with lower frequency than CZ's target qubit.
  For the parking gate, if the time is greater than the CZ pulse, the extra time is added as padding at the beginning/end
  of the pulse.
  The parameters for the CZ in the runcard are amplitude, duration *of the halfpulse*; and for the CZ's snz pulse b
  (impulse between halfpulses) and t_phi (time between halfpulses without accounting for b)

  Example:

  ```yaml
  gates:
   1:
     - name: Park
       amplitude: 1.0
       phase: 0
       duration: 103
       shape:
         name: rectangular

   (0,2):
     - name: CZ
       amplitude: 1.0
       phase:
       duration: 40
       shape:
         name: snz
         b: 0.5
         t_phi: 1
  ```

  In the example above, if qubit 1 is connected to 2 and has lower frequency, there will be an attempt to apply a parking
  pulse. If a Park gate definition is found for qubit 1, then a parking pulse will be applied.
  The total duration of the CZ gate above will be 2\*duration + t_phi + 2 = 83 (each b has 1ns duration and there are 2 bs).
  Thus the parking gate lasts for some extra 20ns which will result in 10ns 'pad time' in the parking gate before and after
  the SNZ pulse.
  Note that the order of the qubits in the CZ is important even if the gate is symmetric, because the second qubit will be
  the target for the SNZ pulse.
  [#369](https://github.com/qilimanjaro-tech/qililab/pull/369/)

- Added `cosine.py` module containing a `Cosine` child class of `pulse_shape`, which gives a sinusoidal like gaussian A/2\*(1-cos(x)).
  The shape starts at height 0 (phase=0), maximum height A (phase=pi) and ends at height 0 (phase=2pi)

  ```python
  pulse = Pulse(
      amplitude=...,
      phase=...,
      duration=...,
      frequency=...,
      pulse_shape=Cosine(),
  )
  ```

  [#376](https://github.com/qilimanjaro-tech/qililab/pull/376)

- Added `pulse.pulse_distortion.lfilter_correction.py` module, which is another child class for the `pulse.pulse_distortion` package.

  ```python
  distorted_envelope = LFilter(norm_factor=1.2, a=[0.7, 1.3], b=[0.5, 0.6]).apply(
      original_envelopes
  )
  ```

  Also adds a phase property to `PulseEvent` and implements `Factory.get` directly in the `from_dict()` method of the parent class `PulseDistortion`.

  [#354](https://github.com/qilimanjaro-tech/qililab/pull/354)

- Added `get_port_from_qubit_idx` method to `Chip` class. This method takes the qubit index and the line type as arguments and returns the associated port.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

- Added `pulse.pulse_distortion` package, which contains a module `pulse_distortion.py` with the base class to distort envelopes in `PulseEvent`, and two modules `bias_tee_correction.py` and `exponential_decay_correction.py`, each containing examples of distortion child classes to apply. This new feature can be used in two ways, directly from the class itself:

  ```python
  distorted_envelope = BiasTeeCorrection(tau_bias_tee=1.0).apply(original_envelope)
  ```

  or from the class PulseEvent (which ends up calling the previous one):

  ```python
  pulse_event = PulseEvent(
      pulse="example_pulse",
      start_time="example_start",
      distortions=[
          BiasTeeCorrection(tau_bias_tee=1.0),
          BiasTeeCorrection(tau_bias_tee=0.8),
      ],
  )
  distorted_envelope = pulse_event.envelope()
  ```

  This would apply them like: BiasTeeCorrection_0.8(BiasTeeCorrection_1.0(original_pulse)), so the first one gets applied first and so on...
  (If you write their composition, it will be in reverse order respect the list)

  Also along the way modified/refactored the to_dict() and from_dict() and envelope() methods of PulseEvent, Pulse, PulseShape... since they had some bugs, such as:

  - the dict() methods edited the external dictionaries making them unusable two times.
  - the maximum of the envelopes didn't correspond to the given amplitude.

  [#294](https://github.com/qilimanjaro-tech/qililab/pull/294)

- The `QbloxQCMRF` module has been added. To use it, please use the `QCM-RF` name inside the runcard:

  ```yaml
  - name: QCM-RF
    alias: QCM-RF0
    id_: 2
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    out0_lo_freq: 3700000000  # <-- new line
    out0_lo_en: true  # <-- new line
    out0_att: 10  # <-- new line
    out0_offset_path0: 0.2  # <-- new line
    out0_offset_path1: 0.07  # <-- new line
    out1_lo_freq: 3900000000  # <-- new line
    out1_lo_en: true  # <-- new line
    out1_att: 6  # <-- new line
    out1_offset_path0: 0.1  # <-- new line
    out1_offset_path1: 0.6  # <-- new line
    awg_sequencers:
      ...
  ```

  [#327](https://github.com/qilimanjaro-tech/qililab/pull/327)

- The `QbloxQRMRF` module has been added. To use it, please use the `QRM-RF` name inside the runcard:

  ```yaml
  - name: QRM-RF
    alias: QRM-RF0
    id_: 0
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    out0_in0_lo_freq: 3000000000  # <-- new line
    out0_in0_lo_en: true  # <-- new line
    out0_att: 34  # <-- new line
    in0_att: 28  # <-- new line
    out0_offset_path0: 0.123  # <-- new line
    out0_offset_path1: 1.234  # <-- new line
    acquisition_delay_time: 100
    awg_sequencers:
      ...
  ```

  [#330](https://github.com/qilimanjaro-tech/qililab/pull/330)

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

- The `get_bus_by_qubit_index` method of `Platform` class now returns a tuple of three buses: `flux_bus, control_bux, readout_bus`.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

- Arbitrary mapping of I/Q channels to outputs is now possible with the Qblox driver. When using a mapping that is not
  possible in hardware, the waveforms of the corresponding paths are swapped (in software) to allow it. For example,
  when loading a runcard with the following sequencer mapping a warning should be raised:

  ```yaml
  awg_sequencers:
  - identifier: 0
    output_i: 1
    output_q: 0
  ```

  ```pycon
  >>> platform = build_platform(name=runcard_name)
  [qililab] [0.16.1|WARNING|2023-05-09 17:18:51]: Cannot set `output_i=1` and `output_q=0` in hardware. The I/Q signals sent to sequencer 0 will be swapped to allow this setting.
  ```

  Under the hood, the driver maps `path0 -> output0` and `path1 -> output1`.
  When applying an I/Q pulse, it sends the I signal through `path1` and the Q signal through `path0`.
  [#324](https://github.com/qilimanjaro-tech/qililab/pull/324)

- The versions of the `qblox-instruments` and `qpysequence` requirements have been updated to `0.9.0`
  [#337](https://github.com/qilimanjaro-tech/qililab/pull/337)

- Allow uploading negative envelopes on the `QbloxModule` class.
  [#356](https://github.com/qilimanjaro-tech/qililab/pull/356)

- The parameter `sync_en` of the Qblox sequencers is now updated automatically when uploading a program to a sequencer.
  This parameter can no longer be set using `set_parameter`.
  [#353](https://github.com/qilimanjaro-tech/qililab/pull/353)

- The `VNAResult` class now holds the parameters `i` and `q` obtained from the trace of the
  `VectorNetworkAnalyzer` instrument.
  [#360](https://github.com/qilimanjaro-tech/qililab/pull/360)

### Breaking changes

- Old scripts using `Experiment` with circuits should be changed and use `CircuitExperiment` instead.
  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

### Deprecations / Removals

- Remove the `awg_iq_channels` from the `AWG` class. This mapping was already done within each sequencer.
  [#323](https://github.com/qilimanjaro-tech/qililab/pull/323)

- Remove the `get_port` method from the `Chip` class.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

### Documentation

### Bug fixes

- Add `_set_markers` method to the `QbloxModule` class and enable all markers. For the RF modules, this command
  enables the outputs/inputs of the instrument. We decided to enable all markers by default to be able to use them
  later if needed.
  [#361](https://github.com/qilimanjaro-tech/qililab/pull/361)
