# Release dev (development release)

### New features since last release

- [#689](https://github.com/qilimanjaro-tech/qililab/pull/689) Qililab translates any circuits supported by `qbraid` at `platform.execute` and at `ql.execute` levels, before execution and also now`ql.execute` , accepts `PulseSchedules | Circuits` and `lists`, `tuples` or any `iterable` of them, like the `platform.execute`.

### Improvements

- The method `CalibrationNode._execute_notebook()` now changes the working directory to the notebook directory before the execution and restores the previous one after the papermill execution. It allows the notebooks now to use relative paths. Also, the initialization of `CalibrationNode` will now contain absolute paths for the attributes `nb_folder` and `nb_path`
  [#693](https://github.com/qilimanjaro-tech/qililab/pull/693)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Resolved an issue where attempting to execute a previously compiled QUA program on a newly instantiated Quantum Machine resulted in errors due to cache invalidation.
  [#706](https://github.com/qilimanjaro-tech/qililab/pull/706)
