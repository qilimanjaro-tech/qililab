# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

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

### Improvements

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

### Breaking changes

### Deprecations / Removals

- Remove the `awg_iq_channels` from the `AWG` class. This mapping was already done within each sequencer.
  [#323](https://github.com/qilimanjaro-tech/qililab/pull/323)

### Documentation

### Bug fixes

- Add `_set_markers` method to the `QbloxModule` class and enable all markers. For the RF modules, this command
  enables the outputs/inputs of the instrument. We decided to enable all markers by default to be able to use them
  later if needed.
  [#361](https://github.com/qilimanjaro-tech/qililab/pull/361)
