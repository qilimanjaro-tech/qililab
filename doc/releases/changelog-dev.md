# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added support for setting output offsets of a qblox module.
  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

### Improvements

- Added support for the execution of pulses with durations that are not multiples of 4. For this, a new
  `minimum_clock_time` attribute has been added to the runcard:

  ```yaml
  settings:
    id_: 0
    category: platform
    name: spectro_v_flux
    device_id: 9
    minimum_clock_time: 4  # <-- new line!
  ```

  When a pulse has a duration that is not a multiple of the `minimum_clock_time`, a padding of 0s is added after the pulse to make sure the next pulse falls within a multiple of 4.
  [#227](https://github.com/qilimanjaro-tech/qililab/pull/227)

### Breaking changes

- An `out_offsets` attribute has been added to the settings of a `QbloxModule` object. This attribute contains a list
  of the offsets applied to each output. The runcard should be updated to contain this new information:

  ```yaml
  instruments:
    - name: QRM
    alias: QRM
    id_: 1
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    acquisition_delay_time: 100
    out_offsets: [0.3, 0, 0, 0]  # <-- this new line needs to be added to the runcard!
    awg_sequencers:
      ...
  ```

  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `PulseBusSchedule.waveforms` where the pulse time was recorded twice.
  [#227](https://github.com/qilimanjaro-tech/qililab/pull/227)
