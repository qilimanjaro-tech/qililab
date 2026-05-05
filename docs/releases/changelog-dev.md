# Release dev (development release)

### New features since last release

- Fix `qcodes` version to `0.51.0` to avoid breaking changes introduced in later releases.
  [#1092](https://github.com/qilimanjaro-tech/qililab/pull/1092)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Qblox: After each acquisition, an empty sequence is re-uploaded to ensure that bin allocation is properly reset (introduced in [this PR](https://github.com/qilimanjaro-tech/qililab/pull/1082)). Previously, the upload cache compared sequence hashes and skipped re-uploading if no changes were detected. However, since the acquisition portion of the sequence had been removed, this led to an inconsistency: the cached sequence was not re-uploaded, resulting in an error during execution.
The cache has now been removed so that the sequence is always re-uploaded, ensuring correct bin allocation and preventing this error before each run.
  [#1089](https://github.com/qilimanjaro-tech/qililab/pull/1089)

- Fixed a bug in the Qblox compiler where the bin acquisition index was not incrementing correctly when multiple `measure` calls are used sequentially inside an `average` block with an outer sweep loop.  Each sequential acquire now gets its own bin register initialised to its position offset, and the bin register is advanced by the total number of acquires per sweep step (instead of always 1), so that consecutive acquires write to consecutive bins and the full acquisition matrix is filled correctly.
  [#1101](https://github.com/qilimanjaro-tech/qililab/pull/1101)
