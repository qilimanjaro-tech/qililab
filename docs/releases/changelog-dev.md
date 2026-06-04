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
