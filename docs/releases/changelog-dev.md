# Release dev (development release)

### New features since last release

- Implemented QDACII crosstalk compensation for `Qprogram`. The compiler automatically detects if there is a crosstalk matrix inside platform and implements the crosstalk for any bus inside the `Crosstalk` class. This function can be deactivated by setting the crosstalk variable as False inside `qp.play` and `qp.offset`.
The crosstalk modifies the structure of the `QProgram`, it changes any play or set offset into a set of plays and offsets of each bus of the crosstalk. It also takes into account different loops.
With crosstalk, this example qprogram:
```
r_wf = ql.Square(amplitude=1.0, duration=1000)
flux_wf = ql.Arbitrary(
    samples=np.array([0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3, 0.2, 0.1, 0])
)
qp_qdac = ql.QProgram()

freq = qp_qdac.variable(label="frequency", domain=ql.Domain.Frequency)

with qp_qdac.average(10):
    qp_qdac.set_offset(bus="qdac_flux2", offset_path0=0.3)
    with qp_qdac.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):

        # QDAC TRIGGER GENERATION
        qp_qdac.qdac.play(bus="qdac_flux1", waveform=flux_wf, dwell=2)
        qp_qdac.set_offset(bus="qdac_flux2", offset_path0=-0.2)
        qp_qdac.set_trigger(bus="qdac_flux1", duration=10e-6, outputs=1, position="start")

        # QBLOX WAIT TRIGGER
        qp_qdac.wait_trigger(bus="readout", duration=4)

        qp_qdac.set_frequency(bus="readout", frequency=freq)
        qp_qdac.sync()
        qp_qdac.measure(
            bus="readout",
            waveform=ql.IQPair(I=r_wf, Q=r_wf),
            weights=ql.IQPair(I=r_wf, Q=r_wf),
        )

        qp_qdac.wait(bus="readout", duration=100)
```
Turns internally into this (for a crosstalk matrix only including `qdac_flux1` and `qdac_flux2`):
```
...

with qp_qdac.average(10):
    qp_qdac.set_offset(bus="qdac_flux2", offset_path0=offset_2_compensated)
    qp_qdac.set_offset(bus="qdac_flux1", offset_path0=offset_1_compensated)
    with qp_qdac.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):

        # QDAC TRIGGER GENERATION
        qp_qdac.qdac.play(bus="qdac_flux2", waveform=flux_wf_crosstalk_compensated_2, dwell=2)
        qp_qdac.qdac.play(bus="qdac_flux1", waveform=flux_wf_crosstalk_compensated_1, dwell=2)
        qp_qdac.set_trigger(bus="qdac_flux1", duration=10e-6, outputs=1, position="start")

        # QBLOX WAIT TRIGGER
        qp_qdac.wait_trigger(bus="readout", duration=4)

        qp_qdac.set_frequency(bus="readout", frequency=freq)
        qp_qdac.sync()
        qp_qdac.measure(
            bus="readout",
            waveform=ql.IQPair(I=r_wf, Q=r_wf),
            weights=ql.IQPair(I=r_wf, Q=r_wf),
        )

        qp_qdac.wait(bus="readout", duration=100)
```
  [#1030](https://github.com/qilimanjaro-tech/qililab/pull/1030)

### Improvements

- For Autocalibration database, moved `sample_name` and `cooldown` from `AutocalMeasurement` (independent experiment) to `CalibrationRun` (full calibration tree). This way the database does not include redundant information, as these variables do not change from one measurement to another, only in different calibration runs.
[#1053](https://github.com/qilimanjaro-tech/qililab/pull/1053)

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