# Release dev (development release)

### New features since last release

### Improvements

- Added `timeout_repetitions` parameter for QRM and QRM-RF instruments sequencers inside the runcard. This parameter controls how many (if any) executions of the same qblox qprogram execution must be done after an acquisition `TimeoutError`. Defaults to no repetitions.
In the runcard this parameter is located inside the instruments sequencer for QRM and QRM-RF modules.

  ```
    - name: QRM-RF
    alias: QRM-RF1
    ...
    awg_sequencers:
    - identifier: 0
      ...
      acquisition_timeout: 1  # In minutes
      timeout_repetitions: 3  # Optional parameter, defaults to None
      ...
  ```

  [#1106](https://github.com/qilimanjaro-tech/qililab/pull/1106)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug in `load_sequence_by_id` where measurements were returned in an undefined order, causing incorrect results when processing sequences. Measurements are now ordered by `measurement_id`.
  [#1132](https://github.com/qilimanjaro-tech/qililab/pull/1132)

- Pinned spirack to ==0.2.12 as some newer versions may cause an error when importing qblox-instruments.
  [#1135](https://github.com/qilimanjaro-tech/qililab/pull/1135)