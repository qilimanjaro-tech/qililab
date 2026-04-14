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