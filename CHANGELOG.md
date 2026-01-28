# CHANGELOG

## BSC-15

### Improvements

- For Autocalibration database, moved `sample_name` and `cooldown` from `AutocalMeasurement` (independent experiment) to `CalibrationRun` (full calibration tree). This way the database does not include redundant information, as these variables do not change from one measurement to another, only in different calibration runs.
[#1053](https://github.com/qilimanjaro-tech/qililab/pull/1053)

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

## BSC-14

### New features since last release

- Hardware Loop over the time domain has been implemented for Qblox backend in `QProgram`.
  This allows sweeping wait times entirely in hardware, eliminating the need of software loops (which require uploading multiple Q1ASM).
  The implementation leverages the different Q1ASM jump instructions to ensure correct execution of the `QProgram` sync operation.

- Variable expressions for time domain
  Variable expressions are now supported in `QProgram` for the time domain.
  The supported formats are given in ns:

  - `constant + time variable`
  - `time variable + constant`
  - `constant - time variable`
  - `time variable - constant`

Code example:

```
qp = QProgram()
duration = qp.variable(label="time", domain=Domain.Time)
with qp.for_loop(variable=duration, start=100, stop=200, step=10):
  qp.wait(bus="drive", duration)
  qp.sync()
  qp.wait(bus="drive", duration - 50)
```

[#950](https://github.com/qilimanjaro-tech/qililab/pull/950)

- QbloxDraw: Replaced the fixed qualitative palette (10 colors) with the continuous "Turbo" colorscale. Previously, plotting more than 10 buses caused an index error due to the palette’s limited size. The new implementation samples the continuous colorscale at evenly spaced positions based on the number of buses.
  [#1039](https://github.com/qilimanjaro-tech/qililab/pull/1039)

- **Active reset for transmon qubits in QBlox**

  Implemented a feedback-based reset for QBlox: measure the qubit, and if it is in the `|1⟩` state apply a corrective DRAG pulse; if it is already in `|0⟩` (ground state), do nothing. This replaces the relaxation time at the end of each experiment with a much faster, conditional reset.
  This has been implemented as: **`qprogram.qblox.measure_reset(bus: str, waveform: IQPair, weights: IQPair, control_bus: str, reset_pulse: IQPair, trigger_address: int = 1, save_adc: bool = False)`**

  It is compiled by the QBlox compiler as:

  1. `latch_rst 4` on the control_bus
  1. play readout pulse
  1. acquire
  1. sync the readout and control buses
  1. wait 400 ns on the control bus (trigger-network propagation)
  1. `set_conditional(1, mask, 0, duration of the reset pulse)` → enable the conditional
  1. Play the reset pulse on the control bus
  1. `set_conditional(0, 0, 0, 4)` → disable the conditional\
     For the control bus, `latch_en 4` is added to the top of the Q1ASM to enable trigger latching.

  `MeasureResetCalibrated` has been implemented to enable the use of active reset with a calibration file.
  After retrieving the waveforms and weights from the calibration file, the measure reset can be called with: **`qprogram.qblox.measure_reset(bus='readout_bus', waveform='Measure', weights='Weights', control_bus='drive_bus', reset_pulse='Drag')`**. Unlike other methods, this one does not allow a mix of calibrated and non-calibrated parameters is not allowed. This method requires the calibration file to be used consistently across `waveform`, `weight`, and `reset_pulse`; either for all three or for none. An error is raised if this condition is not met.
  **Notes**

  - The 400 ns wait inside `measure_reset` is the propagation delay of the Qblox trigger network. This figure is conservative as the official guideline is 388ns.
  - Users may supply any IQPair for the reset_pulse, though DRAG pulses are recommended to minimize leakage.
  - After `measure_reset`, users should insert a further wait as needed to allow the readout resonator to ring down before subsequent operations.
  - On compilation, `cluster.reset_trigger_monitor_count(address)` is applied to zero the module’s trigger counter. And the qcodes parameters required to set up the trigger network are implemented by the QbloxQRM class.
  - The Qblox Draw class has been modified so that `latch_rst` instructions are interpreted as a `wait`, and all `set_conditional` commands are ignored.
    [#955](https://github.com/qilimanjaro-tech/qililab/pull/955)
    [#1042](https://github.com/qilimanjaro-tech/qililab/pull/1042)

- Introduced `electrical_delay` as a new setting for the E5080b VNA driver. It is a pure software setting to be used in autoplotting and not a physical parameter of the device.
  [#1037](https://github.com/qilimanjaro-tech/qililab/pull/1037)

- Introduced a Pydantic-powered `QililabSettings` that centralizes runtime configuration, with the singleton `get_settings()` pulling values from multiple sources so teams can pick what fits their workflow. Settings still default to sensible values, but can be overridden directly in code by editing the fields (handy for tests or ad-hoc scripts), by exporting environment variables (for example `QILILAB_EXPERIMENT_RESULTS_BASE_PATH=/data/qililab`), or by dropping the same keys into a project-level `.env` file that is auto-discovered and parsed.
  [#1025](https://github.com/qilimanjaro-tech/qililab/pull/1025)

### Improvements

- Upgraded requirement: `qpysequence>=0.10.8`
  [#1044](https://github.com/qilimanjaro-tech/qililab/pull/1044)

- Improved acquisition result handling in the QBlox Compiler.

  Previously, each acquisition was assigned a unique acquisition index, which meant that a single qprogram could only contain up to 32 acquisitions per bus (due to QBlox’s limit of 32 indices).
  Now, acquisitions at the same nested level reuse the same acquisition index while incrementing the bin index. This removes the 32-acquisition limit in most cases. A `ValueError` is raised only if more than 32 acquisitions occur at different nested levels.
  Since the results retrieved from QBlox are now intertwined, a new function `_unintertwined_qblox_results` has been introduced in `platform`. This function called by `_execute_qblox_compilation_output method` and `execute_compilation_outputs_parallel` separates each acquisition into its own QbloxMeasurementResult object.
  [#998](https://github.com/qilimanjaro-tech/qililab/pull/998)

- Added support for real-time predistortion on Qblox hardware.

  - The outputs of a QCM can now set an FIR filter and up to four exponential filters (provided as a list). These parameters can be configured via the runcard (example below) and via platform.set_parameter/get_parameter.

  - The runcard has a new section under each QCM module: `filters: [...]` configured by output. The section is optional.

  - The states of a QCM filter are "enabled", "bypassed" and "delay_comp". Users can provide a boolean where True is mapped to "enabled" and False is mapped to "bypassed". When enabling a filter that could cause delay with other module outputs Qililab coerces the state to "delay_comp". This state ensures pulse timing remains consistent with filtered paths, keeping all outputs synchronized.

  - Parameters:

    - Exponential Filters (given by exponential index)
      - EXPONENTIAL_AMPLITUDE_0 ... EXPONENTIAL_AMPLITUDE_3
      - EXPONENTIAL_TIME_CONSTANT_0 ... EXPONENTIAL_TIME_CONSTANT_3
      - EXPONENTIAL_STATE_0 ... EXPONENTIAL_STATE_3
    - FIR Filters:
      - FIR_COEFF
      - FIR_STATE

  - Note: fir_coeff/FIR_COEFF must contain exactly 32 coefficients.

  - Below is an example of the filter part of the runcard:

    ```
      filters:
      - output_id: 0
        exponential_amplitude: [0.8, -1]
        exponential_time_constant: [6, 8]
        exponential_state: [True, True, False]
        fir_coeff: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
        fir_state: True
      - output_id: 1
        exponential_amplitude: 0.31
        exponential_time_constant: 9
        exponential_state: False
        fir_coeff: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
        fir_state: False
    ```

    Below is an example of set/get_parameter, the output_id must be provided:

    ```
    platform.set_parameter(alias=bus_alias, parameter=Parameter.EXPONENTIAL_TIME_CONSTANT_0, value=300, output_id=0)
    platform.get_parameter(alias=bus_alias, parameter=Parameter.FIR_STATE, output_id=2)
    ```

  - When setting/getting any parameter from the platform and giving the bus_alias, if an output_id or channel_id not associated with the bus is given, an exception is raised; and if an output_id instead of a channel_id (and vice versa) has been given an Exception is raised.
    [#981](https://github.com/qilimanjaro-tech/qililab/pull/981)

- This update introduces a new mechanism that allows the library to optionally import either full concrete implementations or lightweight stubs, depending on the user’s environment and installed dependencies. As part of this improvement, all Quantum Machines–related components have been reorganized under the `extra/quantum-machines` module hierarchy for better modularity and maintainability. Additionally, the Quantum Machines integration has been moved to the `[project.optional-dependencies]` section of the configuration, enabling users to install it only when needed.

  For example, to install the base library without any optional dependencies, run:

  ```bash
  pip install qililab
  ```

  or

  ```bash
  uv sync
  ```

  If you plan to use the Quantum Machines integration, you can include it during installation using the optional dependency group:

  ```bash
  pip install qililab[quantum-machines]
  ```

  or

  ```bash
  uv sync --extra quantum-machines
  ```

  [#995](https://github.com/qilimanjaro-tech/qililab/pull/995)

- Update qblox-instruments to 0.16.0 and qblox firmware to 0.11
  [#1015](https://github.com/qilimanjaro-tech/qililab/pull/1015)

- This PR is the beginning of a series that will aim to reduce the length of the Q1ASM, which can be limiting for some experiments. This PR has two distinct improvements:

  1. When possible, waits will be combined together. For example, before this PR the following Q1ASM could be generated:

     ```
     wait 10
     wait 40
     ```

     ```
     wait 10
     wait 40
     ```

     It will now be generated as:

     ```
     wait 50
     ```

     It will now be generated as:

     ```
     wait 50
     ```

  1. When instructing an `acquire_weighed` in Q1ASM, the creation of registers has been optimised. New registers for the weights would be created each time, a dictionary `weight_index_to_register` has been introduced in the QBlox Compiler to track previously used values of weight and reuse the register if possible.
     For example, two `acquire_weighted` with the same weight would use 4 registers for the weights (R0, R1, R3, R4):

     ```
     setup:
                   wait_sync        4              
                   set_mrk          0              
                   upd_param        4              

     main:
                     move             0, R0          
                     move             0, R1          
                     move             0, R2          
                     move             0, R3          
                     move             0, R4          
                     move             0, R5          
                     move             101, R6        
                     move             0, R7          
     loop_0:
                     play             0, 0, 4        
                     acquire_weighed  0, R5, R4, R3, 100
                     add              R5, 1, R5      
                     play             0, 0, 4        
                     acquire_weighed  1, R2, R1, R0, 100
                     add              R2, 1, R2      
                     add              R7, 1, R7      
                     loop             R6, @loop_0    
                     set_mrk          0              
                     upd_param        4              
                     stop
     ```

     But they will now only use 1 register (R1):

     ```
     setup:
                   wait_sync        4
                   set_mrk          0
                   upd_param        4

      main:
                      move             0, R0          
                      move             0, R1          
                      move             0, R2          
                      move             101, R3        
                      move             0, R4          
      loop_0:
                      play             0, 0, 4        
                      acquire_weighed  0, R2, R1, R1, 100
                      add              R2, 1, R2      
                      play             0, 0, 4        
                      acquire_weighed  1, R0, R1, R1, 100
                      add              R0, 1, R0      
                      add              R4, 1, R4      
                      loop             R3, @loop_0    
                      set_mrk          0              
                      upd_param        4              
                      stop
     ```

  [#1009](https://github.com/qilimanjaro-tech/qililab/pull/1009)

- Added `parameters` dictionary to the `Calibration` class, and removed legacy code.
  [#1005](https://github.com/qilimanjaro-tech/qililab/pull/1005)

- `platform.execute_qprograms_parallel()` now takes a list of bus mappings to allow one bus mapping per qprogram.
  Parameters for the function have now the same syntax and behaviour:
  bus_mapping (ist\[dict[str, str] | None\] | dict[str, str], optional). It can be one of the following:
  A list of dictionaries mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values). In this case, each bus mapping gets assigned to the :class:`.QProgram` in the same index of the list of qprograms passed as first parameter.
  A single dictionary mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values). In this case the same bus mapping is used for each one of the qprograms.
  None, in this case there is not a bus mapping between :class:`.QProgram` (keys )to the buses in the platform (values) and the buses are as defined in each qprogram.
  It is useful for mapping a generic :class:`.QProgram` to a specific experiment.
  Defaults to None.
  calibrations (list[Calibration], Calibration, optional). Contains information of previously calibrated values, like waveforms, weights and crosstalk matrix. It can be one of the following:
  A list of :class:`.Calibration` instances, one per :class:`.QProgram` instance in the qprograms parameter.
  A single instance of :class:`.Calibration`, in this case the same `.Calibration` instance gets associated to all qprograms.
  None. In this case no `.Calibration` instance is used.
  Defaults to None.
  [#996](https://github.com/qilimanjaro-tech/qililab/pull/996)

- `%% submit_job`: Added support for `sbatch --chdir` via a new `-c/--chdir` option that is propagated through `slurm_additional_parameters` and also enforced inside the job (`os.chdir(...)`) so it works with `-e local`. Made `--output` mandatory and hardened the output‑assignment check to recognize `Assign`, `AugAssign`, `AnnAssign`, walrus (`NamedExpr`), and tuple targets. Shipment of the notebook namespace is now safer: only picklable values (via `cloudpickle`) are sent, with common pitfalls (modules, loggers, private `_` names, IPython internals) excluded. `--low-priority` is a boolean flag mapping to a sane Slurm `nice=10000`. Paths are handled with `pathlib` plus `expanduser/expandvars`, the logs directory is created if missing, and imports are harvested conservatively from history (one‑line `import`/`from`, excluding `from __future__`). Parameter assembly only includes Slurm extras when provided, and the submitted function compiles the code string internally while accepting the output name and optional workdir. The job object is written to both `local_ns` and the global `user_ns` for IPython robustness. Log cleanup was rewritten to be cross‑platform and resilient: artifacts are grouped by numeric job‑ID prefix, non‑conforming entries are removed, and only the newest `num_files_to_keep` job groups are retained.
  [#994](https://github.com/qilimanjaro-tech/qililab/pull/994)

- QbloxDraw now supports passing a calibration file as an argument when plotting from both the platform and qprogram.
  [#977](https://github.com/qilimanjaro-tech/qililab/pull/977)

- Previously, `platform.draw(qprogram)` and `qprogram.draw()` returned the plotly object and the raw data being plotted. Now they return only the plotly object. This change ensures:

  - When calling `qprogram.draw()` or `platform.draw(qprogram)` directly, the figure is displayed.
  - When assigning it to a variable (e.g., `plotly_figure = qprogram.draw()` or `plotly_figure = platform.draw(qprogram)`), the figure is stored but not automatically shown (since `figure.show()` has been removed from QbloxDraw).

  If the user needs access to the underlying data, it can be retrieved as follows:

  ```
  plotly_figure = qprogram.draw()
  plotly_figure.data
  ```

Note: QbloxDraw class continues to return both, the plotly object and the dictionary of raw data.
[#963](https://github.com/qilimanjaro-tech/qililab/pull/963)

- Previously, QbloxDraw returned only the raw data being plotted. Now, the class returns both the Plotly Figure object and the raw data. This has been extended to qprogram and platform:

```
plotly_figure, data_draw = qprogram.draw()
plotly_figure, data_draw = platform.draw(qprogram)
```

[#960](https://github.com/qilimanjaro-tech/qililab/pull/960)

- The R&S SGS100a driver has now the capability to change the operation mode between normal mode and bypass mode. The default mode is the normal mode. The allowed strings for each mode
  in the settings are `normal` and `bypass`. If the instrument is reset the native instrument configuration defaults to normal.
  [#957](https://github.com/qilimanjaro-tech/qililab/pull/957)

- Implementation of the Sudden Net Zero (SNZ) waveform to be able to realise better fidelity two qubit gates.
  [#952](https://github.com/qilimanjaro-tech/qililab/pull/952)

- The driver of the VNA has been simplified: all files related to Agilent E5071B have been removed, only Keysight E5080B remains. The file structure has been refactored to align with the architecture used by other instruments in Qililab. The file 'driver_keysight_e5080b' is meant to be submitted to the public repo QCoDeS contrib drivers, conditional on their approval. The testing file for the driver 'test_driver_e50808b.py', alongside the file used to simulate the instrument 'Keysight_E5080B.yaml' will also be submitted. The data acquisition process now follows a status-check-based polling loop. The instrument is queried repeatedly using the command "STAT:OPER:COND?". Before each retrieval, a delay of 0.5 seconds is introduced to prevent overloading the instrument. The command returns an integer representing a bitmask indicating the status of the VNA's operation. A bitwise operation is performed to determine the readiness for data retrieval, this is done differently depending on whether the number of averages is 1 or greater:

  - For averages greater than 1: the data can be acquired when bit 8 is set (typically, bit 10 gets enabled after the first average, hence the command usually returns 1280 in decimal or 10100000000 in binary)
  - For averages equal to 1: the data can be acquired when bit 10 is set (bit 8 does not get set in this case, the expected response is 1024 in decimal or 10000000000 in binary)

- For the plots outputted by Qblox Draw, the name legend will now be a concatenation of the bus name and "Flux", similar to I and Q when hardware modulation is enabled.

- An additional argument has been added, to Qblox Draw, time_window. It allows the user to stop the plotting after the specified number of ns have been plotted. The plotting might not be the exact number of ns inputted. For example, if the time_window is 100 ns but there is a play operation of 150 ns, the plots will display the data until 150 ns.
  [#933](https://github.com/qilimanjaro-tech/qililab/pull/933)

- Added measurements databases into the results saving structure all the architecture for them is located inside `results/database.py`. Added functionality for stream array using databases through `platform.database_saving` and through the class `StreamArray`, legacy `stream_array()` function still works as usual for retrocompatibility.
  [#928](https://github.com/qilimanjaro-tech/qililab/pull/928)
  [#1014](https://github.com/qilimanjaro-tech/qililab/pull/1014)

- Added SQLAlchemy and xarray (usefull tool for measurements) to the dependencies as they are required for databases.
  [#928](https://github.com/qilimanjaro-tech/qililab/pull/928)

- Relocated save_results and load_results from data_management to result/result_management.py for structure consistency. The load_results functions has been slightly changed to take into account different structures of data.
  [#928](https://github.com/qilimanjaro-tech/qililab/pull/928)

- Add base_path as an input for stream_array and an optional parameter for the experiment class, qililab cannot have the data path hardcoded.
  [#936](https://github.com/qilimanjaro-tech/qililab/pull/936)

- In the VNA Driver for Keysight E5080B, an update_settings function has been implemented, it allows to efresh all settings inside qililab by querying the VNA.

- The sweep time and sweep time auto parameters have been added in the qcodes like driver and also in the wrapper.

- The sims file used to test the qcode like driver file has been moved to a similar location as qcodes (\\qililab\\src\\qililab\\instruments\\sims).
  [#943](https://github.com/qilimanjaro-tech/qililab/pull/943)

- Modified Streamarray to allow for np.complexfloat values following VNA results. This process has been automatized and requires no input from the user.
  [#941](https://github.com/qilimanjaro-tech/qililab/pull/941)

- VNA Driver Keysight E5080B:

  - Added triggerring related parameters. The parameters included are: sweep_group_count, trigger_source, trigger_type, trigger_slope, accept_before_armed. The first four have been included in the qcode type driver and the qililab wrapper; the last has only been added to the qcodes type driver to avoid cluttering the qililab code with parameters not required.
  - The expected data type has been added to all set_parameters
  - In the initial_setup, all parameters are now set, the conditionals have been removed. Now the VNA itself will show an error if two uncompatible parameters are being set.
    [#944](https://github.com/qilimanjaro-tech/qililab/pull/944)

- QbloxDraw:

  - The code is now tracking real time/classical time. The implications are the following:
    - A play can interrupt a preceeding play - this replicates the hardware behaviour.
    - Acquisitions are now plotted, when hovering the mouse on the plot, the user can see the index of the acquisition (they are plotted by default but this can be set to False if desired with the argument 'acquisition_showing').
    - Acquire and Play can overlap each other as they are real time commands - this replicates the hardware behaviour.
      The integration length of the acquire is retrieved from the platform if given. If plotting directly from qprogram, the integration length is set as the duration of the acquire.
  - The sub and not commands have been implemented.
  - If QbloxDraw is given a Q1ASM command it is not programmed for, it will raise a NotImplementedError.
  - The \_handle_play() used to loop through all the waveform indices, now it exits in the loop as soon as I and Q have been found, this is more efficient.
  - When running the code from the platform, the bus_mapping can be provided.
  - The overall plotting design has been improved. A plotly colour plaette is used. The I and Q are the same color but in a different shade.

[#945](https://github.com/qilimanjaro-tech/qililab/pull/945)

- Added the database implementation inside `Experiment`. `load_db_manager` function added to platform to add the db_manager. For `Experiment` class, added an input variable (`platform.save_experiment_results_in_database`) to define if working with databases or not (default set as True), if True, the database is automatically generated using the `Experiment` variables as information.

Code example:

```
...
platform.load_db_manager(db_ini_path = "path")  # To load the database manager. Optional path.
platform.save_experiment_results_in_database = True  # Default is True.
experiment = Experiment(label="Experiment_name", description = "optional description")
platform.execute_experiment(experiment)
...
```

[#938](https://github.com/qilimanjaro-tech/qililab/pull/938)
[#997](https://github.com/qilimanjaro-tech/qililab/pull/997)

- Minor modification at database `DatabaseManager`, as it now requires the config file to contain a `base_path_local`, `base_path_shared` and `data_write_folder`. following the structure:

```
[postgresql]
user =
passwd =
host = haldir.localdomain
port = 9999
database = postgres
base_path_local = "/mnt/home.local/"
base_path_shared = "/home/"
data_write_folder = "shared_measurement_haldir"
```

The data automatically selects between the local or shared domains depending on availability, always prioritizing local domains but if not available choosing the shared domain.

[#951](https://github.com/qilimanjaro-tech/qililab/pull/951)

- Modified `StreamArray` to work with live plot. Now the H5 file has the `swmr_mode` set as true allowing for live reading and `StreamArray`'s `__enter__` and `__setitem__` have `file.flush()` to update the H5 live. Moved `create_dataset` to `__enter__` instead of `__setitem__` to allow for live plot while acounting for VNA results with different data structure. Modified the `experiment_completed` to set as `True` after the execution, now in case of a crash the experiment will not be set as Completed.
  [#966](https://github.com/qilimanjaro-tech/qililab/pull/966)
  [#976](https://github.com/qilimanjaro-tech/qililab/pull/976)

- Implemented a QDACII compiler for triggered voltage lists together with QDACII - QBlox pulse synchronization.
  Inside the QDACII drivers the functions to create voltage lists, triggered pulses and play those pulse have been created, to simplify the user interaction with the QDACII a `QdacCompiler` has been created using `Qprogram`.

The structure of a qprogram combining QDACII and Qblox is exemplified as:

```
qp = Qprogram()

qp.qdac.play(bus="flux_1", waveform=qdac_volt_list, dwell=dwell, repetitions=repetitions)
qp.set_offset(bus="flux_2", offset=value)
qp.set_trigger(bus="flux_1", duration=duration, outputs=out_trigger, position="start")

# QBLOX WAIT TRIGGER
qp.wait_trigger(bus="readout", duration=4)

# QBLOX PULSE
qp.play(bus="drive", waveform=d_wf)

# READOUT PULSE
qp_rabi.measure(bus="readout", waveform=IQPair(I=r_wf_I, Q=r_wf_Q), weights=IQPair(I=weights_shape, Q=weights_shape))
```

In this example a pulse is played through QDACII flux line 1 and an offset is played through flux line 2. In the meantime Qblox is waiting for each QDACII pulse repetition.
[#968](https://github.com/qilimanjaro-tech/qililab/pull/968)

- Modified smoothed square waveform class `FlatTop(amplitude, duration, smooth_duration, buffer = 0)` which works similar to the `Square` waveform with an additional smoothing on the edges. The only additional parameters are the smoothing duration and the buffer time. In `QbloxCompiler` if the duration exceeds a threshold of 100 ns the pulses are divide into two arbitrary pulses at the beginning and the end for the smooth parts and a loop of square pulses in the middle, with the exact same behavior as `Square` pulses.
  [#969](https://github.com/qilimanjaro-tech/qililab/pull/969)

- Modified the `experiment_completed` to set as `True` after the execution, now in case of a crash the experiment will not be set as Completed.
  [#972](https://github.com/qilimanjaro-tech/qililab/pull/972)

- Added new functions to DatabaseManager to support more efficient loading of data for live-plotting application. Such as get_platform and get_qprogram.
  [#979](https://github.com/qilimanjaro-tech/qililab/pull/979)

- Added `ql.load_by_id(id)` in qililab, This function allows to retrieve the data path of a measurement with the given id without creating a `DatabaseManager` instance. This function is intended to be used inside notebooks using slurm as `DatabaseManager` cannot be submitted.
  [#986](https://github.com/qilimanjaro-tech/qililab/pull/986)

- Added Database manager for autocalibration and QiliSDK-Speqtrum. Added Database column structure and added new functions on `DatabaseManager` such as `add_calibration_run`, `add_autocal_measurement`, `add_experiment`, `load_calibration_by_id`, `load_experiment_by_id` to control such databases. Moved all functions related to databases inside `result/database/`. Modified `StreamArray` and `ExperimentResultsWriter` to accomodate for these databases.
  [#1019](https://github.com/qilimanjaro-tech/qililab/pull/1019)

### Breaking changes

- Modified file structure for functions `save_results` and `load_results`, previously located inside `qililab/src/qililab/data_management.py` and now located at `qililab/src/qililab/result/result_management.py`. This has been done to improve the logic behind our libraries. The init structure still works in the same way, `import qililab.save_results` and `import qililab.load_results` still works the same way.
  [#928](https://github.com/qilimanjaro-tech/qililab/pull/928)

- Set database saving and live plotting to `False` by default during experiment execution.
  [#999](https://github.com/qilimanjaro-tech/qililab/pull/999)

### Deprecations / Removals

### Documentation

- Added the return typings and missing docstring elements for the DatabaseManager class.
  [#1036](https://github.com/qilimanjaro-tech/qililab/pull/1036)

### Bug fixes

- Added `py.typed` file in the root dictionary to mark the library as typed and inform type checkers (mypy, pyright, etc.) that this package ships with usable type hints.
  [#1034](https://github.com/qilimanjaro-tech/qililab/pull/1034)

- Qblox Draw read the dac offsets of RF modules (parameters: `OUT0_OFFSET_PATH0`, `OUT0_OFFSET_PATH1`, `OUT1_OFFSET_PATH0` and `OUT1_OFFSET_PATH1`) in Volt, although they are specified in millivolts. This has been fixed by converting the value to Volts.
  [#1033](https://github.com/qilimanjaro-tech/qililab/pull/1033)

- Qblox Draw- When dealing with real time and classical time, the real duration was put instead of the wait duration. Note: do not include this comment in the next release changelog as the bug was not in the previous release.

- Fixed a bug in the QBlox Compiler handling of the wait, long waits that were a multiple of 65532 (the maximum wait) up to 65535 were giving out an error. This has been solved by checking if the remainder would be below 4. If the remainder is 0 it appends a wait of 65532 and if the remainder is between 1 and 3, the duration of the last wait is computed as : `(INST_MAX_WAIT + remainder) - INST_MIN_WAIT` (where `INST_MAX_WAIT` is 65532 and `INST_MIN_WAIT` is 4) and a wait of `INST_MIN_WAIT` is added.
  [#1006](https://github.com/qilimanjaro-tech/qililab/pull/1006)

- Exposed `Platform` in the global namespace.
  [#1002](https://github.com/qilimanjaro-tech/qililab/pull/1002)

- Fixed a bug in the reshaping of MeasurementResults within the ExperimentResults.
  [#999](https://github.com/qilimanjaro-tech/qililab/pull/999)

- Qblox Draw: Previously, when plotting from the platform, the integration length was incorrectly taken from the runcard parameter. However, since Qililab currently only implements acquire_weighted, the integration length should instead be determined by the duration of the weight.
  This has been corrected and now the behaviour of the acquire is the same when plotting from the platform or the qprogram.
  The integration length is defined as the duration of the acquire, not the weight, because Qililab ensures they are always equal. As a result, two acquires cannot overlap in Qililab. However, in QbloxDraw’s logic, interruptions remain possible, similar to Play.
  [#982](https://github.com/qilimanjaro-tech/qililab/pull/982)

- Removed the unsupported zorder kwarg from QbloxDraw plotting to prevent Plotly errors across environments.
  [#974](https://github.com/qilimanjaro-tech/qililab/pull/974)

- A bug on the tests of Qblox Draw has been fixed. Previously, the test compared `figure.data` using the position of items in the list. Since the order of items can change, this caused inconsistent results. The test now compares the data based on the bus name.
  [#965](https://github.com/qilimanjaro-tech/qililab/pull/965)

- For Qblox Draw, the move commands of the Q1ASM were being read correctly once but were not being updated after - this caused problem with loops.

- A 4ns has been added when an acquire_weighed command is added to account for the extra clock cycle
  [#933](https://github.com/qilimanjaro-tech/qililab/pull/933)

- Qblox Draw: Corrected bug with time window and nested loops- now after the code exits the recursive loop, the code checks the time window flag status and exits if needed.
  [#937](https://github.com/qilimanjaro-tech/qililab/pull/937)

- VNA Driver Keysight E5080B:

  - The user can now set through the platform the parameters of type Enums, the enums were not being capitalised. - The bounds in the frequency span of the qcodes type driver have been removed as they were wrong.
  - The bounds of the points in the qcodes type driver have been modified to range from 1 to 100003.
    [#943](https://github.com/qilimanjaro-tech/qililab/pull/943)

- QbloxDraw:

  - The sequencer offsets given from the runcard (offset_i and offset_q in the runcard) were being applied similarly to the DAC offsets, when they should have been treated like the Q1ASM offsets - this has been fixed and those sequencer offsets havee been renamed sequencer_runcard_offset_i and sequencer_runcard_offset_q instead of ac_offsets_i and ac_offsets_q for improved clarity.
  - get_value() in the QbloxDraw class now checks that the given string is a float, it used to check x.isdigit() which didn't work for negative values.
    [#945](https://github.com/qilimanjaro-tech/qililab/pull/945)

- Fixed a bug for `StreamArray` while using dictionary structures for the loops. Now the order is correct and the data is saved in the correct h5 file format.
  [#953](https://github.com/qilimanjaro-tech/qililab/pull/953)

- Quick fix for set_parameter of scope_store_enabled. Now it executes the correct Qblox functions to record the scope.
  [#956](https://github.com/qilimanjaro-tech/qililab/pull/956)
  [#959](https://github.com/qilimanjaro-tech/qililab/pull/959)

- Added an integer transformation for the play pulse duration at the `QbloxCompiler` `compile`. Before this fix, if a user introduced a pulse duration as a float and greater than 100 ns in `qp.play`, the program would crash with a weir and difficul to trace error report. Now this is fixed.
  [#969](https://github.com/qilimanjaro-tech/qililab/pull/969)

- Fixed an error inside set_parameter for OUT0_ATT and OUT1_ATT for the QRM-RF and QCM-RF. When the device was disconnected qililab tried to get the non existent device. not it executes as expected.
  [#973](https://github.com/qilimanjaro-tech/qililab/pull/973)

- Fixed `FluxVector.set_crosstalk_from_bias(...)` and `platform.set_bias_to_zero(...)` related to automatic crosstalk compensation. Now the bias is set to 0 correctly and the fluxes are set to the correct value based on the offset.
  [#983](https://github.com/qilimanjaro-tech/qililab/pull/983)

- Fixed documentation for results `counts`, now it warns the user that instead of `num_avg` they must use `num_bins`.
  [#989](https://github.com/qilimanjaro-tech/qililab/pull/989)

- Fixed an error impeding two instances of QDAC2 to be executed through platform.connect when the runcard included 2 different `qdevil_qdac2` controllers inside `instrument_controllers`.
  [#990](https://github.com/qilimanjaro-tech/qililab/pull/990)

- Qblox module `desynch_sequencers` now iterates over instrument_controllers in the Runcard, instead than the plain instruments, solving a bug, where a discrepancy in the runcard between both used to error, trying to desynch an instrument that wasn't connected (connect loops instrument_controllers, not instruments too).
  [#964](https://github.com/qilimanjaro-tech/qililab/pull/964)

- Fixed a bug where using stream array with `Calibration` raised an error. This was dues to the `StreamArray._get_debug()` function, trying to compile a qprogram with calibration waveforms or block without bus mapping. Improved `StreamArray` error traceability and added bus_mapping as a variable for proper compilation.
  [#1043](https://github.com/qilimanjaro-tech/qililab/pull/1043)

## 0.29.3 (2025-04-07)

### Improvements

- The tests for `QbloxDraw` have been modified such that the plots don't open on the user's browser when running pytests via VSCode.
  [#924](https://github.com/qilimanjaro-tech/qililab/pull/924)

- Github Actions now use `pytest-xdist` plugin to run tests in parallel. To run tests in parallel locally use `uv run pytest -n auto --dist loadfile`. The `--dist loadfile` flag is mandatory to avoid conflicts between tests that edit shared data, and should be planned for removal in the future.
  [#925](https://github.com/qilimanjaro-tech/qililab/pull/925)

### Bug fixes

- For the Rohde & Schwarz SGS100A, a missing line in the driver prevented the settings from updating when set. This issue has been fixed.
  [#927](https://github.com/qilimanjaro-tech/qililab/pull/927)

- Qblox-instruments version updated to the right one.
  [#929](https://github.com/qilimanjaro-tech/qililab/pull/929)

## 0.29.2 (2025-03-31)

### New features since last release

- This update marks a significant transition in our workflow by adopting Astral's uv for dependency management, building, and publishing. With this change, our project now centralizes dependency definitions within a dedicated configuration file `pyproject.toml`, ensuring consistent version locking and resolution across all environments. The legacy system for managing dependencies has been replaced with uv's streamlined approach, which simplifies the maintenance process and reduces potential inconsistencies.

In addition, the build process has been completely overhauled. The old build scripts have been retired in favor of uv's build command, which compiles the source code, bundles assets, and prepares production-ready artifacts. This change not only standardizes the build process but also introduces enhanced logging and error handling, making it easier to diagnose any issues that arise during the build.

Publishing has also been improved with the integration of uv. The new process automates packaging and deployment, ensuring that artifacts are published in sync with the version specified in the configuration file. This automation minimizes manual intervention and helps maintain consistency in the release process.

Developers should install Astral's uv globally (for example, running `curl -LsSf https://astral.sh/uv/install.sh | sh`). After installation, project management is handled through uv CLI. For additional details or troubleshooting, please refer to the official Astral's uv documentation at <https://docs.astral.sh/uv/concepts/projects/>.

[#923](https://github.com/qilimanjaro-tech/qililab/pull/923)

- Implemented automatic mixers calibration for Qblox RF modules. There are to ways to use it. The first one is by setting a parameter in the runcard, which indicates when and which type of calibration is ran.

For the QRM-RF module the parameter is `out0_in0_lo_freq_cal_type_default`, and the values it can take are `off`, `lo` and `lo_and_sidebands`. The first one is the default value, if set the instrument won't do any automatic mixers calibration on its own, to avoid unexpected behaviours by default. The second value will suppress the leakage in the LO, and the third one the LO plus the sidebands. The parameter that will trigger this autocalibration everytime is changed in the instrument is `out0_in0_lo_freq`.

For the QCM-RF module the parameters in the runcard are `out0_lo_freq_cal_type_default` and `out1_lo_freq_cal_type_default`, and the values are the same one that for the QRM-RF described above. The parameters that will trigger this autocalibration everytime is changed in the instrument are `out0_lo_freq` and `out1_lo_freq`.

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

### Bug fixes

- Correction of bugs following the implementation of the qblox drawing class. The user can now play the same waveform twice in one play, and when gains are set as 0 in the qprogram they are no longer replaced by 1 but remain at 0. Some improvements added, the RF modules are now scaled properly instead of on 1, when plotting through qprogram the y axis now reads Amplitude [a.u.], and the subplots have been removed, all the lines plot in one plot.
  [#918](https://github.com/qilimanjaro-tech/qililab/pull/918)

- Fixed an issue involving D5a initial setup where the channel id was not correctly set by id index.

  [#926](https://github.com/qilimanjaro-tech/qililab/pull/926)

## 0.29.1 (2025-03-27)

### New features since last release

- QBlox: An oscilloscope simulator has been implemented. It takes the sequencer as input, plots its waveforms and returns a dictionary (data_draw) containing all data points used for plotting.

  The user can access the Qblox drawing feature in two ways:

  1. Via platform (includes runcard knowledge)

     ```python
     with platform.session():
         platform.draw(qprogram=qprogram)
     ```

     Note that if it is used with a Quantum Machine runcard, a ValueError will be generated.

  1. Via QProgram (includes runcard knowledge)

     ```python
     qp = QProgram()
     qprogram.draw()
     ```

  Both methods compile the qprogram internally to generate the sequencer and call `QbloxDraw.draw(self, sequencer, runcard_data=None, averages_displayed=False) -> dict`. [#901](https://github.com/qilimanjaro-tech/qililab/pull/901)

### Improvements

- Now the Rohde & Schwarz will return an error after a limit of frequency or power is reached based on the machine's version.
  [#897](https://github.com/qilimanjaro-tech/qililab/pull/897)

- QBlox: Added support for executing multiple QProgram instances in parallel via the new method `platform.execute_qprograms_parallel(qprograms: list[QProgram])`. This method returns a list of `QProgramResults` corresponding to the input order of the provided qprograms. Note that an error will be raised if any submitted qprograms share a common bus.

  ```python
  with platform.session():
      results = platform.execute_qprograms_parallel([qprogram1, qprogram2, qprogram3])
  ```

  [#906](https://github.com/qilimanjaro-tech/qililab/pull/906)

### Deprecations / Removals

- Remove the check of forcing GRES in slurm.
  [#907](https://github.com/qilimanjaro-tech/qililab/pull/907)

### Bug fixes

- D5a instrument now does not raise error when the value of the dac is higher or equal than 4, now it raises an error when is higher or equal than 16 (the number of dacs).
  [#908](https://github.com/qilimanjaro-tech/qililab/pull/908)

## 0.29.0 (2025-03-17)

### New features since last release

- We have introduced an optimization in the QbloxCompiler that significantly reduces memory usage when compiling square waveforms. The compiler now uses a heuristic algorithm that segments long waveforms into smaller chunks and loops over them. This optimization follows a two-pass search:

  1. **First Pass**: The compiler tries to find a chunk duration that divides the total waveform length evenly (i.e., remainder = 0).
  1. **Second Pass**: If no exact divisor is found, it looks for a chunk duration that leaves a remainder of at least 4 ns. This leftover chunk is large enough to be stored or handled separately.

  Each chunk duration is restricted to the range ([100, 500]) ns, ensuring that chunks are neither too small (leading to excessive repetitions) nor too large (risking out-of-memory issues). If no duration within ([100, 500]) ns meets these remainder constraints, the compiler defaults to using the original waveform in its entirety.
  [#861](https://github.com/qilimanjaro-tech/qililab/pull/861)
  [#895](https://github.com/qilimanjaro-tech/qililab/pull/895)

- Raises an error when the inputed value for the QDAC is outside of the bounds provided by QM. Done in 3 ways, runcard, set_parameter RAMPING_ENABLED and set_parameter RAMPING_RATE.
  [#865](https://github.com/qilimanjaro-tech/qililab/pull/865)

- Enable square waveforms optimization for Qblox.
  [#874](https://github.com/qilimanjaro-tech/qililab/pull/874)

- Implemented ALC, IQ wideband and a function to see the RS models inside the drivers for SGS100a.
  [#894](https://github.com/qilimanjaro-tech/qililab/pull/894)

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

### Breaking changes

### Deprecations / Removals

- Removed weighted acquisitions for circuits.
  [#904](https://github.com/qilimanjaro-tech/qililab/pull/904)

- Removed quick fix for the timeout error while running with QM as it has been fixed.
  [#854](https://github.com/qilimanjaro-tech/qililab/pull/854)

### Documentation

### Bug fixes

- Addressed a known bug in the qblox where the first frequency and gain settings in a hardware loop are incorrect. The code now includes a workaround to set these parameters a second time to ensure proper functionality. This is a temporary fix awaiting for QBlox to resolve it.
  [#903](https://github.com/qilimanjaro-tech/qililab/pull/898)

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

## 0.28.0 (2024-12-09)

### New features since last release

- Incorporated new check for maximum allowed attenuation in RF modules.

[#843](https://github.com/qilimanjaro-tech/qililab/pull/843)

- Updated to latest qblox-instruments version. Changed some deprecated code from the new version and the QcmQrm into the more generic Module class.

[#836](https://github.com/qilimanjaro-tech/qililab/pull/836)

- Added empty handlers for Blocks in QProgram compilers

[#839](https://github.com/qilimanjaro-tech/qililab/pull/839)

- Support GRES in %%submit_job magic method

[#828](https://github.com/qilimanjaro-tech/qililab/pull/828)

- Added intermediate frequency to single input lines on qm. The default is 0 (this prevents some bugs from qua-qm). Now it is possible to use the set_parameter IF and qm.set_frequency for buses with single_input.

[#807](https://github.com/qilimanjaro-tech/qililab/pull/807)

- A new `GetParameter` operation has been added to the Experiment class, accessible via the `.get_parameter()` method. This allows users to dynamically retrieve parameters during experiment execution, which is particularly useful when some variables do not have a value at the time of experiment definition but are provided later through external operations. The operation returns a `Variable` that can be used seamlessly within `SetParameter` and `ExecuteQProgram`.

  Example:

  ```
  experiment = Experiment()

  # Get a parameter's value
  amplitude = experiment.get_parameter(bus="drive_q0", parameter=Parameter.AMPLITUDE)

  # The returned value is of type `Variable`. It's value will be resolved during execution.
  # It can be used as usual in operations.

  # Use the variable in a SetOperation.
  experiment.set_parameter(bus="drive_q1", parameter=Parameter.AMPLITUDE, value=amplitude)

  # Use the variable in an ExecuteQProgram with the lambda syntax.
  def get_qprogram(amplitude: float, duration: int):
    square_wf = Square(amplitude=amplitude, duration=duration)

    qp = QProgram()
    qp.play(bus="readout", waveform=square_wf)
    return qp

  experiment.execute_qprogram(lambda: amplitude=amplitude: get_qprogram(amplitude, 2000))
  ```

  [#814](https://github.com/qilimanjaro-tech/qililab/pull/814)

- Added offset set and get for quantum machines (both OPX+ and OPX1000). For hardware loops there is `qp.set_offset(bus: str, offset_path0: float, offset_path1: float | None)` where `offset_path0` is a mandatory field (for flux, drive and readout lines) and `offset_path1` is only used when changing the offset of buses that have to IQ lines (drive and readout). For software loops there is `platform.set_parameter(alias=bus_name, parameter=ql.Parameter.OFFSET_PARAMETER, value=offset_value)`. The possible arguments for `ql.Parameter` are: `DC_OFFSET` (flux lines), `OFFSET_I` (I lines for IQ buses), `OFFSET_Q` (Q lines for IQ buses), `OFFSET_OUT1` (output 1 lines for readout lines), `OFFSET_OUT2` (output 2 lines for readout lines).
  [#791](https://github.com/qilimanjaro-tech/qililab/pull/791)

- Added the `Ramp` class, which represents a waveform that linearly ramps between two amplitudes over a specified duration.

  ```python
  from qililab import Ramp

  # Create a ramp waveform from amplitude 0.0 to 1.0 over a duration of 100 units
  ramp_wf = Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100)
  ```

  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- Added the `Chained` class, which represents a waveform composed of multiple waveforms chained together in time.

  ```python
  from qililab import Ramp, Square, Chained

  # Create a chained waveform consisting of a ramp up, a square wave, and a ramp down
  chained_wf = Chained(
      waveforms=[
          Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100),
          Square(amplitude=1.0, duration=200),
          Ramp(from_amplitude=1.0, to_amplitude=0.0, duration=100),
      ]
  )
  ```

  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- Added `add_block()` and `get_block()` methods to the `Calibration` class. These methods allow users to store a block of operations in a calibration file and later retrieve it. The block can be inserted into a `QProgram` or `Experiment` by calling `insert_block()`.

  ```python
  from qililab import QProgram, Calibration

  # Create a QProgram and add operations
  qp = QProgram()
  # Add operations to qp...

  # Store the QProgram's body as a block in the calibration file
  calibration = Calibration()
  calibration.add_block(name="qp_as_block", block=qp.body)

  # Retrieve the block by its name
  calibrated_block = calibration.get_block(name="qp_as_block")

  # Insert the retrieved block into another QProgram
  another_qp = QProgram()
  another_qp.insert_block(block=calibrated_block)
  ```

  [#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- Added routing algorithms to `qililab` in function of the platform connectivity. This is done passing `Qibo` own `Routers` and `Placers` classes,
  and can be called from different points of the stack.

  The most common way to route, will be automatically through `qililab.execute_circuit.execute()`, or also from `qililab.platform.execute/compile()`. Another way, would be doing the transpilation/routing directly from an instance of the Transpiler, with: `qililab.digital.CircuitTranspiler.transpile/route_circuit()` (with this last one, you can route with a different topology from the platform one, if desired, defaults to platform)

  Example

  ```python
  from qibo import gates
  from qibo.models import Circuit
  from qibo.transpiler.placer import ReverseTraversal, Random
  from qibo.transpiler.router import Sabre
  from qililab import build_platform
  from qililab.digital import CircuitTranspiler

  # Create circuit:
  c = Circuit(5)
  c.add(gates.CNOT(1, 0))

  ### From execute_circuit:
  # With defaults (ReverseTraversal placer and Sabre routing):
  probabilities = ql.execute(c, runcard="./runcards/galadriel.yml", placer= Random, router = Sabre, routing_iterations: int = 10,)
  # Changing the placer to Random, and changing the number of iterations:
  probabilities = ql.execute(c, runcard="./runcards/galadriel.yml",

  ### From the platform:
  # Create platform:
  platform = build_platform(runcard="<path_to_runcard>")
  # With defaults (ReverseTraversal placer, Sabre routing)
  probabilities = platform.execute(c, num_avg: 1000, repetition_duration: 1000)
  # With non-defaults, and specifying the router with kwargs:
  probabilities = platform.execute(c, num_avg: 1000, repetition_duration: 1000,  placer= Random, router = (Sabre, {"lookahead": 2}), routing_iterations: int = 20))
  # With a router instance:
  router = Sabre(connectivity=None, lookahead=1) # No connectivity needed, since it will be overwritten by the platform's one
  probabilities = platform.execute(c, num_avg: 1000, repetition_duration: 1000, placer=Random, router=router)

  ### Using the transpiler directly:
  ### (If using the routing from this points of the stack, you can route with a different topology from the platform one)
  # Create transpiler:
  transpiler = CircuitTranspiler(platform.digital_compilation_settings)
  # Default Transpilation (ReverseTraversal, Sabre and Platform connectivity):
  routed_circ, qubits, final_layouts = transpiler.route_circuit(c)
  # With Non-Default Random placer, specifying the kwargs, for the router, and different coupling_map:
  routed_circ, qubits, final_layouts = transpiler.route_circuit(c, placer=Random, router=(Sabre, {"lookahead": 2}, coupling_map=<some_different_topology>))
  # Or finally, Routing with a concrete Routing instance:
  router = Sabre(connectivity=None, lookahead=1) # No connectivity needed, since it will be overwritten by the specified in the Transpiler:
  routed_circ, qubits, final_layouts = transpiler.route_circuit(c, placer=Random, router=router, coupling_map=<connectivity_to_use>)
  ```

[#821](https://github.com/qilimanjaro-tech/qililab/pull/821)

- Added a timeout inside quantum machines to control the `wait_for_all_values` function. The timeout is controlled through the runcard as shown in the example:

  ```yaml
  instruments:
    - name: quantum_machines_cluster
      alias: QMM
      ...
      timeout: 10000 # optional timeout in seconds
      octaves:
      ...
  ```

  [#826](https://github.com/qilimanjaro-tech/qililab/pull/826)

- Added `shareable` trigger inside runcard for quantum machines controller. The controller is defined in the runcard following this example:

  ```
  instruments:
    - name: con1
        analog_outputs:
        - port: 1
          offset: 0.0
          shareable: True
  ```

[#844](https://github.com/qilimanjaro-tech/qililab/pull/844)

### Improvements

- Legacy linting and formatting tools such as pylint, flake8, isort, bandit, and black have been removed. These have been replaced with Ruff, a more efficient tool that handles both linting and formatting. All configuration settings have been consolidated into the `pyproject.toml` file, simplifying the project's configuration and maintenance. Integration config files like `pre-commit-config.yaml` and `.github/workflows/code_quality.yml` have been updated accordingly. Several rules from Ruff have also been implemented to improve code consistency and quality across the codebase. Additionally, the development dependencies in `dev-requirements.txt` have been updated to their latest versions, ensuring better compatibility and performance. [#813](https://github.com/qilimanjaro-tech/qililab/pull/813)

- `platform.execute_experiment()` and the underlying `ExperimentExecutor` can now handle experiments with multiple qprograms and multiple measurements. Parallel loops are also supported in both experiment and qprogram. The structure of the HDF5 results file as well as the functionality of `ExperimentResults` class have been changed accordingly. [#796](https://github.com/qilimanjaro-tech/qililab/pull/796)

- Added pulse distorsions in `execute_qprogram` for QBlox in a similar methodology to the distorsions implemented in pulse circuits. The runcard needs to contain the same structure for distorsions as the runcards for circuits and the code will modify the waveforms after compilation (inside `platform.execute_qprogram`).

  Example (for Qblox)

  ```yaml
  buses:
  - alias: readout
    ...
    distortions:
      - name: exponential
        tau_exponential: 1.
        amp: 1.
        sampling_rate: 1.  # Optional. Defaults to 1
        norm_factor: 1.  # Optional. Defaults to 1
        auto_norm: True  # Optional. Defaults to True
      - name: bias_tee
        tau_bias_tee: 11000
        sampling_rate: 1.  # Optional. Defaults to 1
        norm_factor: 1.  # Optional. Defaults to 1
        auto_norm: True  # Optional. Defaults to True
      - name: lfilter
        a: []
        b: []
        norm_factor: 1.  # Optional. Defaults to 1
        auto_norm: True  # Optional. Defaults to True
  ```

  [#779](https://github.com/qilimanjaro-tech/qililab/pull/779)

- The execution of `QProgram` has been split into two distinct steps: **compilation** and **execution**.

  1. **Compilation**: Users can now compile a `QProgram` by calling:

  ```python
  platform.compile_qprogram(
    qprogram: QProgram,
    bus_mapping: dict[str, str] | None = None,
    calibration: Calibration | None = None
  )
  ```

  This method can be executed without being connected to any instruments. It returns either a `QbloxCompilationOutput` or a `QuantumMachinesCompilationOutput`, depending on the platform setup.

  2. **Execution**: Once the compilation is complete, users can execute the resulting output by calling:

  ```python
  platform.execute_compilation_output(
    output: QbloxCompilationOutput | QuantumMachinesCompilationOutput,
    debug: bool = False
  )
  ```

  If desired, both steps can still be combined into a single call using the existing method:

  ```python
  platform.execute_qprogram(
    qprogram: QProgram,
    bus_mapping: dict[str, str] | None = None,
    calibration: Calibration | None = None,
    debug: bool = False
  )
  ```

  [#817](https://github.com/qilimanjaro-tech/qililab/pull/817)

- Introduced settable attributes `experiment_results_base_path` and `experiment_results_path_format` in the `Platform` class. These attributes determine the directory and file structure for saving experiment results during execution. By default, results are stored within `experiment_results_base_path` following the format `{date}/{time}/{label}.h5`. [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

- Added a `save_plot=True` parameter to the `plotS21()` method of `ExperimentResults`. When enabled (default: True), the plot is automatically saved in the same directory as the experiment results. [#819](https://github.com/qilimanjaro-tech/qililab/pull/819)

- Improved the transpiler, by making it more modular, and adding a `gate_cancellation()` stage before the transpilation to natives, this stage can be skipped, together with the old `optimize_transpilation()`, if the flag `optimize=False` is passed. [#823](https://github.com/qilimanjaro-tech/qililab/pull/823)

- Split execution of annealing programs into two steps: compilation and execution. [#825](https://github.com/qilimanjaro-tech/qililab/pull/825)

- Added a try and except similar to the dataloss error to restart the measurement in case of random timeout issue for quantum machines. This is a temporary fix and will be deleted once the Quantum Machines team fix their issue.

[#832](https://github.com/qilimanjaro-tech/qililab/pull/832)

### Breaking changes

- Renamed the platform's `execute_anneal_program()` method to `execute_annealing_program()` and updated its parameters. The method now expects `preparation_block` and `measurement_block`, which are strings used to retrieve blocks from the `Calibration`. These blocks are inserted before and after the annealing schedule, respectively.

[#816](https://github.com/qilimanjaro-tech/qililab/pull/816)

- **Major reorganization of the library structure and runcard functionality**. Key updates include:

  - Removed obsolete instruments, such as VNAs.
  - Removed the `drivers` module.
  - Simplified the `Qblox` sequencer class hierarchy into two main classes: `QbloxSequencer` and `QbloxADCSequencer`.
  - Removed `SystemController` and `ReadoutSystemController`; buses now interface directly with instruments.
  - Introduced a new `channels` attribute to the `Bus` class, allowing specification of channels for each associated instrument.
  - Removed the `Chip` class and its related runcard settings.
  - Eliminated outdated settings, such as instrument firmware.
  - Refactored runcard settings into a modular structure with four distinct groups:
    - `instruments` and `instrument_controllers` for lab instrument setup.
    - `buses` for grouping instrument channels.
    - `digital` for digital compilation settings (e.g., Qibo circuits).
    - `analog` for analog compilation settings (e.g., annealing programs).

[#820](https://github.com/qilimanjaro-tech/qililab/pull/820)

### Bug fixes

- Fixed minor type bug in `Platform`. [#846](https://github.com/qilimanjaro-tech/qililab/pull/846)

- Fixed minor type bug in `CrosstalkMatrix`. [#825](https://github.com/qilimanjaro-tech/qililab/pull/825)

- Fixed typo in ExceptionGroup import statement for python 3.11+ [#808](https://github.com/qilimanjaro-tech/qililab/pull/808)

- Fixed serialization/deserialization of lambda functions, mainly used in `experiment.execute_qprogram()` method. The fix depends on the `dill` library which is added as requirement. [#815](https://github.com/qilimanjaro-tech/qililab/pull/815)

- Fixed calculation of Arbitrary waveform's envelope when resolution is greater than 1ns. [#837](https://github.com/qilimanjaro-tech/qililab/pull/837)

## 0.27.1 (2024-09-16)

### New features since last release

- Introduced the possibility to run multiple shots and averages at the same time for `execute_anneal_program` method.
  [#797](https://github.com/qilimanjaro-tech/qililab/pull/797)

- Introduced the `Experiment` class, which inherits from `StructuredProgram`. This new class enables the ability to set parameters and execute quantum programs within a structured experiment. Added the `set_parameter` method to allow setting platfform parameters and `execute_qprogram` method to facilitate the execution of quantum programs within the experiment.
  [#782](https://github.com/qilimanjaro-tech/qililab/pull/782)

- Introduced the `ExperimentExecutor` class to manage and execute quantum experiments within the Qililab framework. This class provides a streamlined way to handle the setup, execution, and results retrieval of experiments.

  Temporary Constraints:

  - The experiment must contain only one `QProgram`.
  - The `QProgram` must contain a single measure operation.
  - Parallel loops are not supported.
    [#790](https://github.com/qilimanjaro-tech/qililab/pull/790)

- Introduced the `platform.execute_experiment()` method for executing experiments. This method simplifies the interaction with the ExperimentExecutor by allowing users to run experiments with a single call.

  Example:

  ```Python
  # Define the QProgram
  qp = QProgram()
  gain = qp.variable(label='resonator gain', domain=Domain.Voltage)
  with qp.for_loop(gain, 0, 10, 1):
      qp.set_gain(bus="readout_bus", gain=gain)
      qp.measure(bus="readout_bus", waveform=IQPair(I=Square(1.0, 1000), Q=Square(1.0, 1000)), weights=IQPair(I=Square(1.0, 2000), Q=Square(1.0, 2000)))

  # Define the Experiment
  experiment = Experiment()
  bias_z = experiment.variable(label='bias_z voltage', domain=Domain.Voltage)
  frequency = experiment.variable(label='LO Frequency', domain=Domain.Frequency)
  experiment.set_parameter(alias="drive_q0", parameter=Parameter.VOLTAGE, value=0.5)
  experiment.set_parameter(alias="drive_q1", parameter=Parameter.VOLTAGE, value=0.5)
  experiment.set_parameter(alias="drive_q2", parameter=Parameter.VOLTAGE, value=0.5)
  with experiment.for_loop(bias_z, 0.0, 1.0, 0.1):
      experiment.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=bias_z)
      with experiment.for_loop(frequency, 2e9, 8e9, 1e9):
          experiment.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=frequency)
          experiment.execute_qprogram(qp)

  # Execute the Experiment and display the progress bar.
  # Results will be streamed to an h5 file. The path of this file is returned from the method.
  path = platform.execute_experiment(experiment=experiment, results_path="/tmp/results/")

  # Load results
  results, loops = load_results(path)
  ```

  [#790](https://github.com/qilimanjaro-tech/qililab/pull/790)

- Introduced a robust context manager `platform.session()` for managing platform lifecycle operations. The manager automatically calls `platform.connect()`, `platform.initial_setup()`, and `platform.turn_on_instruments()` to set up the platform environment before experiment execution. It then ensures proper resource cleanup by invoking `platform.turn_off_instruments()` and `platform.disconnect()` after the experiment, even in the event of an error or exception during execution. If multiple exceptions occur during cleanup (e.g., failures in both `turn_off_instruments()` and `disconnect()`), they are aggregated into a single `ExceptionGroup` (Python 3.11+) or a custom exception for earlier Python versions.

  Example:

  ```Python
  with platform.session():
    # do stuff...
  ```

  [#792](https://github.com/qilimanjaro-tech/qililab/pull/792)

- Add crosstalk compensation to `AnnealingProgram` workflow. Add methods to `CrosstalkMatrix` to ease crosstalk compensation in the annealing workflow
  [#775](https://github.com/qilimanjaro-tech/qililab/pull/775)

- Add default measurement to `execute_anneal_program()` method. This method takes now a calibration file and parameters
  to add the dispersive measurement at the end of the annealing schedule.
  [#778](https://github.com/qilimanjaro-tech/qililab/pull/778)

- Added a try/except clause when executing a QProgram on Quantum Machines cluster that controls the execution failing to perform a turning off of the instrument so the \_qm object gets
  removed. This, plus setting the close_other_machines=True by default allows to open more than one QuantumMachines VM at the same time to allow more than one experimentalist to work at the same time in the cluster.
  [#760](https://github.com/qilimanjaro-tech/qililab/pull/760/)

- Added `__str__` method to qprogram. The string is a readable qprogram.
  [#767](https://github.com/qilimanjaro-tech/qililab/pull/767)

- Added workflow for the execution of annealing programs.

  Example:

  ```Python
  import qililab as ql

  platform = ql.build_platform("examples/runcards/galadriel.yml")
  anneal_program_dict = [
    {qubit_0": {"sigma_x" : 0, "sigma_y": 0, "sigma_z": 1, "phix":1, "phiz":1},
      "qubit_1": {"sigma_x" : 0.1, "sigma_y": 0.1, "sigma_z": 0.1},
      "coupler_0_1": {"sigma_x" : 1, "sigma_y": 0.2, "sigma_z": 0.2}
     },
    {"qubit_0": {"sigma_x" : 0.1, "sigma_y": 0.1, "sigma_z": 1.1},
      "qubit_1": {"sigma_x" : 0.2, "sigma_y": 0.2, "sigma_z": 0.2},
      "coupler_0_1": {"sigma_x" : 0.9, "sigma_y": 0.1, "sigma_z": 0.1}
     },
     {"qubit_0": {"sigma_x" : 0.3, "sigma_y": 0.3, "sigma_z": 0.7},
      "qubit_1": {"sigma_x" : 0.5, "sigma_y": 0.2, "sigma_z": 0.01},
      "coupler_0_1": {"sigma_x" : 0.5, "sigma_y": 0, "sigma_z": -1}
      }
  ]

  results = platform.execute_anneal_program(anneal_program_dict=anneal_program_dict, transpiler=lambda delta, epsilon: (delta, epsilon), averages=100_000)
  ```

  Alternatively, each step of the workflow can be executed separately i.e. the following is equivalent to the above:

  ```python
  import qililab as ql

  platform = ql.build_platform("examples/runcards/galadriel.yml")
  anneal_program_dict = [...]  # same as in the above example
  # intialize annealing program class
  anneal_program = ql.AnnealingProgram(platform=platform, anneal_program=anneal_program_dict)
  # transpile ising to flux, now flux values can be accessed same as ising coeff values
  # eg. for phix qubit 0 at t=1ns anneal_program.anneal_program[1]["qubit_0"]["phix"]
  anneal_program.transpile(lambda delta, epsilon: (delta, epsilon))
  # get a dictionary {control_flux: (bus, waveform) from the transpiled fluxes
  anneal_waveforms = anneal_program.get_waveforms()
  # from here on we can create a qprogram to execute the annealing schedule
  ```

  [#767](https://github.com/qilimanjaro-tech/qililab/pull/767)

- Added `CrosstalkMatrix` class to represent and manipulate a crosstalk matrix, where each index corresponds to a bus. The class includes methods for initializing the matrix, getting and setting crosstalk values, and generating string representations of the matrix.

  Example:

  ```Python
  # Create an empty crosstalk matrix
  crosstalk_matrix = CrosstalkMatrix()

  # Add crosstalk values, where the keys are in matrix shape [row][column]
  crosstalk_matrix["bus1"]["bus2"] = 0.9
  crosstalk_matrix["bus2"]["bus1"] = 0.1

  # Alternatively, create a matrix from a collection of buses.
  # All crosstalk values are initialized to 1.0
  crosstalk_matrix = CrosstalkMatrix.from_buses({"bus1", "bus2", "bus3"})

  # Get a formatted string representation of the matrix
  #        bus1     bus2     bus3
  # bus1   \        1.0      1.0
  # bus2   1.0      \        1.0
  # bus3   1.0      1.0      \

  print(crosstalk_matrix)
  ```

- Added the Qblox-specific `set_markers()` method in `QProgram`. This method takes a 4-bit binary mask as input, where `0` means that the associated marker will be open (no signal) and `1` means that the associated marker will be closed (signal). The mapping between bit indexes and markers depends on the Qblox module that the compiled `QProgram` will run on.

  Example:

  ```Python
  qp = QProgram()
  qp.qblox.set_markers(bus='drive_q0', mask='0111')
  ```

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `set_markers_override_enabled_by_port` and `set_markers_override_value_by_port` methods in `QbloxModule` to set markers through QCoDeS, overriding Q1ASM values.
  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `from_qprogram` method to the `Counts` class to compute the counts of quantum states obtained from a `QProgram`. The `Counts` object is designed to work for circuits that have only one measurement per bus at the end of the circuit execution. It is the user's responsibility to ensure that this method is used appropriately when it makes sense to compute the state counts for a `QProgram`. Note that probabilities can easily be obtained by calling the `probabilities()` method. See an example below.

  Example:

  ```Python
  from qililab.result.counts import Counts

  qp = QProgram()
  # Define instructions for QProgram
  # ...
  qp_results = platform.execute_qprogram(qp)  # Platform previously defined
  counts_object = Counts.from_qprogram(qp_results)
  probs = counts_object.probabilities()
  ```

  [#743](https://github.com/qilimanjaro-tech/qililab/pull/743)

- Added `threshold_rotations` argument to `compile()` method in `QProgram`. This argument allows to use rotation angles on measurement instructions if not specified. Currently used to use the angle rotations specified on the runcard (if any) so the user does not have to explicitly pass it as argument to the measure instruction. Used for classification of results in Quantum Machines's modules. The following example shows how to specify this value on the runcard.

  Example:

  ```yaml
    buses:
      - alias: readout_q0_bus
        system_control:
          name: readout_system_control
          instruments: [QMM]
        port: readout_line_q0
        distortions: []
    instruments:
      - name: quantum_machines_cluster
        alias: QMM
        firmware: ...
        elements:
          - bus: readout_q0_bus
            rf_inputs:
              octave: octave1
              port: 1
            rf_outputs:
              octave: octave1
              port: 1
            time_of_flight: 160
            smearing: 0
            intermediate_frequency: 10.0e+6
            threshold_rotation: 0.5
            threshold: 0.03
    ...
  ```

  [#759](https://github.com/qilimanjaro-tech/qililab/pull/759)

- Added `thresholds` argument to `_execute_qprogram_with_quantum_machines` method in `Platform`. This argument allows to threshold results after the execution of the `QProgram`. It is also a new parameter that can be specified on the runcard for each readout bus. An example of the configuration of this parameter on the runcard can be found above.

  [#762](https://github.com/qilimanjaro-tech/qililab/pull/762)

- Added `filter` argument inside the qua config file compilation from runcards with qm clusters. This is an optional element for distorsion filters that includes feedforward and feedback, two distorion lists for distorsion compensation and fields in qua config filter. These filters are calibrated and then introduced as compensation for the distorsions of the pulses from external sources such as Bias T. The runcard now might include the new filters (optional):

  Example:

  ```
  instruments:
  - name: quantum_machines_cluster
    alias: QMM
    firmware: 0.7.0
    ...
    controllers:
        - name: con1
          analog_outputs:
          - port: 1
            offset: 0.0
            filter:
              feedforward: [0.1,0.1,0.1]
              feedback: [0.1,0.1,0.1]
    ...
  ```

  [#768](https://github.com/qilimanjaro-tech/qililab/pull/768)

- Added loopbacks in the octave config file for qua following the documentation at <https://docs.quantum-machines.co/1.2.0/qm-qua-sdk/docs/Guides/octave/?h=octaves#setting-the-octaves-clock>. By default only port 1 of the octave is linked with a local demodulator, to work with the rest of the ports at the back ports must be connected based on the Octave Block Diagram \[<https://docs.quantum-machines.co/1.2.0/qm-qua-sdk/docs/Hardware/octave/#octave-block-diagram%5C>\]. Where `Synth` is one of the possible 3 synths and `Dmd` is one of the 2 demodulators.

  Example:

  ```
  - name: quantum_machines_cluster
      alias: QMM
      ...
      octaves:
        - name: octave1
          port: 11252
          ...
          loopbacks:
            Synth: Synth2 # Synth1, Synth2, Synth3
            Dmd: Dmd2LO # Dmd1LO, Dmd2LO
  ```

  [#770](https://github.com/qilimanjaro-tech/qililab/pull/770)

- Added delay variables to Qblox qprogram implementation. The delays are added in the runcard in nanoseconds and they can be positive or negative scalars (negative delays will make the rest of buses wait). The delay is a wait applied to each iteration of a loop where the bus is present.

  Example:

  ```
  buses:
  - alias: readout
    ...
    delay: 100
  ```

  [#793](https://github.com/qilimanjaro-tech/qililab/pull/793)

### Improvements

- Improve Crosstalk matrix `from_buses` method so it can be a dictionary of buses and crosstalks coefficients.
  [#784]<https://github.com/qilimanjaro-tech/qililab/pull/784>

- Now platform.get_parameter works for QM without the need of connecting to the machine.

- Added the option to get the time of flight and smearing information from the QM cluster
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.
  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Automatic method to implement the correct `upsampling_mode` when the output mode is selected as `amplified` (fluxes), the `upsampling_mode` is automatically defined as `pulse`. In this mode, the upsampling is optimized to produce cleaner step responses.
  [#783](https://github.com/qilimanjaro-tech/qililab/pull/783)

- Automatic method for `execute_qprogram` in quantum machines to restart the measurement in case the `StreamProcessingDataLossError` is risen by `qua-qm`, the new feature allows to try again the measurement a number of times equal to the value of `dataloss_tries` (default of three). We can define this value at `execute_qprogram(..., dataloss_tries = N)` and will only do its intended job in case of working with QM.
  [#788](https://github.com/qilimanjaro-tech/qililab/pull/788)

### Breaking changes

- Big code refactor for the `calibration` module/directory, where all `comparisons`, `check_parameters`, `check_data()`,
  `check_state()`, `maintain()`, `diagnose()` and other complex unused methods have been deleted, leaving only linear calibration.

  Also some other minor improvements like:

  - `drift_timeout` is now a single one for the full controller, instead of a different one for each node.
  - Notebooks without an export are also accepted now (we will only raise error for multiple exports in a NB).
  - Extended/Improved the accepted type for parameters to input/output in notebooks, thorught json serialization.
    [#746](https://github.com/qilimanjaro-tech/qililab/pull/746)

- Variables in `QProgram` and `Experiment` now require a label.

  ```Python
  qp = QProgram()
  gain = qp.variable(label="gain", domain=Domain.Voltage)
  ```

  [#790](https://github.com/qilimanjaro-tech/qililab/pull/790)

### Deprecations / Removals

- Deleted all the files in `execution` and `experiment` directories (Already obsolete).
  [#749](https://github.com/qilimanjaro-tech/qililab/pull/749)

### Documentation

### Bug fixes

- Hotfix to allow to serialise zeros in yaml.
  [#799](https://github.com/qilimanjaro-tech/qililab/pull/799)

- get_parameter for QM did not work due to the lack of the variable `bus_alias in self.system_control.get_parameter`. The variable has been added to the function and now get parameter does not return a crash.
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- set_parameter for intermediate frequency in quantum machines has been adapted for both OPX+ and OPX1000 following the new requirements for OPX1000 with qm-qua job.set_intermediate_frequency.
  [#764](https://github.com/qilimanjaro-tech/qililab/pull/764)

## 0.27.0 (2024-06-28)

### New features since last release

- Added `Calibration` class to manage calibrated waveforms and weights for QProgram. Included methods to add (`add_waveform`/`add_weights`), check (`has_waveform`/`has_weights`), retrieve (`get_waveform`/`get_weights`), save (`save_to`), and load (`load_from`) calibration data.

  Example:

  ```Python
  # Create a Calibration instance
  calibration = Calibration()

  # Define waveforms and weights
  drag_wf = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4.5, drag_coefficient=-2.5)
  readout_wf = ql.IQPair(I=ql.Square(amplitude=1.0, duration=200), Q=ql.Square(amplitude=0.0, duration=200))
  weights = ql.IQPair(I=ql.Square(amplitude=1.0, duration=200), Q=ql.Square(amplitude=1.0, duration=200))

  # Add waveforms to the calibration
  calibration.add_waveform(bus='drive_q0_bus', name='Xpi', waveform=drag_wf)
  calibration.add_waveform(bus='readout_q0_bus', name='Measure', waveform=readout_wf)

  # Add weights to the calibration
  calibration.add_weights(bus='readout_q0_bus', name='optimal_weights', weights=weights)

  # Save the calibration data to a file
  calibration.save_to('calibration_data.yml')

  # Load the calibration data from a file
  loaded_calibration = Calibration.load_from('calibration_data.yml')
  ```

  The contents of `calibration_data.yml` will be:

  ```YAML
  !Calibration
  waveforms:
    drive_q0_bus:
      Xpi: !IQPair
        I: &id001 !Gaussian {amplitude: 1.0, duration: 40, num_sigmas: 4.5}
        Q: !DragCorrection
          drag_coefficient: -2.5
          waveform: *id001
    readout_q0_bus:
      Measure: !IQPair
        I: !Square {amplitude: 1.0, duration: 200}
        Q: !Square {amplitude: 0.0, duration: 200}
  weights:
    readout_q0_bus:
      optimal_weights: !IQPair
        I: !Square {amplitude: 1.0, duration: 200}
        Q: !Square {amplitude: 1.0, duration: 200}
  ```

  Calibrated waveforms and weights can be used in QProgram by providing their name.

  ```Python
  qp = QProgram()
  qp.play(bus='drive_q0_bus', waveform='Xpi')
  qp.measure(bus='readout_q0_bus', waveform='Measure', weights='optimal_weights')
  ```

  In that case, a `Calibration` instance must be provided when executing the QProgram. (see following changelog entries)

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)
  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- Introduced `qililab.yaml` namespace that exports a single `YAML` instance for common use throughout qililab. Classes should be registered to this instance with the `@yaml.register_class` decorator.

  ```Python
  from qililab.yaml import yaml

  @yaml.register_class
  class MyClass:
      ...
  ```

  `MyClass` can now be saved to and loaded from a yaml file.

  ```Python
  from qililab.yaml import yaml

  my_instance = MyClass()

  # Save to file
  with open(file="my_file.yml", mode="w", encoding="utf-8") as stream:
      yaml.dump(data=my_instance, stream=stream)

  # Load from file
  with open(file="my_file.yml", mode="r", encoding="utf8") as stream:
      loaded_instance = yaml.load(stream)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Added `serialize()`, `serialize_to()`, `deserialize()`, `deserialize_from()` functions to enable a unified method for serializing and deserializing Qililab classes to and from YAML memory strings and files.

  ```Python
  import qililab as ql

  qp = QProgram()

  # Serialize QProgram to a memory string and deserialize from it.
  yaml_string = ql.serialize(qp)
  deserialized_qprogram = ql.deserialize(yaml_string)

  # Specify the class for deserialization using the `cls` parameter.
  deserialized_qprogram = ql.deserialize(yaml_string, cls=ql.QProgram)

  # Serialize to and deserialize from a file.
  ql.serialize_to(qp, 'qprogram.yml')
  deserialized_qprogram = ql.deserialize_from('qprogram.yml', cls=ql.QProgram)
  ```

  [#737](https://github.com/qilimanjaro-tech/qililab/pull/737)

- Added Qblox support for QProgram's `measure` operation. The method can now be used for both Qblox
  and Quantum Machines, and the expected behaviour is the same.

  ```Python
  readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
  weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
  qp = QProgram()

  # The measure operation has the same behaviour in both vendors.
  # Time of flight between readout pulse and beginning of acquisition is retrieved from the instrument's settings.
  qp.measure(bus="readout_bus", waveform=readout_pair, weights=weights_pair, save_adc=True)
  ```

  [#734](https://github.com/qilimanjaro-tech/qililab/pull/734)
  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)
  [#738](https://github.com/qilimanjaro-tech/qililab/pull/738)

- Update Qibo version to `v.0.2.8`.
  [#732](https://github.com/qilimanjaro-tech/qililab/pull/732)

### Improvements

- Introduced `QProgram.with_bus_mapping` method to remap buses within the QProgram.

  Example:

  ```Python
  # Define the bus mapping
  bus_mapping = {"drive": "drive_q0"}

  # Apply the bus mapping to a QProgram instance
  mapped_qprogram = qprogram.with_bus_mapping(bus_mapping=bus_mapping)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)
  [#740](https://github.com/qilimanjaro-tech/qililab/pull/740)

- Introduced `QProgram.with_calibration` method to apply calibrated waveforms and weights to the QProgram.

  Example:

  ```Python
  # Load the calibration data from a file
  calibration = Calibration.load_from('calibration_data.yml')

  # Apply the calibration to a QProgram instance
  calibrated_qprogram = qprogram.with_calibration(calibration=calibration)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)
  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- Extended `Platform.execute_qprogram` method to accept a calibration instance.

  ```Python
  # Load the calibration data from a file
  calibration = Calibration.load_from('calibration_data.yml')

  platform.execute_qprogram(qprogram=qprogram, calibration=calibration)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Added interfaces for Qblox and Quantum Machines to QProgram. The interfaces contain vendor-specific methods and parameters. They can be accessed by `qprogram.qblox` and `qprogram.quantum_machines` properties.

  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- Added `time_of_flight` setting to Qblox QRM and QRM-RF sequencers.

  [#738](https://github.com/qilimanjaro-tech/qililab/pull/738)

### Breaking changes

- QProgram interface now contains methods and parameters that have common functionality for all hardware vendors. Vendor-specific methods and parameters have been move to their respective interface.

  Examples:

  ```Python
  # Acquire method has been moved to Qblox interface. Instead of running
  # qp.acquire(bus="readout_q0_bus", weights=weights)
  # you should run
  qp.qblox.acquire(bus="readout_q0_bus", weights=weights)

  # Play method with `wait_time` parameter has been moved to Qblox interface. Instead of running
  # qp.play(bus="readout_q0_bus", waveform=waveform, wait_time=40)
  # you should run
  qp.qblox.play(bus="readout_q0_bus", waveform=waveform, wait_time=40)

  # `disable_autosync` parameter has been moved to Qblox interface. Instead of running
  # qp = QProgram(disable_autosync=True)
  # you should run
  qp = QProgram()
  qp.qblox.disable_autosync = True

  # Measure method with parameters `rotation` and `demodulation` has been moved to Quantum Machines interface. Instead of running
  # qp.measure(bus="readout_q0_bus", waveform=waveform, weights=weights, save_adc=True, rotation=np.pi, demodulation=True)
  # you should run
  qp.quantum_machines.measure(bus="readout_q0_bus", waveform=waveform, weights=weights, save_adc=True, rotation=np.pi, demodulation=True)
  ```

  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- `time_of_flight` parameter must be added to Qblox QRM and QRM-RF sequencers's runcard settings.

  [#738](https://github.com/qilimanjaro-tech/qililab/pull/738)

### Deprecations / Removals

- Remove `qiboconnection` dependency from Qililab. It is not a requirement anymore.
  [#732](https://github.com/qilimanjaro-tech/qililab/pull/732)

- Following the remove of Qiboconnection, `LivePlot` has been removed along with the creation of a `Platform` via API.
  [#732](https://github.com/qilimanjaro-tech/qililab/pull/732)

- Remove the deprecated `path` argument from `build_platform()`.

  [#739](https://github.com/qilimanjaro-tech/qililab/pull/739)

## 0.26.2 (2024-05-28)

### New features since last release

- Introduce the Two-Step pulse shape to improve readout
  [#730](https://github.com/qilimanjaro-tech/qililab/pull/730)

### Deprecations / Removals

- Remove qiboconnection_api.block_device() and release_device()
  [#728](https://github.com/qilimanjaro-tech/qililab/pull/728)

## 0.26.1 (2024-04-26)

### Bug fixes

- Hotfix for the 2readout problem
  [#720](https://github.com/qilimanjaro-tech/qililab/pull/720)

## 0.25.1 (2024-03-26)

### Bug fixes

- Appended hardcoded Time of Flight
  [#711](https://github.com/qilimanjaro-tech/qililab/pull/711)

## 0.25.0 (2024-03-25)

### New features since last release

- Add FlatTop pulse shape
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

- Add FlatTop waveform
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

- Add support for multiple QRM modules
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

- Update qpysequence to 10.1
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

### Improvements

- The method `CalibrationNode._execute_notebook()` now changes the working directory to the notebook directory before the execution and restores the previous one after the papermill execution. It allows the notebooks now to use relative paths. Also, the initialization of `CalibrationNode` will now contain absolute paths for the attributes `nb_folder` and `nb_path`
  [#693](https://github.com/qilimanjaro-tech/qililab/pull/693)

### Breaking changes

- Added support for Qblox cluster firmware v0.6.1 and qblox-instruments v0.11.2. This changes some of the i/o mappings in the runcard for qblox sequencers so with older versions is broken.
  [#680](https://github.com/qilimanjaro-tech/qililab/pull/680)

### Documentation

- Added documentation for QProgram.

### Bug fixes

- Resolved an issue where attempting to execute a previously compiled QUA program on a newly instantiated Quantum Machine resulted in errors due to cache invalidation.
  [#706](https://github.com/qilimanjaro-tech/qililab/pull/706)

## 0.24.0 (2024-03-05)

### New features since last release

- Introduced a new parameter, `disable_autosync`, to the `QProgram` constructor. This parameter allows users to control the automatic synchronization behavior of loops within their quantum programs. By default, the parameter is set to `False`, enabling the compiler to automatically insert synchronization operations at the conclusion of each loop. Users have the option to set `disable_autosync` to `True` to indicate that they prefer to manage loop timing manually. This feature is particularly useful for operations on Qblox hardware, due to its constraints on dynamic synchronization. It's important to note that Quantum Machines will disregard this setting and adhere to the default synchronization behavior.
  [#694](https://github.com/qilimanjaro-tech/qililab/pull/694)

### Breaking changes

- The unit of measurement for phases within QProgram has been updated from degrees to radians.
  [#695](https://github.com/qilimanjaro-tech/qililab/pull/695)

### Bug fixes

- Resolved an issue encountered during the retrieval of results from QProgram executions on Qblox hardware, where acquisition data from other sequencers would unintentionally be deleted.
  [#691](https://github.com/qilimanjaro-tech/qililab/pull/691)

## 0.23.3 (2024-02-19)

### Bug fixes

- Fixed an issue when serializing / deserializing a QProgram so results are returned in a standard results class.
  [#688](https://github.com/qilimanjaro-tech/qililab/pull/688)

## 0.23.2 (2024-02-13)

### Bug fixes

- Fixed an issue when serializing / deserializing a QProgram that contained an Arbitrary waveform or a DRAG pulse.
  [#686](https://github.com/qilimanjaro-tech/qililab/pull/686)

## 0.23.1 (2024-02-09)

### Bug fixes

- Fixes an equality issue of QProgram's variables that resulted in a slightly different QProgram when serializing and then deserializing.
  [#684](https://github.com/qilimanjaro-tech/qililab/pull/684)

## 0.23.0 (2024-02-09)

### New features since last release

- Allow execution of `QProgram` through `platform.execute_qprogram` method for Quantum Machines hardware.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Allow multiple measurements of the same qubit in a single circuit. Also allow measurements in the middle of a circuit.
  [#674](https://github.com/qilimanjaro-tech/qililab/pull/674)

- Wait times longer than 2\*\*16-4 (QBLOX maximum wait time in a Q1ASM wait instruction) are now allowed in the middle of
  a circuit.
  [#674](https://github.com/qilimanjaro-tech/qililab/pull/674)

- Add method to get sequencer channel id from qubit index and bus alias
  [#678](https://github.com/qilimanjaro-tech/qililab/pull/678)

### Improvements

- Added `bus_mapping` parameter in `QbloxCompiler.compile` method to allow changing the bus names of the compiled output.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Improved `QuantumMachinesCluster` instrument functionality.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Improved execution times of `QProgram` when used inside a software loop by using caching mechanism.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Added `DictSerializable` protocol and `from_dict` utility function to enable (de)serialization (from)to dictionary for any class.
  [#659](https://github.com/qilimanjaro-tech/qililab/pull/659)

- Added method to get the QRM `channel_id` for a given qubit.
  [#664](https://github.com/qilimanjaro-tech/qililab/pull/664)

- Added Domain restrictions to `Drag` pulse, `DragCorrection` waveform and `Gaussian` waveform.
  [#679](https://github.com/qilimanjaro-tech/qililab/pull/679)

- Compilation for pulses is now done at platform instead of being delegated to each bus pointing to an awg instrument. This allows easier
  communication between `pulse_bus_schedules` so that they can be handled at the same time in order to tackle more complex tasks which were
  not possible otherwise. It also decouples, to a great extent, the instruments and instrument controllers (hardware) from higher level processes more typical of quantum control, which are involved in the pulse compilation to assembly program steps.
  [#651](https://github.com/qilimanjaro-tech/qililab/pull/651)

- Changed save and load methods using `PyYAML` to `ruamel.YAML`.
  [#661](https://github.com/qilimanjaro-tech/qililab/pull/661)

- Qprogram's qblox compiler now allows iterations over variables even if these variables do nothing. (eg. iterate over nshots)
  [#666](https://github.com/qilimanjaro-tech/qililab/pull/666)

### Bug fixes

- Added the temporary parameter `wait_time` to QProgram's `play` method. This allows the user to emulate a `time_of_flight` duration for measurement until this is added as a setting in runcard.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

- Fixed issue with Yokogawa GS200 instrument, that raised an error during initial_setup when the instrument's output was on.
  [#648](https://github.com/qilimanjaro-tech/qililab/pull/648)

## 0.22.2 (2024-01-04)

### New features since last release

- Added Yokogawa `GS200` instrument and associated istrument controller.
  [#619](https://github.com/qilimanjaro-tech/qililab/pull/619)

- Added QDevil `QDAC-II` instrument and associated istrument controller.
  [#634](https://github.com/qilimanjaro-tech/qililab/pull/634)

- `set_parameter()` can now be used without being connected to the instruments.
  [#647](https://github.com/qilimanjaro-tech/qililab/pull/647)

### Improvements

- `QuantumMachinesCluster` can be created by translating the runcard into the equivelant QUA config dictionary. `initial_setup`, `turn_on` and `turn_off` methods have been edited to properly instatiate and calibrate the instrument.
  [#620](https://github.com/qilimanjaro-tech/qililab/pull/620)

### Breaking changes

- `QuantumMachinesManager` has been renamed to `QuantumMachinesCluster` and `QMMController` to `QuantumMachinesClusterController`.
  [#620](https://github.com/qilimanjaro-tech/qililab/pull/620)

### Bug fixes

- Fixed [bug #653](https://github.com/qilimanjaro-tech/qililab/issues/635), where saving the runcard would not include the reset parameter in the instrument controllers.
  [#653](https://github.com/qilimanjaro-tech/qililab/pull/653)

## 0.22.1 (2023-12-05)

### Bug fixes

- Fixed [bug #635](https://github.com/qilimanjaro-tech/qililab/issues/635), where trying to read/set the Intermediate
  frequency parameter was failing for Qblox RF modules.
  [#635](https://github.com/qilimanjaro-tech/qililab/pull/635)

## 0.22.0 (2023-11-27)

### New features since last release

- Added real time results saving capability.
  [#598](https://github.com/qilimanjaro-tech/qililab/pull/598)

- Raise an error if a user requests to run a circuit that is longer than `repetition_duration`
  [#621](https://github.com/qilimanjaro-tech/qililab/pull/621)

- Add parameter to the SLURM magic method to configure the time limit of a job.
  [#608](https://github.com/qilimanjaro-tech/qililab/pull/608)

- Add magic method to run python code as slurm jobs from Jupyter Notebooks.
  [#600](https://github.com/qilimanjaro-tech/qililab/pull/600)

- Implemented `QuantumMachinesCompiler` class to compile QPrograms to QUA programs.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Implemented `platform.execute_qprogram()` method to execute a qprogram on Qblox hardware.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Added the two main classes need for automatic-calibration, `CalibrationController` and `CalibrationNode`
  [#554](https://github.com/qilimanjaro-tech/qililab/pull/554)

- Added the driver for Quantum Machines Manager and a new QuantumMachinesResult class to handle Quantum Machines instruments.
  [#568](https://github.com/qilimanjaro-tech/qililab/pull/568)

- Implemented the `QuantumMachinesMeasurementResult` class to store data acquired from a single instrument.
  [#596](https://github.com/qilimanjaro-tech/qililab/pull/596)

### Improvements

- Improved the UX for circuit transpilation by unifying the native gate and pulse transpiler under one `CircuitTranspiler` class, which has 3 methods:

  - `circuit_to_native`: transpiles a qibo circuit to native gates (Drag, CZ, Wait, M) and optionally RZ if optimize=False (optimize=True by default)
  - `circuit_to_pulses`: transpiles a native gate circuit to a `PulseSchedule`
  - `transpile_circuit`: runs both of the methods above sequentially
    `Wait` gate moved from the `utils` module to `circuit_transpilation_native_gates`
    [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

- Added `infinite_loop()` method to QProgram.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Added `measure()` method to QProgram.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Various improvements in the compilation flow of `QbloxCompiler`.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Updated `qm-qua` library to latest `1.1.5.1`.
  [#596](https://github.com/qilimanjaro-tech/qililab/pull/596)

### Breaking changes

- Changed `resolution` parameter of waveforms' `envelope()` method to integer.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

- Changed the way variables work within a QProgram. Variables are now instantiated based on the physical domain they affect.
  [#563](https://github.com/qilimanjaro-tech/qililab/pull/563)

### Deprecations / Removals

- Removed the park gate since it is no longer needed
  [#575](https://github.com/qilimanjaro-tech/qililab/pull/575)

### Bug fixes

- Fixed [bug #626](https://github.com/qilimanjaro-tech/qililab/issues/626), where a regression bug was introduced by adding empty schedules to all flux buses, not only the ones with an AWG registered instrument, as it was intended originally.
  [#628](https://github.com/qilimanjaro-tech/qililab/pull/628)

- Fixed [bug #579](https://github.com/qilimanjaro-tech/qililab/issues/579), were now all `yaml.dumps` are done with [ruamel](https://yaml.readthedocs.io/en/latest/#changelog), for not losing decimals precisons, and also following the previous bug due to the elimination of `ruamel.yaml.round_trip_dump`, the version of ruamel in qililab got fixed, and imports where rewritten for more clarity
  [#578](https://github.com/qilimanjaro-tech/qililab/pull/578)

## 0.21.1 (2023-10-31)

### New features since last release

- Enums for gate options
  [#589](https://github.com/qilimanjaro-tech/qililab/pull/589)

- Two new enums for SNZ gate
  [#587](https://github.com/qilimanjaro-tech/qililab/pull/587)

### Bug fixes

- Fixed [bug](https://github.com/qilimanjaro-tech/qililab/issues/584) where executing multiple circuits with each measuring different qubits would launch measurements for previously measured
  qubits even if those did not have measurements on the circuit currently being executed.
  [#576](https://github.com/qilimanjaro-tech/qililab/pull/576)

- [ruamel 0.18.0](https://yaml.readthedocs.io/en/latest/#changelog) eliminated `ruamel.yaml.round_trip_dump`, so we changed its usage to the recommended version: `ruamel.yaml.YAML().dump` [#577](https://github.com/qilimanjaro-tech/qililab/pull/577)

## 0.21.0 (2023-10-20)

### New features since last release

- Changed gate settings serialization so that fields with None values are not in the resulting dictionary
  [#562](https://github.com/qilimanjaro-tech/qililab/pull/562)

- Update qiboconnection to 0.12.0
  [#559](https://github.com/qilimanjaro-tech/qililab/pull/559)

- Added phase correction for CZ gates to the optimize step of translate circuit in `qililab.transpiler.transpiler`. Gates now can accept an optional dicionary with additional settings.
  As an example, the CZ phase correction can be added at options for each qubit:

  ```yaml
  CZ(0,2):
  - bus: flux_line_q2_bus
    pulse:
      amplitude: 1.0
      phase: 0
      duration: 101
      shape:
        name: snz
        t_phi: 1
        b: 0.5
      options:
        q0_phase_correction: 0.1
        q2_phase_correction: 0.2
  ```

  The default value for the `optimize` flag in qililab.transpiler.transpiler.translate_circuit has been changed from `False` to `True`

  [#552](https://github.com/qilimanjaro-tech/qililab/pull/552)

- build_platform() has been extended: [#533](https://github.com/qilimanjaro-tech/qililab/pull/533)

  Now appart from passing the runcard YAML file path, you can directly pass an already build dictionary.

  Also the argument has changed names from `path` to `runcard`.

- Buses serialization have been implemented: [#515](https://github.com/qilimanjaro-tech/qililab/pull/515)

  When printing the runcard, in the buses part we will now have the normal Buses serialization, plus the parameters of the instruments associated to that bus, with the `to_dict/from_dict` methods.\`

  Also the serialization includes using the `set/get_params` for setting/getting the instruments params.

- Distorsions and PulseShapes have been improved: [#512](https://github.com/qilimanjaro-tech/qililab/pull/512)

  They now work for `amplitude=0`, and for negative and `snz` envelopes (both positive and negatives)

  It now also adds the `norm_factor` parameter for manual normalization to all the distortions (previously only in the lfilter distortion)

  And finally we also have added the option to skip the automatic normalization that we do, setting the parameter `auto_norm` to `False`, (defaults to `True`).

  Plus, added a lots of tests and documentation to both classes.

- Fixed bug which did not allow gaussian waveforms to have amplitude 0
  [#471](https://github.com/qilimanjaro-tech/qililab/pull/471)

- Delete `Schema` class from `Platform` and `RuncardSchema` classes (and from the rest of qililab).

  Also `RuncardSchema` is now called simply `Runcard` (since its the class that maps our runcard files).

  This PR brings importants simplifications to the full qililab structure, now the runcard will have the following structure:

  ```yaml
  name: ...

  device_id: ...

  gates_settings:   # Old `settings` without name & device_id
    ...

  chip:
    ...

  buses:
    ...

  instruments:
    ...

  instrument_controllers:
    ...
  ```

  instead than the previous:

  ```yaml
  settings:
    name: ...
    device_id: ...
    ...

  schema:   # Schema disappears from the platform.
    chip:
      ...

    buses:
      ...

    instruments:
      ...

    instrument_controllers:
      ...
  ```

  Notice also how `settings` (and his respective class `PlatformSettings`) has changed to `gates_settings` (and the class to `GatesSettings` having the runcard string and the class the same name now, before they didn't).

  [#475](https://github.com/qilimanjaro-tech/qililab/pull/475)
  [#505](https://github.com/qilimanjaro-tech/qililab/pull/505)

- Simplify circuit gate to pulse transpilation.
  Previous hardware gates are removed. Now gates can be defined in the runcard as a list of
  `GateEvent` items with bus, wait time (optional) and pulse information. This allows more
  customization and freedom of what a certain gate does. The gate will be transpiled as long
  as the circuit gate's name and qubits match those of the gate in the runcard.
  An example of a custom gate for the circuit X gate at qubit 0 and a CZ gate at (0,1)

  ```yaml
  X(0):
  - bus: drive_line_q0_bus  # alias of the bus
    wait_time: 200
    pulse:
      amplitude: 0.5
      phase: 0
      duration: 200
      frequency: 0
      shape:
        name: drag
        drag_coefficient: 1
        num_sigmas: 2
  - bus: flux_line_q0_bus  # alias of the bus
    pulse:
      amplitude: 1.0
      phase: 0
      duration: 200
      frequency: 0
      shape:
        name: rectangular

  CZ(0,1):
  - bus: flux_line_q0_bus  # park pulse
    pulse:
      amplitude: 0.5
      phase: 0
      duration: 241
      frequency: 0
      shape:
        name: rectangular
  - bus: flux_line_q1_bus  # snz
    wait_time: 40 # wait 40ns after start of the park pulse
    pulse:
      amplitude: 1
      phase: 0
      duration: 201
      frequency: 0
      shape:
        name: snz
        b: 0.5
        t_phi: 1
  ```

  Experiments can access `GateEvent` items by using the gate and qubit `alias` like previously
  and adding `_item` to access a `GateEvent` that is not the first event of the gate.
  For example, `set_parameter(parameter='amplitude', value=0.8, alias='X(0)')` will set the amplitude
  in the gate setting above from 0.5 to 0.8. This is equivalent to `alias='X(0)_0'`. However
  `alias='X(0)_1'` sets instead the amplitude of the second event (`bus=flux_line_q0_bus`) from
  1.0 to 0.8
  [#472](https://github.com/qilimanjaro-tech/qililab/pull/472)

- Rename Experiment and CircuitExperiment classes and dependencies:
  This branch renames the Experiment class to BaseExperiment and CircuitExperiment to Experiment.
  [#482](https://github.com/qilimanjaro-tech/qililab/pull/482)

- Add a new Factory for the Buses and registered the current ones
  [#487](https://github.com/qilimanjaro-tech/qililab/pull/487)

- Add the NEW_DRIVERS flag to choose between old and new instruments and bus drivers.
  [#486](https://github.com/qilimanjaro-tech/qililab/pull/486)

- Add a new Factory for the InstrumentDrivers and registered the current ones
  [#473](https://github.com/qilimanjaro-tech/qililab/pull/473)

- Add interfaces and drivers for Flux bus:
  This PR brings the qililab implementation of the Flux bus driver and unittests.
  [#469](https://github.com/qilimanjaro-tech/qililab/pull/469)

- Add ReadoutBus class.
  [#465](https://github.com/qilimanjaro-tech/qililab/pull/465)

- Fix: check whether cluster has submodules not present at init time.
  [#477](https://github.com/qilimanjaro-tech/qililab/pull/477)

- Add interfaces and drivers for Voltage and Current sources:
  This PR brings the qililab implementation of the Keithly2600 and Yokowaga QCodes drivers and unittests.
  [#438](https://github.com/qilimanjaro-tech/qililab/pull/438)

- Fix: add acquisitions and weights to Sequencer QRM
  [#461](https://github.com/qilimanjaro-tech/qililab/pull/461)

- Add DriveBus and its interface for the new bus structure.
  [457](https://github.com/qilimanjaro-tech/qililab/pull/457)

- Add QProgram for developing quantum programs in the bus level, the operations `Play`, `Sync`, `Wait`, `Acquire`, `SetGain`, `SetOffset`, `SetFrequency`, `SetPhase`, `ResetPhase`, and the iteration blocks `AcquireLoop` and `Loop`.
  [452](https://github.com/qilimanjaro-tech/qililab/pull/452)

- Add QBloxCompiler for compiling QProgram into QPySequence.
  [481](https://github.com/qilimanjaro-tech/qililab/pull/481)

- Add waveforms for the new QProgram
  [456](https://github.com/qilimanjaro-tech/qililab/pull/456)

- Add interface for Voltage and Current sources
  [#448](https://github.com/qilimanjaro-tech/qililab/pull/448)

- New AWG Interface + SequencerQCM, Pulsar, QCM-QRM drivers
  [#442](https://github.com/qilimanjaro-tech/qililab/pull/442)

- New Digitiser interface + SequencerQRM driver
  [#443](https://github.com/qilimanjaro-tech/qililab/pull/442)

- Add interface for the Attenuator.
  This is part of the "Promoting Modular Autonomy" epic.
  [#432](https://github.com/qilimanjaro-tech/qililab/pull/432)

- Added new drivers for Local Oscillators inheriting from QCoDeS drivers and Local Oscillator interface.
  This is part of the "Promoting Modular Autonomy" epic.
  [#437](https://github.com/qilimanjaro-tech/qililab/pull/437)

- Add qcodes_contrib_drivers (0.18.0) to requierements
  [#440](https://github.com/qilimanjaro-tech/qililab/pull/440)

- Update qcodes to latest current version (0.38.1)
  [#431](https://github.com/qilimanjaro-tech/qililab/pull/431)

- Added hotfix for bus delay issue from Hardware:
  This fix adds a delay for each pulse on a bus
  [#439](https://github.com/qilimanjaro-tech/qililab/pull/439)

- Added `T1` portfolio experiment
  [#409](https://github.com/qilimanjaro-tech/qililab/pull/409)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- Added `T2Echo` portfolio experiment
  [#415](https://github.com/qilimanjaro-tech/qililab/pull/415)

- The `ExecutionManager` can now be built from the loops of the experiment.
  This is done by `alias` matching, the loops will be executed on the bus with the same `alias`.
  Note that aliases are not unique, therefore the execution builder will use the first bus alias that matches the loop alias. An exception is raised if a `loop.alias` does not match any `bus.alias` specified in the runcard
  [#320](https://github.com/qilimanjaro-tech/qililab/pull/320)

- The `Experiment` class has been changed to support a more general definition of experiment by removing the
  `circuits` and `pulse_schedules`. A new class `CircuitExperiment` inherits from the new `Experiment` class has the previous attributes and all the functionality the old `Experiment` had.

  ```python
  experiment = Experiment(platform=platform, options=options)
  experiment_2 = CircuitExperiment(platform=platform, options=options, circuits=[circuit])
  ```

  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

- Added `threshold_rotation` parameter to `AWGADCSequencer`. This adds a new parameter to the runcard of sequencers of that type, QRM sequencers in the case of Qblox. This value is an angle expressed in degrees from 0.0 to 360.0.

  ```yaml
  awg_sequencers:
    - identifier: 0
      chip_port_id: 1
      intermediate_frequency: 1.e+08
      weights_path0: [0.98, ...]
      weights_path1: [0.72, ...]
      weighed_acq_enabled: true
      threshold: 0.5
      threshold_rotation: 45.0 # <-- new line
  ```

  [#417](https://github.com/qilimanjaro-tech/qililab/pull/417)

### Improvements

- Add `ForLoop` iteration method to QProgram.
  [481](https://github.com/qilimanjaro-tech/qililab/pull/481)

- Add `Parallel` block to QProgram to allow parallel loops, and compilation support to QBloxCompiler.
  [496](https://github.com/qilimanjaro-tech/qililab/pull/496)

- Allow CZ gates to use different pulse shapes
  [#406](https://github.com/qilimanjaro-tech/qililab/pull/406)

- Add support for the `Wait` gate

- Addeds support for the `Wait` gate
  [#405](https://github.com/qilimanjaro-tech/qililab/pull/405)

- Added support for `Parameter.Gate_Parameter` in `experiment.set_parameter()` method. In this case, alias is a, convertable to integer, string that denotes the index of the parameter to change, as returned by `circuit.get_parameters()` method.
  [#404](https://github.com/qilimanjaro-tech/qililab/pull/404)

- The `Chip` class now uses the `alias` of each node to define node connections.
  [#494](https://github.com/qilimanjaro-tech/qililab/pull/494)

  Before:

  ```yaml
  chip:
  nodes:
    - name: qubit
      alias: qubit_0
      id_: 0
      qubit_index: 0
      frequency: 4.92e+09
      nodes: [2, 10, 20, 30]
  ```

  Now:

  ```yaml
  chip:
  nodes:
    - name: qubit
      alias: qubit_0
      qubit_index: 0
      frequency: 4.92e+09
      nodes: [qubit_2, resonator_q0, drive_line_q0, flux_line_q0]
  ```

- `ql.execute` now accepts a list of circuits!
  [#549](https://github.com/qilimanjaro-tech/qililab/pull/549)

### Breaking changes

- Old scripts using `Experiment` with circuits should be changed and use `CircuitExperiment` instead.
  [#334](https://github.com/qilimanjaro-tech/qililab/pull/334)

### Deprecations / Removals

- `id` and `category` attributes have been removed from `qililab`.
  [#494](https://github.com/qilimanjaro-tech/qililab/pull/494)

### Documentation

- Documentation for the Chip module: [#553] (<https://github.com/qilimanjaro-tech/qililab/pull/553>)

  Includes documentation for all public features of the Chip module

- Documentation for the Pulse module: [#532](https://github.com/qilimanjaro-tech/qililab/pull/532)

  Includes documentation for all public features of the Pulse module

- Added documentation for platform module and the tutorial sections of Platform and Runcards: [#531](https://github.com/qilimanjaro-tech/qililab/pull/531/files)

### Bug fixes

- Avoid creating empty sequences for buses that are no flux lines and do for flux ones that do not have any AWG instrument.
  [#556](https://github.com/qilimanjaro-tech/qililab/pull/bug-557)

- The `threshold` and `threshold_rotation` parameters of a `QbloxQRM` can now be set using `Platform.set_parameter`.
  [#534](https://github.com/qilimanjaro-tech/qililab/pull/534)

- The `QbloxQRMRF` and `QbloxQCMRF` do not save an empty list for the parameter `out_offsets` in the saved runcard.
  [#565](https://github.com/qilimanjaro-tech/qililab/pull/565)

- The `save_platform` now saves in the yaml file float values with the same precision as in the `Platform` object.
  [#565](https://github.com/qilimanjaro-tech/qililab/pull/565)

## 0.20.0 (2023-05-26)

### New features since last release

- Added hotfixes for several issues encountered during the hackathon:
  [#413](https://github.com/qilimanjaro-tech/qililab/pull/413)

  - Save experiments flag for experiments execute method

  ```python
  # Option 1 (Default, save_experiment=True)
  experiment = Experiment(platform=platform, circuits=circuits, options=options)
  experiment.execute()

  # Option 2 (Equivalent to option 1, save_experiment=False)
  experiment = Experiment(platform=platform, circuits=circuits, options=options)
  experiment.execute(save_experiment=False)
  ```

  - Empty sequences to avoid creating repeated programs.
  - Create empty programs for all qubit flux lines to activate calibrated offsets.
  - Added method to get qubits from the chip

  ```python
  qubits = ql.Chip.qubits()
  ```

- Added to the `draw()` method the option of specifying if you want:

  - modulation or not,
  - plot the real, iamginary, absolute or any combination of these options
  - specify the type of plotline to use, such as "-", ".", "--", ":"...
    for the classes `Experimental` and `ExecutionManager`, like:

  ```python
  # Option 1 (Default)
  figure = sample_experiment.draw(real=True, imag=True, abs=False, modulation=True, linestyle="-")

  # Option 2 (Equivalent to option 1)
  figure = sample_experiment.draw()

  # Option 3 (something different, only plotting the envelopes without modulation)
  figure = sample_experiment.draw(modulation=False, linestyle=".")

  plt.show()
  ```

  [#383](https://github.com/qilimanjaro-tech/qililab/pull/383)

- Added `lambda_2` attribute to the `cosine.py` module containing the `Cosine` pulse_shape, modifying the previous A/2\*(1-cos(x)).
  Into a more general A/2\*(1-lambda_1*cos(phi)-lambda_2*cos(2phi)), giving a modified sinusoidal-gaussian.

  - lambda_1 cosine A/2\*(1-cos(x)): Starts at height 0 (phase=0), maximum height A (phase=pi)
    and ends at height 0 (phase=2pi). Which is a sinusoidal like gaussian.

  - lambda_2 cosine A/2\*(1-cos(2x)): Starts at height 0 (phase=0), maximum height A (phase=pi/2)
    then another height 0 in the middle at phase=pi, then another maximum height A (phase=3/2pi)
    and ends at height 0 (phase=2pi).

  For more info check the docstring and the following references:

  - Supplemental material B. "Flux pulse parametrization" at \[<https://arxiv.org/abs/1903.02492%5C%5D>\],
  - OPTIMAL SOLUTION: SMALL CHANGE IN θ at \[<https://arxiv.org/abs/1402.5467%5C%5D>\]

  [#385](https://github.com/qilimanjaro-tech/qililab/pull/385)

- Added user integration for `pulse_distortions`. Now they can be used writing them in the Buses of the runcards:

  ```python
  buses:
    - id_: 0
      category: bus
      alias: feedline_bus
      system_control:
        id_: 0
        name: readout_system_control
        category: system_control
        instruments: [QRM1, rs_1]
      port: 100
      distortions: # <-- new line
        - name: bias_tee # <-- new line
          tau_bias_tee: 1.0 # <-- new line
        - name: lfilter # <-- new line
          a: [0.1, 1.1] # <-- new line
          b: [1.1, 1.3] # <-- new line
    - id_: 10
      category: bus
      alias: drive_line_q0_bus
      system_control:
        id_: 10
        name: system_control
        category: system_control
        instruments: [QCM-RF1]
      port: 10
      distortions: [] # <-- new line
  ```

  [#372](https://github.com/qilimanjaro-tech/qililab/pull/372)

- Added CZ gate support, 2 qubit gate support to `circuit_to_pulse` and corresponding definitions to the runcard.

  CZ implements a Sudden Net Zero (SNZ) pulse through the flux line as well as a parking gate (if defined in the runcard)
  to adjacent qubits with lower frequency than CZ's target qubit.
  For the parking gate, if the time is greater than the CZ pulse, the extra time is added as padding at the beginning/end
  of the pulse.
  The parameters for the CZ in the runcard are amplitude, duration *of the halfpulse*; and for the CZ's snz pulse b
  (impulse between halfpulses) and t_phi (time between halfpulses without accounting for b)

  Example:

  ```yaml
  gates:
   1:
     - name: Park
       amplitude: 1.0
       phase: 0
       duration: 103
       shape:
         name: rectangular

   (0,2):
     - name: CZ
       amplitude: 1.0
       phase:
       duration: 40
       shape:
         name: snz
         b: 0.5
         t_phi: 1
  ```

  In the example above, if qubit 1 is connected to 2 and has lower frequency, there will be an attempt to apply a parking
  pulse. If a Park gate definition is found for qubit 1, then a parking pulse will be applied.
  The total duration of the CZ gate above will be 2\*duration + t_phi + 2 = 83 (each b has 1ns duration and there are 2 bs).
  Thus the parking gate lasts for some extra 20ns which will result in 10ns 'pad time' in the parking gate before and after
  the SNZ pulse.
  Note that the order of the qubits in the CZ is important even if the gate is symmetric, because the second qubit will be
  the target for the SNZ pulse.
  [#369](https://github.com/qilimanjaro-tech/qililab/pull/369/)

- Added `cosine.py` module containing a `Cosine` child class of `pulse_shape`, which gives a sinusoidal like gaussian A/2\*(1-cos(x)).
  The shape starts at height 0 (phase=0), maximum height A (phase=pi) and ends at height 0 (phase=2pi)

  ```python
  pulse = Pulse(
      amplitude=...,
      phase=...,
      duration=...,
      frequency=...,
      pulse_shape=Cosine(),
  )
  ```

  [#376](https://github.com/qilimanjaro-tech/qililab/pull/376)

- Added `pulse.pulse_distortion.lfilter_correction.py` module, which is another child class for the `pulse.pulse_distortion` package.

  ```python
  distorted_envelope = LFilter(norm_factor=1.2, a=[0.7, 1.3], b=[0.5, 0.6]).apply(original_envelopes)
  ```

  Also adds a phase property to `PulseEvent` and implements `Factory.get` directly in the `from_dict()` method of the parent class `PulseDistortion`.

  [#354](https://github.com/qilimanjaro-tech/qililab/pull/354)

- Added `get_port_from_qubit_idx` method to `Chip` class. This method takes the qubit index and the line type as arguments and returns the associated port.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

- Added `pulse.pulse_distortion` package, which contains a module `pulse_distortion.py` with the base class to distort envelopes in `PulseEvent`, and two modules `bias_tee_correction.py` and `exponential_decay_correction.py`, each containing examples of distortion child classes to apply. This new feature can be used in two ways, directly from the class itself:

  ```python
  distorted_envelope = BiasTeeCorrection(tau_bias_tee=1.0).apply(original_envelope)
  ```

  or from the class PulseEvent (which ends up calling the previous one):

  ```python
  pulse_event = PulseEvent(
      pulse="example_pulse",
      start_time="example_start",
      distortions=[
          BiasTeeCorrection(tau_bias_tee=1.0),
          BiasTeeCorrection(tau_bias_tee=0.8),
      ],
  )
  distorted_envelope = pulse_event.envelope()
  ```

  This would apply them like: BiasTeeCorrection_0.8(BiasTeeCorrection_1.0(original_pulse)), so the first one gets applied first and so on...
  (If you write their composition, it will be in reverse order respect the list)

  Also along the way modified/refactored the to_dict() and from_dict() and envelope() methods of PulseEvent, Pulse, PulseShape... since they had some bugs, such as:

  - the dict() methods edited the external dictionaries making them unusable two times.
  - the maximum of the envelopes didn't correspond to the given amplitude.

  [#294](https://github.com/qilimanjaro-tech/qililab/pull/294)

- The `QbloxQCMRF` module has been added. To use it, please use the `QCM-RF` name inside the runcard:

  ```yaml
  - name: QCM-RF
    alias: QCM-RF0
    id_: 2
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    out0_lo_freq: 3700000000  # <-- new line
    out0_lo_en: true  # <-- new line
    out0_att: 10  # <-- new line
    out0_offset_path0: 0.2  # <-- new line
    out0_offset_path1: 0.07  # <-- new line
    out1_lo_freq: 3900000000  # <-- new line
    out1_lo_en: true  # <-- new line
    out1_att: 6  # <-- new line
    out1_offset_path0: 0.1  # <-- new line
    out1_offset_path1: 0.6  # <-- new line
    awg_sequencers:
      ...
  ```

  [#327](https://github.com/qilimanjaro-tech/qililab/pull/327)

- The `QbloxQRMRF` module has been added. To use it, please use the `QRM-RF` name inside the runcard:

  ```yaml
  - name: QRM-RF
    alias: QRM-RF0
    id_: 0
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    out0_in0_lo_freq: 3000000000  # <-- new line
    out0_in0_lo_en: true  # <-- new line
    out0_att: 34  # <-- new line
    in0_att: 28  # <-- new line
    out0_offset_path0: 0.123  # <-- new line
    out0_offset_path1: 1.234  # <-- new line
    acquisition_delay_time: 100
    awg_sequencers:
      ...
  ```

  [#330](https://github.com/qilimanjaro-tech/qililab/pull/330)

### Improvements

- The `get_bus_by_qubit_index` method of `Platform` class now returns a tuple of three buses: `flux_bus, control_bux, readout_bus`.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

- Arbitrary mapping of I/Q channels to outputs is now possible with the Qblox driver. When using a mapping that is not
  possible in hardware, the waveforms of the corresponding paths are swapped (in software) to allow it. For example,
  when loading a runcard with the following sequencer mapping a warning should be raised:

  ```yaml
  awg_sequencers:
  - identifier: 0
    output_i: 1
    output_q: 0
  ```

  ```pycon
  >>> platform = build_platform(name=runcard_name)
  [qililab] [0.16.1|WARNING|2023-05-09 17:18:51]: Cannot set `output_i=1` and `output_q=0` in hardware. The I/Q signals sent to sequencer 0 will be swapped to allow this setting.
  ```

  Under the hood, the driver maps `path0 -> output0` and `path1 -> output1`.
  When applying an I/Q pulse, it sends the I signal through `path1` and the Q signal through `path0`.
  [#324](https://github.com/qilimanjaro-tech/qililab/pull/324)

- The versions of the `qblox-instruments` and `qpysequence` requirements have been updated to `0.9.0`
  [#337](https://github.com/qilimanjaro-tech/qililab/pull/337)

- Allow uploading negative envelopes on the `QbloxModule` class.
  [#356](https://github.com/qilimanjaro-tech/qililab/pull/356)

- The parameter `sync_en` of the Qblox sequencers is now updated automatically when uploading a program to a sequencer.
  This parameter can no longer be set using `set_parameter`.
  [#353](https://github.com/qilimanjaro-tech/qililab/pull/353)

- The Qblox RF modules now support setting their LO frequency using the generic `Parameter.LO_FREQUENCY` parameter.
  [#455](https://github.com/qilimanjaro-tech/qililab/pull/455)

### Deprecations / Removals

- Remove the `awg_iq_channels` from the `AWG` class. This mapping was already done within each sequencer.
  [#323](https://github.com/qilimanjaro-tech/qililab/pull/323)

- Remove the `get_port` method from the `Chip` class.
  [#362](https://github.com/qilimanjaro-tech/qililab/pull/362)

### Bug fixes

- Add `_set_markers` method to the `QbloxModule` class and enable all markers. For the RF modules, this command
  enables the outputs/inputs of the instrument. We decided to enable all markers by default to be able to use them
  later if needed.
  [#361](https://github.com/qilimanjaro-tech/qililab/pull/361)

## 0.19.0 (2023-05-08)

### New features since last release

- Added Drag gate support to `circuit_to_pulse` so that Drag gates are implemented as drag pulses
  [#312](https://github.com/qilimanjaro-tech/qililab/pull/312)

- Added `experiment/portfolio/` submodule, which will contain pre-defined experiments and their analysis.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `ExperimentAnalysis` class, which contains methods used to analyze the results of an experiment.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `Rabi` portfolio experiment. Here is a usage example:

  ```python
  loop_range = np.linspace(start=0, stop=1, step=0.1)
  rabi = Rabi(platform=platform, qubit=0, range=loop_range)
  rabi.turn_on_instruments()

  bus_parameters = {Parameter.GAIN: 0.8, Parameter.FREQUENCY: 5e9}
  rabi.bus_setup(bus_parameters, control=True)  # set parameters of control bus
  x_parameters = {Parameter.DURATION: 40}
  rabi.gate_setup(x_parameters, gate="X")  # set parameters of X gate

  rabi.build_execution()
  results = rabi.run()  # all the returned values are also saved inside the `Rabi` class!
  post_processed_results = rabi.post_process_results()
  fitted_parameters = rabi.fit()
  fig = rabi.plot()
  ```

  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `FlippingSequence` portfolio experiment.
  [#245](https://github.com/qilimanjaro-tech/qililab/pull/245)

- Added `get_bus_by_qubit_index` method to the `Platform` class.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- Added `circuit` module, which contains everything related to Qililab's internal circuit representation.

  The module contains the following submodules:

  - `circuit/converters`: Contains classes that can convert from external circuit representation to Qililab's internal circuit representation and vice versa.
  - `circuit/nodes`: Contains classes representing graph nodes that are used in circuit's internal graph data structure.
  - `circuit/operations`: Contains classes representing operations that can be added to the circuit.
    [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `Circuit` class for representing quantum circuits. The class stores the quantum circuit as a directed acyclic graph (DAG) using the `rustworkx` library for manipulation. It offers methods to add operations to the circuit, calculate the circuit's depth, and visualize the circuit. Example usage:

  ```python
  # create a Circuit with two qubits
  circuit = Circuit(2)

  # add operations
  for qubit in [0, 1]:
      circuit.add(qubit, X())
  circuit.add(0, Wait(t=100))
  circuit.add(0, X())
  circuit.add((0, 1), Measure())

  # print depth of circuit
  print(f"Depth: {circuit.depth}")

  # print circuit
  circuit.print()

  # draw circuit's graph
  circuit.draw()
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `OperationFactory` class to register and retrieve operation classes based on their names.
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `CircuitTranspiler` class for calculating operation timings and transpiling quantum circuits into pulse operations. The `calculate_timings()` method annotates operations in the circuit with timing information by evaluating start and end times for each operation. The `remove_special_operations()` method removes special operations (Barrier, Wait, Passive Reset) from the circuit after the timings have been calculated. The `transpile_to_pulse_operations()` method then transpiles the quantum circuit operations into pulse operations, taking into account the calculated timings. Example usage:

  ```python
  # create the transpiler
  transpiler = CircuitTranspiler(settings=platform.settings)

  # calculate timings
  circuit_ir1 = transpiler.calculate_timings(circuit)

  # remove special operations
  circuit_ir2 = transpiler.remove_special_operations(circuit_ir1)

  # transpile operations to pulse operations
  circuit_ir3 = transpiler.transpile_to_pulse_operations(circuit_ir2)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Added `QiliQasmConverter` class to convert a circuit from/to QiliQASM, an over-simplified QASM version. Example usage:

  ```python
  # Convert to QiliQASM
  qasm = QiliQasmConverter.to_qasm(circuit)
  print(qasm)

  # Parse from QiliQASM
  parsed_circuit = QiliQasmConverter.from_qasm(qasm)
  ```

  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- Pulses with different frequencies will be automatically sent and read by different sequencers (multiplexed readout).
  [#242](https://github.com/qilimanjaro-tech/qililab/pull/242)

- Added an optional parameter "frequency" to the "modulated_waveforms" method of the Pulse and PulseEvent classes, allowing for specification of a modulation frequency different from that of the Pulse.
  [#242](https://github.com/qilimanjaro-tech/qililab/pull/242)

- Added `values` and `channel_id` attribute to the `Loop` class.
  Here is an example on how a loop is created now:

  ```python
  new_loop = Loop(alias="loop", parameter=Parameter.POWER, values=np.linspace(1, 10, 10))
  ```

  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- Gate settings can be set for each qubit individually, or tuple of qubits in case of two-qubit gates.
  Example of updated runcard schema:

  ```yaml
  gates:
    0:
      - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
      - name: X
        amplitude: 1.0
        phase: 0
        duration: 100
        shape:
          name: gaussian
          num_sigmas: 4
    1:
      - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
      - name: X
        amplitude: 1.0
        phase: 0
        duration: 100
        shape:
          name: gaussian
          num_sigmas: 4
    (0,1):
      - name: CPhase
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
          name: rectangular
  ```

  To change settings with set_parameter methods, use the alias format "GATE(QUBITs)". For example:

  ```python
  platform.set_parameter(alias="X(0)", parameter=Parameter.DURATION, value=40)
  platform.set_parameter(alias="CPhase(0,1)", parameter=Parameter.DURATION, value=80)
  ```

  [#292](https://github.com/qilimanjaro-tech/qililab/pull/292)

- Weighted acquisition is supported. The weight arrays are set as sequencer parameters `weights_i` and `weights_q`, and the weighed acquisition can be enabled setting the sequencer parameter `weighed_acq_enabled` to `true`. Note: the `integration_length` parameter will be ignored if `weighed_acq_enabled` is set to `true`, and the length of the weights arrays will be used instead.

```yaml
awg_sequencers:
  - identifier: 0
    chip_port_id: 1
    intermediate_frequency: 1.e+08
    weights_i: [0.98, ...]  # <-- new line
    weights_q: [0.72, ...]  # <-- new line
    weighed_acq_enabled: true   # <-- new line
    threshold: 0.5              # <-- new line
```

[#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

- `Result`, `Results` and `Acquisitions` classes implement the `counts` method, which returns a dictionary-like object containing the counts of each measurement based in the discretization of the instrument via the `threshold` sequencer parameter. Alternatively, the `probabilities` method can also be used, which returns a normalized version of the same counts object.

  ```pycon
  >>> counts = result.counts()
  Counts: {'00': 502, '01': 23, '10': 19, '11': 480}
  >>> probabilities = result.probabilities()
  Probabilities: {'00': 0.49023438, '01': 0.02246094, '10': 0.01855469, '11': 0.46875}
  ```

  [#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

### Improvements

- Return an integer (instead of the `Port` class) when calling `Chip.get_port`. This is to avoid using the private
  `id_` attribute of the `Port` class to obtain the port index.
  [#189](https://github.com/qilimanjaro-tech/qililab/pull/189)

- The asynchronous data handling used to save results and send data to the live plotting has been improved. Now we are
  saving the results in a queue, and there is only ONE thread which retrieves the results from the queue, sends them to
  the live plotting and saves them to a file.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

- The asynchronous data handling used to save results and send data to the live plotting has been improved.
  Previously we only had ONE active thread retrieving the results and saving them but was created and killed after processing one result of the total `Results` object. Now we are creating the thread just ONCE, so threading is handled at the `Experiment` level instead of what was done previously at the `Exution_Manager` level.
  [#298](https://github.com/qilimanjaro-tech/qililab/pull/298)

### Breaking changes

- `draw()` method of `Circuit` uses Graphviz internally. To be able to call the method Graphviz must be installed. In Ubuntu-based distros a simple `sudo apt-get install graphviz` is sufficient. For detailed installation information for your OS please consult Graphviz's [installation page](https://graphviz.org/download/).
  [#175](https://github.com/qilimanjaro-tech/qililab/issues/175)

- `gates` property of runcard must be updated to provide a list of gate settings for each qubit individually.
  [#292](https://github.com/qilimanjaro-tech/qililab/pull/292)

### Deprecations / Removals

- The `Execution` class has been removed. Its functionality is now added to the `ExecutionManager` class.
  Please use `ExecutionManager`instead. The `ExecutionBuilder` returns now an instance of `ExecutionManager`.
  [#246](https://github.com/qilimanjaro-tech/qililab/pull/246)

- The `LoopOptions` class has been removed. It was used to create a numpy array and store this array in the `values`
  attribute which is now in the `Loop` class.
  [#254](https://github.com/qilimanjaro-tech/qililab/pull/254)

- The `plot_y_label` argument of the `ExperimentOptions` class has been removed.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

- All the `probabilities` methods that returned a `pandas.DataFrame` return now a `dict[str, float]`. All the methods related to the construction of such dataframes have been removed.
  [#283](https://github.com/qilimanjaro-tech/qililab/pull/283)

### Documentation

### Bug fixes

- Fixed bug where acquisition data was not deleted when compiling the same sequence twice.
  [#264](https://github.com/qilimanjaro-tech/qililab/pull/264)

- Fixed bug where the live plotting created a new plot when using parallel loops.
  [#282](https://github.com/qilimanjaro-tech/qililab/pull/282)

## 0.18.0 (2023-04-11)

### New features since last release

- Added `Experiment.compile` method, which return the compiled experiment for debugging purposes.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

  ```pycon
  >>> sequences = experiment.compile()
  ```

  This method returns a list of dictionaries (one dictionary per circuit executed in the experiment). Each dictionary
  contains the sequences uploaded for each bus:

  ```pycon
  >>> sequences[0]
  {'drive_line_bus': [qpysequence_1], 'feedline_input_output_bus': [qpysequence_2]}
  ```

  This experiment is using two buses (`drive_line_bus` and `feedling_input_output_bus`), which have a list of the uploaded sequences
  (in this case only 1).

  We can then obtain the program of such sequences:

  ```pycon
  >>> sequences[0]["drive_line_bus"][0]._program
  setup:
    move             1000, R0
    wait_sync        4
  average:
    reset_ph
    play             0, 1, 4
    long_wait_1:
        move             3, R1
        long_wait_1_loop:
            wait             65532
            loop             R1, @long_wait_1_loop
        wait             3400

    loop             R0, @average
  stop:
    stop
  ```

- Added support for setting output offsets of a qblox module.
  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

- Added gate to native gate transpiler. Contains method `translate_circuit` which translates a qibo.Circuit to a qibo.Circuit with
  native gates (Drag pulses, C-phase), virtual Zs and measurement gates only.
  [#244](https://github.com/qilimanjaro-tech/qililab/pull/244)

- Added optimizer for the native gate transpiler. Shifts all Z, RZ gates to the left and removes them before measurement.
  [#269](https://github.com/qilimanjaro-tech/qililab/pull/269)

### Improvements

- Added support for the execution of pulses with durations that are not multiples of 4. For this, a new
  `minimum_clock_time` attribute has been added to the runcard:

  ```yaml
  settings:
    id_: 0
    category: platform
    name: spectro_v_flux
    device_id: 9
    minimum_clock_time: 4  # <-- new line!
  ```

  When a pulse has a duration that is not a multiple of the `minimum_clock_time`, a padding of 0s is added after the pulse to make sure the next pulse falls within a multiple of 4.
  [#227](https://github.com/qilimanjaro-tech/qililab/pull/227)

- Change name `PulseScheduledBus` to `BusExecution`.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

- Separate `generate_program_and_upload` into two methods: `compile` and `upload`. From now on, when executing a
  single circuit, all the pulses of each bus will be compiled first, and then uploaded to the instruments.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

- Make `nshots` and `repetition_duration` dynamic attributes of the `QbloxModule` class. When any of these two settings
  changes, the cache is emptied to make sure new programs are compiled.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

- Added methods to `PulseBusSchedule` for multiplexing: [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)

  - `frequencies()` returns a list of the frequencies in the schedule.
  - `with_frequency(frequency: float)` returns a new `PulseBusSchedule` containing only those events at that frequency.

- `Pulse`, `PulseEvent`, `PulseShapes` and child classes are now immutable.
  [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)

### Breaking changes

- An `out_offsets` attribute has been added to the settings of a `QbloxModule` object. This attribute contains a list
  of the offsets applied to each output. The runcard should be updated to contain this new information:

  ```yaml
  instruments:
    - name: QRM
    alias: QRM
    id_: 1
    category: awg
    firmware: 0.7.0
    num_sequencers: 1
    acquisition_delay_time: 100
    out_offsets: [0.3, 0, 0, 0]  # <-- this new line needs to be added to the runcard!
    awg_sequencers:
      ...
  ```

  [#199](https://github.com/qilimanjaro-tech/qililab/pull/199)

### Deprecations / Removals

- Removed the `AWG.frequency` attribute because it was not used.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)
- Removed `ReadoutPulse` and `ReadoutEvent`. `Pulse` and `PulseEvent` have to be used instead.
  [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)
- Removed `add(Pulse)` method from `PulseBusSchedule` and `PulseSchedule`. `add_event(PulseEvent)` has to be used instead.
  [#236](https://github.com/qilimanjaro-tech/qililab/pull/236)

### Bug fixes

- Fixed a bug in `PulseBusSchedule.waveforms` where the pulse time was recorded twice.
  [#227](https://github.com/qilimanjaro-tech/qililab/pull/227)

- Fixed bug where the `QbloxModule` uploaded the same sequence to all the sequencers.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

## 0.17.0 (2023-03-27)

### New features since last release

- Added new ChangeLog!
  [#170](https://github.com/qilimanjaro-tech/qililab/pull/170)

- Added rf_on property to SignalGenerator
  [#186](https://github.com/qilimanjaro-tech/qililab/pull/186)

### Improvements

- Cast `chip` dictionary into the `ChipSchema` class and remove unused `InstrumentControllerSchema` class.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

- Upload sequence directly to Qblox instruments, without having to save & load a `json` file.
  [#197](https://github.com/qilimanjaro-tech/qililab/pull/197)

- Changed `schedule_index_to_load` argument to `idx` for more readability.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Refactored the `Experiment` class, creating a method for each step of the workflow. The `Experiment.execute` method will run all these methods in order:
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

  - `connect`: Connect to the instruments and block the device.
  - `initial_setup`: Apply runcard settings to the instruments.
  - `build_execution`:
    - Translate the circuit into pulses.
    - Create the `Execution` class (which contains all the buses with the pulses to execute).
    - Initialize the live plotting.
    - Create the `Results` class and the `results.yml` file (where the results will be stored).
  - `turn_on_instruments`: Turn on the instruments (if necessary).
  - `run`: Iterate over all the loop values, and for each step:
    - Generate the program.
    - Upload the program.
    - Execute the program.
    - Save the result to the `results.yml` file.
    - Send data to live plotting.
    - Save the result to the `Experiment.results` attribute.
  - `turn_off_instruments`: Turn off the instruments (if necessary).
  - `disconnect`: Disconnect from the platform and release the device.
  - `remote_save_experiment`: If `remote_save = True`, save the experiment and the results to the database.

- When translating a Circuit into pulses, the target qubit/resonator frequency is now used to initialize the
  corresponding pulse.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/209)

### Breaking changes

- Removed context manager from `Execution` class. Users will be responsible for turning off and disconnecting the
  instruments when not using the `execute` method directly!
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed the `ExecutionOptions` class. Now the user can freely choose which steps of the workflow to execute.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed the `Platform.connect_and_initial_setup` method.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Move `connection` and `device_id` information into the `Platform` class. Now users should add `device_id` inside
  the runcard and add a `connection` argument when calling `build_platform`:
  [#211](https://github.com/qilimanjaro-tech/qililab/pull/211)

  ```python
  platform = build_platform(name=runcard_name, connection=connection)
  platform.connect(manual_override=False)
  ```

- Removed the frequency argument from the `Pulse.modulated_waveforms` method (and all the methods that uses this method
  internally). Remove `frequency` property from certain buses.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/209)

- The `Pulse.frequency` argument is now mandatory to initialize a pulse.
  [#209](https://github.com/qilimanjaro-tech/qililab/pull/209)

### Deprecations / Removals

- Removed the `ExecutionPreparation` class and the `results_data_management.py` file, and replace it with a
  `prepare_results` method inside the `Experiment` class.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed unused `connect`, `disconnect` and `setup` methods from the `Execution` class. These are used in the
  `Experiment` class, which call the corresponding methods of the `Platform` class.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed the `RemoteAPI` class. This class didn't add any functionality.
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

- Removed all the `Bus` and `SystemControl` types. Now there is only a generic `Bus`, that can contain a
  `SystemControl`, `ReadoutSystemControl` (which contain a list of instruments to control) or `SimulatedSystemControl`,
  which is used to control simulated quantum systems.
  [#210](https://github.com/qilimanjaro-tech/qililab/pull/210)

### Bug fixes

- Fixed wrong timing calculation in Q1ASM generation
  [#186](https://github.com/qilimanjaro-tech/qililab/pull/186)

- Fix bug where calling `set_parameter` with `Parameter.DRAG_COEFFICIENT` would raise an error.
  [#187](https://github.com/qilimanjaro-tech/qililab/pull/187)

- The `qibo` version has been downgraded to `0.1.10` to allow installation on Mac laptops.
  [#185](https://github.com/qilimanjaro-tech/qililab/pull/185)

- Fixed the `Platform.get_element` method:
  [#192](https://github.com/qilimanjaro-tech/qililab/pull/192)

  - Now calling `get_element` of a gate returns a `GateSettings` instance, instead of a `PlatformSettings` instance.
  - Add try/except over the `chip.get_node_from_alias` method to avoid getting an error if the node doesn't exist.

## 0.16.1 (2023-02-24)

### Fix

- Platform should be stateful for connections (#143)

## 0.16.0 (2023-02-07)

### Feat

- updates to Qibo v0.1.11, fixes breaking changes (#139)

## 0.15.1 (2023-01-26)

### Fix

- Duplicate hardware_average property & bus.run() in parallel error (#136)

## 0.15.0 (2023-01-24)

### Feat

- Experimentally validated & debugged Spectroscopy (#134)

## 0.14.0 (2023-01-17)

### Feat

- **Experiment**: added remote experiment saving (#112)

## 0.13.0 (2023-01-17)

### Feat

- **enums**: transform them to string enums (#125)

### Fix

- remove hardcoded modulation from Pulse (#127)

## 0.12.0 (2023-01-17)

### Feat

- Update qblox and qpysequence

## 0.11.0 (2023-01-12)

### Feat

- custom exceptions

## 0.10.3 (2022-12-21)

### Fix

- **Results**: fixed no-results dataframe generation (#109)

## 0.10.2 (2022-12-14)

### Refactor

- [qili-243] sequence class (#104)

## 0.10.1 (2022-12-14)

### Fix

- negative-wait (#106)

## 0.10.0 (2022-12-13)

### Feat

- [QILI-201] multibus support (#101)

## 0.9.2 (2022-11-17)

### Fix

- remove master drag coefficient (#98)

## 0.9.1 (2022-11-17)

### Refactor

- pulse events (#93)

## 0.9.0 (2022-10-06)

### Feat

- qilisimulator integration (#79)

## 0.8.0 (2022-10-05)

### Feat

- qilisimulator integration (#77)

## 0.7.3 (2022-10-03)

### Fix

- [QILI-169] load 2D results (#69)

## 0.7.2 (2022-08-22)

### Fix

- [QILI-187 ] :bug: loops minimum length taking the passed value instead of the self (#57)

## 0.7.1 (2022-08-19)

### Refactor

- [QILI-186] :recycle: renamed beta to drag_coefficient (#56)

## 0.7.0 (2022-08-19)

### Feat

- [QILI-185] add option to NOT reset an instrument (#54)

## 0.6.0 (2022-08-18)

### Feat

- [QILI-184] :sparkles: New daily directory generated for results data (#50)

## 0.5.9 (2022-08-18)

### Fix

- [QILI-183] :bug: accept float master duration gate (#49)

## 0.5.8 (2022-08-18)

### Fix

- [QILI-182] :bug: uses deepcopy before pop dict key (#48)

## 0.5.7 (2022-08-17)

### Fix

- set beta serialization correctly (#47)

## 0.5.6 (2022-08-17)

### Fix

- reference clock after reset and using only the necessary sequencers

## 0.5.5 (2022-07-27)

### Fix

- **setup**: versioning

## 0.5.4 (2022-07-26)

### Fix

- [QILI-181] :bug: fixed values types when they are numpy (#38)

## 0.5.3 (2022-07-26)

### Fix

- [QILI-178] set beta master (#37)

## 0.5.2 (2022-07-26)

### Fix

- [QILI-180] :bug: check for multiple loops correctly (#36)

## 0.5.1 (2022-07-25)

### Fix

- [QILI-177] :bug: make sure amplitude and duration are float or int (#35)

## 0.5.0 (2022-07-24)

### Feat

- [QILI-174] loop support multiple parameters (#34)

## 0.4.2 (2022-07-23)

### Fix

- [QILI-176] set master value for gate amplitude and duration (#33)

## 0.4.1 (2022-07-23)

### Fix

- [QILI-168] Set voltage normalization (#32)

## 0.4.0 (2022-07-20)

### Feat

- New features from TII trip (#31)

## 0.3.0 (2022-04-26)

### Feat

- [QILI-81] Implement schema class (#5)

## 0.2.0 (2022-04-19)

### Feat

- [QILI-46] Implement instrument classes (#9)

## 0.1.0 (2022-04-06)

### Feat

- [QILI-48] Implement platform, backend and settings classes (#8)

## 0.0.0 (2022-03-28)
