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

  Also along the way modified/refactored the to_dict() and from_dict() methods of PulseEvent, Pulse, PulseShape...

  [#279](https://github.com/qilimanjaro-tech/qililab/pull/279)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
