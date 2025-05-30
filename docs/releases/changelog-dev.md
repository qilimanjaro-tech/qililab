# Release dev (development release)

### New features since last release

### Improvements

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
- The sims file used to test the qcode like driver file has been moved to a similar location as qcodes (\qililab\src\qililab\instruments\sims).
[#943](https://github.com/qilimanjaro-tech/qililab/pull/943)

- Modified Streamarray to allow for np.complexfloat values following VNA results. This process has been automatized and requires no input from the user.
[#941](https://github.com/qilimanjaro-tech/qililab/pull/941)


### Breaking changes

- Modified file structure for functions `save_results` and `load_results`, previously located inside `qililab/src/qililab/data_management.py` and now located at `qililab/src/qililab/result/result_management.py`. This has been done to improve the logic behind our libraries. The init structure still works in the same way, import `qililab.save_results` and import `qililab.load_results` still works the same way.
[#928](https://github.com/qilimanjaro-tech/qililab/pull/928)

### Deprecations / Removals

### Documentation

### Bug fixes

- For Qblox Draw, the move commands  of the Q1ASM were being read correctly once but were not being updated after - this caused problem with loops.
- A 4ns has been added when an acquire_weighed command is added to account for the extra clock cycle
[#933](https://github.com/qilimanjaro-tech/qililab/pull/933)

- Qblox Draw: Corrected bug with time window and nested loops- now after the code exits the recursive loop, the code checks the time window flag status and exits if needed.
[#937](https://github.com/qilimanjaro-tech/qililab/pull/937)

- VNA Driver Keysight E5080B:
    - The user can now set through the platform the parameters of type Enums, the enums were not being capitalised. - The bounds in the frequency span of the qcodes type driver have been removed as they were wrong.
    - The bounds of the points in the qcodes type driver have been modified to range from 1 to 100003.
[#943](https://github.com/qilimanjaro-tech/qililab/pull/943)

