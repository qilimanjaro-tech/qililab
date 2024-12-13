# Release dev (development release)

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed an issue where appending a configuration to an open QM instance left it hanging. The QM now properly closes before reopening with the updated configuration.
  [#851](https://github.com/qilimanjaro-tech/qililab/pull/851)

- Fixed an issue where turning off voltage/current source instruments would set to zero all dacs instead of only the ones specified in the runcard.
  [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

- Fixed the shareable trigger in the runcard to make every controller shareable while close other machines is set to false (current default) for QM. Improved shareable for OPX1000 as now it only requires to specify the flag on the fem.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)
