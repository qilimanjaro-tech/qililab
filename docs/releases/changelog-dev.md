# Release dev (development release)

### New features since last release

### Improvements

- Now the Rohde & Schwarz will return an error after a limit of frequency or power is reached based on the machine's version.
  [#897](https://github.com/qilimanjaro-tech/qililab/pull/897)

- For QBlox, it is possible to run qprograms in parallel. This can be done by giving the execute_qprograms_parallel method a list of the qprograms. It will give an error if any of the qprograms submitted share a bus.
  [#906](https://github.com/qilimanjaro-tech/qililab/pull/906)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
