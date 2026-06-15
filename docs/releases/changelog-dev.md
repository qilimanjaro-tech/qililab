# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Made `deserialize` / `deserialize_from` safe by default. They now load through a registry-isolated, data-only YAML loader that rejects code-execution tags (`!!python/object/apply`, `!!python/name`, `!function`, `!lambda`, and the gated `!type` / `!PydanticModel` / `!defaultdict`), so deserializing an untrusted string or file can no longer execute arbitrary code. Every legitimate round-trip (waveforms, `QProgram`, `Experiment`, `Calibration`, numpy arrays, tuples, complex numbers, UUIDs, enums) keeps working, and a `trust_code=True` opt-in restores the previous behavior for fully trusted input. This also closes the `build_platform` runcard remote-code-execution path, where a gate-event waveform/weights string reached the unsafe loader via the `GateEvent` validators.
  [#1142](https://github.com/qilimanjaro-tech/qililab/pull/1142)

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
[#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
