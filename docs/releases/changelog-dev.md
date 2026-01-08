# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Calibration file: The `with_calibration` method in `qprogram` was not storing the needed information to import blocks, this information is now being stored.
The `insert_block` method in `structured_qprogram` has been modified such that the block is flattened, hence each element is added separately, rather than adding the block. Adding the block directly was causing problems at compilation because adding twice in a single `qprogram` the same block meant they shared the same UUID.
[#1050](https://github.com/qilimanjaro-tech/qililab/pull/1050)

- QbloxDraw: Fixed two acquisition-related bugs:.
  1. Acquisition-only programs are now displayed correctly.
  2. Acquisition timing issues caused by wait instructions have been fixed.
[#1051](https://github.com/qilimanjaro-tech/qililab/pull/1051)

- QbloxDraw: Variable offsets can now be plotted.
[#1049](https://github.com/qilimanjaro-tech/qililab/pull/1049)

- Removed threading for `ExperimentExecutor()`. This feature caused a deadlock on the execution if any error is raised inside it (mainly involving the ExperimentsResultsWriter). The threading has been removed as it was only necessary for parallel time tracking.
[#1055](https://github.com/qilimanjaro-tech/qililab/pull/1055)