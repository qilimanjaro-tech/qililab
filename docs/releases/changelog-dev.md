# Release dev (development release)

### New features since last release

### Improvements

- Implemented a new driver for the Becker Nachrichtentechnik RSWU-SP16TR
[#1020](https://github.com/qilimanjaro-tech/qililab/pull/1020)
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


- This update introduces a new mechanism that allows the library to optionally import either full concrete  implementations or lightweight stubs, depending on the user’s environment and installed dependencies. As part of this improvement, all Quantum Machines–related components have been reorganized under the `extra/quantum-machines` module hierarchy for better modularity and maintainability. Additionally, the Quantum Machines integration has been moved to the `[project.optional-dependencies]` section of the configuration, enabling users to install it only when needed.

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

  2. When instructing an `acquire_weighed` in Q1ASM, the creation of registers has been optimised. New registers for the weights would be created each time, a dictionary `weight_index_to_register` has been introduced in the QBlox Compiler to track previously used values of weight and reuse the register if possible.
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
bus_mapping (ist[dict[str, str] | None] | dict[str, str], optional). It can be one of the following:
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

  - When calling `qprogram.draw()` or  `platform.draw(qprogram)` directly, the figure is displayed.
  - When assigning it to a variable (e.g., `plotly_figure = qprogram.draw()` or  `plotly_figure = platform.draw(qprogram)`), the figure is stored but not automatically shown (since `figure.show()` has been removed from QbloxDraw).

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

### Deprecations / Removals

### Documentation

### Bug fixes
