# Release dev (development release)

### New features since last release

- Introduced a new parameter, `disable_autosync`, to the `QProgram` constructor. This parameter allows users to control the automatic synchronization behavior of loops within their quantum programs. By default, the parameter is set to `False`, enabling the compiler to automatically insert synchronization operations at the conclusion of each loop. Users have the option to set `disable_autosync` to `True` to indicate that they prefer to manage loop timing manually. This feature is particularly useful for operations on Qblox hardware, due to its constraints on dynamic synchronization. It's important to note that Quantum Machines will disregard this setting and adhere to the default synchronization behavior.
  [#694](https://github.com/qilimanjaro-tech/qililab/pull/694)

### Improvements

### Breaking changes

- The unit of measurement for phases within QProgram has been updated from degrees to radians.
  [#695](https://github.com/qilimanjaro-tech/qililab/pull/695)

### Deprecations / Removals

### Documentation

### Bug fixes

- Resolved an issue encountered during the retrieval of results from QProgram executions on Qblox hardware, where acquisition data from other sequencers would unintentionally be deleted.
  [#691](https://github.com/qilimanjaro-tech/qililab/pull/691)
