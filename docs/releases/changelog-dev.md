# Release dev (development release)

### New features since last release

### Improvements

- The tests for `QbloxDraw` have been modified such that the plots don't open on the user's browser when running pytests via VSCode.
  [#924](https://github.com/qilimanjaro-tech/qililab/pull/924)

- Github Actions now use `pytest-xdist` plugin to run tests in parallel. To run tests in parallel locally use `uv run pytest -n auto --dist loadfile`. The `--dist loadfile` flag is mandatory to avoid conflicts between tests that edit shared data, and should be planned for removal in the future.
  [#925](https://github.com/qilimanjaro-tech/qililab/pull/925)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
- For the rohde SGS100A, a line was missing in the driver causing the settings to not be updated when being set, this has been fixed.
[#927](https://github.com/qilimanjaro-tech/qililab/pull/927)