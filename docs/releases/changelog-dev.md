# Release dev (development release)

### New features since last release

- Added `platform.set_calibration`, which stores a `Calibration` (given an instance or file path) on the platform. `execute_qprogram`, `execute_qprograms_parallel`, and database/stream saving now fall back to it when no `calibration` argument is passed; an explicit argument always overrides it.
  [#1165](https://github.com/qilimanjaro-tech/qililab/pull/1165)

### Improvements

- Qblox: the threshold value (`Parameter.THRESHOLD`, still set via the runcard/`set_parameter` exactly as before) is now scaled by the QProgram's actual weight duration instead of the runcard's `integration_length` field; the weight's duration is the integration length. `integration_length` in the runcard was designed for Qblox's non-weighted `acquire`, which Qililab hasn't used since the old pulse/qibo compiler was removed; now, Qililab only ever does weighted acquisitions, so scaling by the runcard field was the wrong source of truth.
  - `QProgram.qblox.weight_duration` tracks each acquisition's real weight duration, per bus.
  - Value sent to hardware = `threshold * weight_duration`, computed fresh on every execution.
  - Resolves on a copy of the QProgram, so reusing the same QProgram across different `Calibration`s is safe.
  - `bus_mapping` merges durations onto the same physical bus and resolves calibration against it.
  - Multiple durations on one bus -> a warning is logged and the first one (in order) is used.
  [#1151](https://github.com/qilimanjaro-tech/qililab/pull/1151)

### Breaking changes

### Deprecations / Removals

- The runcard's `integration_length` field (on `QbloxADCSequencer`) is deprecated and will be removed in a future release; setting it now emits a `FutureWarning`. The integration length is derived from the QProgram's weight duration instead.
  [#1151](https://github.com/qilimanjaro-tech/qililab/pull/1151)

### Documentation

### Bug fixes
