# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
