# Release dev (development release)

### New features since last release

- We have introduced an optimization in the QbloxCompiler that significantly reduces memory usage when compiling square waveforms. The compiler now uses a heuristic algorithm that segments long waveforms into smaller chunks and loops over them. This optimization follows a two-pass search:

  1. **First Pass**: The compiler tries to find a chunk duration that divides the total waveform length evenly (i.e., remainder = 0).
  1. **Second Pass**: If no exact divisor is found, it looks for a chunk duration that leaves a remainder of at least 4 ns. This leftover chunk is large enough to be stored or handled separately.

  Each chunk duration is restricted to the range (\[100, 500\]) ns, ensuring that chunks are neither too small (leading to excessive repetitions) nor too large (risking out-of-memory issues). If no duration within (\[100, 500\]) ns meets these remainder constraints, the compiler defaults to using the original waveform in its entirety.
  [#861](https://github.com/qilimanjaro-tech/qililab/pull/861)
  [#895](https://github.com/qilimanjaro-tech/qililab/pull/895)

- Raises an error when the inputed value for the QDAC is outside of the bounds provided by QM. Done in 3 ways, runcard, set_parameter RAMPING_ENABLED and set_parameter RAMPING_RATE.
  [#865](https://github.com/qilimanjaro-tech/qililab/pull/865)

- Enable square waveforms optimization for Qblox.
  [#874](https://github.com/qilimanjaro-tech/qililab/pull/874)

- Implemented ALC, IQ wideband and a function to see the RS models inside the drivers for SGS100a.
  [#894](https://github.com/qilimanjaro-tech/qililab/pull/894)

- Implemented Crosstalk automatic implementation through the experiment class. The crosstalk can be added through the `Calibration` file or by creating a `CrosstalkMatrix`. The crosstalk implementation inside the `Experiment` class while not using `Calibration` should be similar to this:

```
experiment = ql.Experiment(label="liveplot_test")

flux_x = experiment.variable("flux_x", ql.Domain.Flux)
flux_z = experiment.variable("flux_z", ql.Domain.Flux)

experiment.crosstalk(crosstalk=crosstalk_matrix)  # to see the values to be applied on the sample
with experiment.for_loop(variable=flux_x, start=0, stop=0.4, step=0.01):
    with experiment.for_loop(variable=flux_z, start=0, stop=0.4, step=0.01):
        experiment.set_parameter(alias="flux_x1", parameter=ql.Parameter.FLUX, value=flux_x)
        experiment.set_parameter(alias="flux_z1", parameter=ql.Parameter.FLUX, value=flux_z)
        experiment.execute_qprogram(qp)
```

With `Calibration` the code does not need to call for `experiment.crosstalk`:

```
experiment = ql.Experiment(label="liveplot_test", calibration=calibration)

flux_x = experiment.variable("flux_x", ql.Domain.Flux)
flux_z = experiment.variable("flux_z", ql.Domain.Flux)

with experiment.for_loop(variable=flux_x, start=0, stop=0.4, step=0.01):
    with experiment.for_loop(variable=flux_z, start=0, stop=0.4, step=0.01):
        experiment.set_parameter(alias="flux_x1", parameter=ql.Parameter.FLUX, value=flux_x)
        experiment.set_parameter(alias="flux_z1", parameter=ql.Parameter.FLUX, value=flux_z)
        experiment.execute_qprogram(qp)
```

Note that not giving a crosstalk matrix implies working with the identity. Warnings rise while creating the experiment to inform the user of this.
[#899](https://github.com/qilimanjaro-tech/qililab/pull/899)

- Implemented crosstalk to the `platform.set_parameter` function through the parameter `Parameter.FLUX`. This flux parameter automatically applies the crosstalk calibration upon the implied fluxes and executes a `set_parameter` with `Parameter.VOLTAGE`, `Parameter.CURRENT` or `Parameter.OFFSET` depending on the instrument of the bus.
Two new functions have been implemented inside platform: `add_crosstalk()`, to add either the `CrosstalkMatrix` or the `Calibration` file and `set_flux_to_zero()`, to set all fluxes to 0 applying a `set_parameter(bus, parameter.FLUX, 0)` for all relevant busses
An example of this implementation would be:

```
platform.add_crosstalk(crosstalk_matrix)
platform.set_parameter("flux_ax_ac", ql.Parameter.FLUX, 0.1)
platform.set_flux_to_zero()
```

[#899](https://github.com/qilimanjaro-tech/qililab/pull/899)

### Improvements

- Updated qm-qua to stable version 1.2.1. And close other machines has been set to True as now it closes only stated ports.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)

- Improvements to Digital Transpilation:

  - Move `optimize` flag, for actual optional optimizations (& Improve `optimize` word use in methods names)
  - Make `Transpilation`/`execute`/`compile` only for single circuits (unify code standard across `qililab`)
  - Make `Transpilation` efficient, by not constructing the `Circuit` class so many times, between methods
  - Pass a transpilation `kwargs` as a TypedDict instead of so many args in `platform`/`qililab`'s `execute(...)`
  - Improve documentation on transpilation, simplifying it in `execute()`'s, and creating Transpilation new section.

  [#862](https://github.com/qilimanjaro-tech/qililab/pull/862)

- Added optimizations for Digital Transpilation for Native gates:

  - Make bunching of consecutive Drag Gates, with same phi's
  - Make the deletion of gates with no amplitude

  [#863](https://github.com/qilimanjaro-tech/qililab/pull/863)

- Improved the layout information display and Updated qibo version to the last version (0.2.15), which improves layout handling
  [#869](https://github.com/qilimanjaro-tech/qililab/pull/869)

- Now the QM qprogram compiler is able to generate the correct stream_processing while the average loop is inside any other kind of loop, before it was only able to be located on the outermost loop due to the way qprogram generated the stream_processing.
  [#880](https://github.com/qilimanjaro-tech/qililab/pull/880)

- The user is now able to only put one value when setting the offset of the bus when using Qblox in the qprogram. Qblox requires two values hence if only 1 value is given, the second will be set to 0, a warning will be given to the user.
  [#896](https://github.com/qilimanjaro-tech/qililab/pull/896)

- For Qblox compiler, all latched parameters are updated before a wait is applied. The update parameter has a minimum wait of 4 ns, which is removed from the wait. If the wait is below 8ns it is entirely replaced with the update parameter.
  [#898](https://github.com/qilimanjaro-tech/qililab/pull/898)

- Modified the `CrosstalkMatrix` and `FluxVector` classes to fit for the crosstalk matrix implementation inside `Experiment` and `Platform`. Now both classes update following the specifications and needs of experimentalists.
[#899](https://github.com/qilimanjaro-tech/qililab/pull/899)

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
