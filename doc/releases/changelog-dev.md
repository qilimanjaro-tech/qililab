# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added support for setting output offsets of a qblox module.
  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

### Improvements

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
