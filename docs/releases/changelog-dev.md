# Release dev (development release)

### New features since last release

- Add FlatTop pulse shape
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

- Add FlatTop waveform
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

- Add support for multiple QRM modules
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

- Update qpysequence to 10.1
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

### Improvements

- The method `CalibrationNode._execute_notebook()` now changes the working directory to the notebook directory before the execution and restores the previous one after the papermill execution. It allows the notebooks now to use relative paths. Also, the initialization of `CalibrationNode` will now contain absolute paths for the attributes `nb_folder` and `nb_path`
  [#693](https://github.com/qilimanjaro-tech/qililab/pull/693)

### Breaking changes

- Added support for Qblox cluster firmware v0.6.1 and qblox-instruments v0.11.2. This changes some of the i/o mappings in the runcard for qblox sequencers so  with older versions is broken.
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

### Deprecations / Removals

### Documentation

### Bug fixes

- Resolved an issue where attempting to execute a previously compiled QUA program on a newly instantiated Quantum Machine resulted in errors due to cache invalidation.
  [#706](https://github.com/qilimanjaro-tech/qililab/pull/706)
