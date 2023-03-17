# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added new ChangeLog!
  [#170](https://github.com/qilimanjaro-tech/qililab/pull/170)

### Improvements

- Cast `chip` dictionary into the `ChipSchema` class and remove unused `InstrumentControllerSchema` class.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

- Change `schedule_index_to_load` argument to `idx` for more readability.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

### Breaking changes

- Remove context manager from `Execution` class. Users will be responsible for turning off and disconnecting the
  instruments when not using the `execute` method directly!
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

### Deprecations / Removals

- Remove `ExecutionPreparation` class, and replace it with a `prepare_results` function inside the `experiments` folder.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Remove unused `connect`, `disconnect` and `setup` methods from the `Execution` class. These are used in the
  `Experiment` class, which call the corresponding methods of the `Platform` class.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Remove the `RemoteAPI` class. This class didn't add any functionality.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Remove the `ExecutionOptions` class. Now the user can freely choose which steps of the workflow to execute.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Remove the `Platform.connect_and_initial_setup` method.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

### Documentation

### Bug fixes

- Fix bug where calling `set_parameter` with `Parameter.DRAG_COEFFICIENT` would raise an error.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

- The `qibo` version has been downgraded to `0.1.10` to allow installation on Mac laptops.
  [#185](https://github.com/qilimanjaro-tech/qililab/pull/185)
