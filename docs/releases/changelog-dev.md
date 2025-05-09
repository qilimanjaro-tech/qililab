# Release dev (development release)

### New features since last release

### Improvements
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

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
- For Qblox Draw, the move commands  of the Q1ASM were being read correctly once but were not being updated after - this caused problem with loops.
- A 4ns has been added when an acquire_weighed command is added to account for the extra clock cycle
[#933](https://github.com/qilimanjaro-tech/qililab/pull/933)

- Qblox Draw: Corrected bug with time window and nested loops- now after the code exits the recursive loop, the code checks the time window flag status and exits if needed.
[#937](https://github.com/qilimanjaro-tech/qililab/pull/937)