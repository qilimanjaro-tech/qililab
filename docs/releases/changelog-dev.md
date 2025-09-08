# Release dev (development release)

### New features since last release

- Updated `qibo` to version 0.2.20, and to fit the requirements `numpy` has been updated to 2.2.6 and `pandas` to 2.2.3.
  [#970](https://github.com/qilimanjaro-tech/qililab/pull/970)

### Improvements

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

- Added measurements databases into the results saving structure all the architecture for them is located inside `results/database.py`. Added functionality for stream array using databases through `platform.database_saving` and through the class `StreaArray`, legacy `stream_array()` function still works as usual for retrocompatibility.
  [#928](https://github.com/qilimanjaro-tech/qililab/pull/928)

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

- Modified smoothed square waveform class `FlatTop(amplitude, duration, smooth_duration, buffer = 0)` which works similar to the `Square` waveform with an additional smoothing on the edges. The only additional parameters are the smoothing duration and the buffer time. In `QbloxCompiler` if the duration exceeds a threshold of 100 ns the pulses are divide into two arbitrary pulses at the beginning and the end for the smooth parts and a loop of square pulses in the middle, with the exact same behavior as `Square` pulses.
  [#969](https://github.com/qilimanjaro-tech/qililab/pull/969)

- Modified `StreamArray` to work with live plot. Now the H5 file has the `swmr_mode` set as true allowing for live reading and `StreamArray`'s `__enter__` and `__setitem__` have `file.flush()` to update the H5 live. Moved `create_dataset` to `__enter__` instead of `__setitem__` to allow for live plot while acounting for VNA results with different data structure. Modified the `experiment_completed` to set as `True` after the execution, now in case of a crash the experiment will not be set as Completed.
  [#966](https://github.com/qilimanjaro-tech/qililab/pull/966)
  [#976](https://github.com/qilimanjaro-tech/qililab/pull/976)

- Modified the `experiment_completed` to set as `True` after the execution, now in case of a crash the experiment will not be set as Completed.
  [#972](https://github.com/qilimanjaro-tech/qililab/pull/972)

- Added new functions to DatabaseManager to support more efficient loading of data for live-plotting application. Such as get_platform and get_qprogram.
  [#979](https://github.com/qilimanjaro-tech/qililab/pull/979)

### Breaking changes

- Modified file structure for functions `save_results` and `load_results`, previously located inside `qililab/src/qililab/data_management.py` and now located at `qililab/src/qililab/result/result_management.py`. This has been done to improve the logic behind our libraries. The init structure still works in the same way, import `qililab.save_results` and import `qililab.load_results` still works the same way.
  [#928](https://github.com/qilimanjaro-tech/qililab/pull/928)

### Deprecations / Removals

### Documentation

### Bug fixes

- Qblox Draw: Previously, when plotting from the platform, the integration length was incorrectly taken from the runcard parameter. However, since Qililab currently only implements acquire_weighted, the integration length should instead be determined by the duration of the weight.
This has been corrected and now the behaviour of the acquire is the same when plotting from the platform or the qprogram.
The integration length is defined as the duration of the acquire, not the weight, because Qililab ensures they are always equal. As a result, two acquires cannot overlap in Qililab. However, in QbloxDraw’s logic, interruptions remain possible, similar to Play.
  [#982](https://github.com/qilimanjaro-tech/qililab/pull/982)

- Removed the unsupported zorder kwarg from QbloxDraw plotting to prevent Plotly errors across environments.
  [#974](https://github.com/qilimanjaro-tech/qililab/pull/974)

- A bug on the tests of Qblox Draw has been fixed. Previously, the test compared `figure.data` using the position of items in the list. Since the order of items can change, this caused inconsistent results. The test now compares the data based on the bus name.
  [#965](https://github.com/qilimanjaro-tech/qililab/pull/965)

- For Qblox Draw, the move commands  of the Q1ASM were being read correctly once but were not being updated after - this caused problem with loops.

- A 4ns has been added when an acquire_weighed command is added to account for the extra clock cycle
  [#933](https://github.com/qilimanjaro-tech/qililab/pull/933)

- Qblox Draw: Corrected bug with time window and nested loops- now after the code exits the recursive loop, the code checks the time window flag status and exits if needed.
  [#937](https://github.com/qilimanjaro-tech/qililab/pull/937)

- VNA Driver Keysight E5080B:

  - The user can now set through the platform the parameters of type Enums, the enums were not being capitalised. - The bounds in the frequency span of the qcodes type driver have been removed as they were wrong.
  - The bounds of the points in the qcodes type driver have been modified to range from 1 to 100003.
    [#943](https://github.com/qilimanjaro-tech/qililab/pull/943)

- QbloxDraw:

  - The sequencer offsets given from the runcard (offset_i and offset_q in the runcard) were being applied similarly to the DAC offsets, when they should have been treated like the Q1ASM offsets - this has been fixed and those sequencer offsets havee been renamed sequencer_runcard_offset_i and  sequencer_runcard_offset_q instead of ac_offsets_i and ac_offsets_q for improved clarity.
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
