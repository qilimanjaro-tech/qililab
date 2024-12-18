# Release dev (development release)

### New features since last release

### Improvements

- Updated qm-qua to stable version 1.2.1. And close other machines has been set to True as now it closes only stated ports.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed an issue where appending a configuration to an open QM instance left it hanging. The QM now properly closes before reopening with the updated configuration.
  [#851](https://github.com/qilimanjaro-tech/qililab/pull/851)

- Fixed an issue where turning off voltage/current source instruments would set to zero all dacs instead of only the ones specified in the runcard.
  [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

- Fixed the shareable trigger in the runcard to make every controller shareable while close other machines is set to false (current default) for QM. Improved shareable for OPX1000 as now it only requires to specify the flag on the fem. Now Octave name inside runcard requires to be the same as the one inside the configuration (now it has the same behavior as the cluster and opx controller). Modified qm Voltage_Coeficient from 2 to 1 as now the voltage defined in the config file waveforms corresponds directly to the voltage of the pulse.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)
