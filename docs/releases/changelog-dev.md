# Release dev (development release)

### New features since last release

### Improvements

- Now the Rohde & Schwarz will return an error after a limit of frequency or power is reached based on the machine's version.
  [#897](https://github.com/qilimanjaro-tech/qililab/pull/897)

- QBlox: Added support for executing multiple QProgram instances in parallel via the new method `platform.execute_qprograms_parallel(qprograms: list[QProgram])`. This method returns a list of `QProgramResults` corresponding to the input order of the provided qprograms. Note that an error will be raised if any submitted qprograms share a common bus.

  ```python
  with platform.session():
    results = platform.execute_qprograms_parallel([qprogram1, qprogram2, qprogram3])
  ```
  [#906](https://github.com/qilimanjaro-tech/qililab/pull/906)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
