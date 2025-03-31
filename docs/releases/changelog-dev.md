# Release dev (development release)

### New features since last release

- Implemented automatic mixers calibration for Qblox RF modules. There are to ways to use it. The first one is by setting a parameter in the runcard, which indicates when and which type of calibration is ran.

For the QRM-RF module the parameter is `out0_in0_lo_freq_cal_type_default`, and the values it can take are `off`, `lo` and `lo_and_sidebands`. The first one is the default value, if set the instrument won't do any automatic mixers calibration on its own, to avoid unexpected behaviours by default. The second value will suppress the leakage in the LO, and the third one the LO plus the sidebands. The parameter that will trigger this autocalibration everytime is changed in the instrument is `out0_in0_lo_freq`.

For the QCM-RF module the parameters in the runcard are `out0_lo_freq_cal_type_default` and `out1_lo_freq_cal_type_default`, and the values are the same one that for the QRM-RF described above. The parameters that will trigger this autocalibration everytime is changed in the instrument are `out0_lo_freq`  and `out1_lo_freq`.

The second way to use this autocalibration is to trigger it manually using the `Platform` instance by calling its method `Platform.calibrate_mixers()`. As input parameters you will need to specify the `alias` for the bus where the RF instrument is, the `cal_type` which allows to specify one of the three values described above, and the `channel_id` for which mixer you would like to calibrate.


```
channel_id = 0
cal_type = "lo"
alias_drive_bus = "drive_line_q1_bus"

platform.calibrate_mixers(alias=alias_drive_bus, cal_type=cal_type, channel_id=channel_id)

channel_id = 0
cal_type = "lo_and_sidebands"
alias_readout_bus = "readout_line_q1_bus"

platform.calibrate_mixers(alias=alias_readout_bus, cal_type=cal_type, channel_id=channel_id)
```

Warnings rise if a value that is not `off`, `lo` or `lo_and_sidebands` are used.
[#917](https://github.com/qilimanjaro-tech/qililab/pull/917)

- Implemented Crosstalk automatic implementation through the experiment class. The crosstalk can be added through the `Calibration` file or by creating a `CrosstalkMatrix`. The crosstalk implementation inside the `Experiment` class is:

```
experiment = ql.Experiment(label="liveplot_test")

flux_x = experiment.variable("flux_x", ql.Domain.Flux)
flux_z = experiment.variable("flux_z", ql.Domain.Flux)

experiment.set_crosstalk(crosstalk=crosstalk_matrix)  # to see the values to be applied on the sample
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

- Modified the `CrosstalkMatrix` and `FluxVector` classes to fit for the crosstalk matrix implementation inside `Experiment` and `Platform`. Now both classes update following the specifications and needs of experimentalists.
[#899](https://github.com/qilimanjaro-tech/qililab/pull/899)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
- Correction of bugs following the implementation of the qblox drawing class. The user can now play the same waveform twice in one play, and when gains are set as 0 in the qprogram they are no longer replaced by 1 but remain at 0. Some improvements added, the RF modules are now scaled properly instead of on 1, when plotting through qprogram the y axis now reads Amplitude [a.u.], and the subplots have been removed, all the lines plot in one plot.
[#918](https://github.com/qilimanjaro-tech/qililab/pull/918)