# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Hardened the live-plot Dash server: it now binds to loopback (`127.0.0.1`) by default instead of all interfaces. Routable exposure (for cross-node SLURM viewing) is opt-in via `QILILAB_EXPERIMENT_LIVE_PLOT_HOST` and must be fronted by an authenticated reverse proxy, since the server has no authentication of its own. The absolute result-file path was also removed from the live-plot page title.
[#1143](https://github.com/qilimanjaro-tech/qililab/pull/1143)

- Fixed a bug for `ExperimentExecutor`'s `_inclusive_range` function where the range for certain loops had overflows and didn't match the experimental result. Now it matches the `QProgram`'s result shape.
[#1066](https://github.com/qilimanjaro-tech/qililab/pull/1066)
