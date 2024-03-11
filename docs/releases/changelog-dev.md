# Release dev (development release)

### New features since last release

### Improvements

- The method `CalibrationNode._execute_notebook()` now changes the working directory to the notebook directory before the execution and restores the previous one after the papermill execution. It allows the notebooks now to use relative paths. Also, the initialization of `CalibrationNode` will now contain absolute paths for the attributes `nb_folder` and `nb_path`
  \[#693\] (https://github.com/qilimanjaro-tech/qililab/pull/693)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
