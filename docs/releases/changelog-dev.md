# Release dev (development release)

### New features since last release


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

With `Calibration`, `experiment.crosstalk` requires the calibration file:

```
experiment = ql.Experiment(label="liveplot_test")

flux_x = experiment.variable("flux_x", ql.Domain.Flux)
flux_z = experiment.variable("flux_z", ql.Domain.Flux)

experiment.crosstalk(calibration=calibration)
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

- Now the Rohde & Schwarz will return an error after a limit of frequency or power is reached based on the machine's version.
  [#897](https://github.com/qilimanjaro-tech/qililab/pull/897)

- Modified the `CrosstalkMatrix` and `FluxVector` classes to fit for the crosstalk matrix implementation inside `Experiment` and `Platform`. Now both classes update following the specifications and needs of experimentalists.
[#899](https://github.com/qilimanjaro-tech/qililab/pull/899)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
