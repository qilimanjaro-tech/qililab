# Release dev (development release)

### New features since last release

- We have introduced an optimization in the QbloxCompiler that significantly reduces memory usage when compiling square waveforms. The compiler now uses a heuristic algorithm that segments long waveforms into smaller chunks and loops over them. This optimization follows a two-pass search:

  1. **First Pass**: The compiler tries to find a chunk duration that divides the total waveform length evenly (i.e., remainder = 0).
  1. **Second Pass**: If no exact divisor is found, it looks for a chunk duration that leaves a remainder of at least 4 ns. This leftover chunk is large enough to be stored or handled separately.

  Each chunk duration is restricted to the range (\[100, 500\]) ns, ensuring that chunks are neither too small (leading to excessive repetitions) nor too large (risking out-of-memory issues). If no duration within (\[100, 500\]) ns meets these remainder constraints, the compiler defaults to using the original waveform in its entirety.
  [#861](https://github.com/qilimanjaro-tech/qililab/pull/861)

- Raises an error when the inputed value for the QDAC is outside of the bounds provided by QM. Done in 3 ways, runcard, set_parameter RAMPING_ENABLED and set_parameter RAMPING_RATE.
[#865](https://github.com/qilimanjaro-tech/qililab/pull/865)

- Code to enable the IQ mixer feature already part of qcode in qililab for the rohde and schwarz SGS100a
[#872](https://github.com/qilimanjaro-tech/qililab/pull/872)

- Enable square waveforms optimization for Qblox.
[#874](https://github.com/qilimanjaro-tech/qililab/pull/874)

### Improvements

- Updated qm-qua to stable version 1.2.1. And close other machines has been set to True as now it closes only stated ports.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)

- Now the QM qprogram compiler is able to generate the correct stream_processing while the average loop is inside any other kind of loop, before it was only able to be located on the outermost loop due to the way qprogram generated the stream_processing.
  [#880](https://github.com/qilimanjaro-tech/qililab/pull/880)

### Breaking changes

### Deprecations / Removals

- Removed quick fix for the timeout error while running with QM as it has been fixed.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)

### Documentation

### Bug fixes

- Fixed an issue where having nested loops would output wrong shape in QbloxMeasurementResult.
  [#853](https://github.com/qilimanjaro-tech/qililab/pull/853)

- Restore the vna driver as it was deleted.
  [#857](https://github.com/qilimanjaro-tech/qililab/pull/857)

- Fixed an issue where appending a configuration to an open QM instance left it hanging. The QM now properly closes before reopening with the updated configuration.
  [#851](https://github.com/qilimanjaro-tech/qililab/pull/851)

- Fixed an issue where turning off voltage/current source instruments would set to zero all dacs instead of only the ones specified in the runcard.
  [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

- Fixed the shareable trigger in the runcard to make every controller shareable while close other machines is set to false (current default) for QM. Improved shareable for OPX1000 as now it only requires to specify the flag on the fem. Now Octave name inside runcard requires to be the same as the one inside the configuration (now it has the same behavior as the cluster and opx controller).
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)

- Ensured that turning on the instruments does not override the RF setting of the Rohde, which can be set to 'False' in the runcard.
  [#888](https://github.com/qilimanjaro-tech/qililab/pull/888)