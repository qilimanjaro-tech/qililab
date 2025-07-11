# Release dev (development release)

### New features since last release

- **Active reset for transmon qubits in QBlox**

  Implemented a feedback-based reset for QBlox: measure the qubit, and if it is in the \|1⟩ state apply a corrective DRAG pulse; if it is already in \|0⟩ (ground state), do nothing. This replaces the commonly used passive 200 000 ns wait at the end of each experiment with a much faster, conditional reset, also improving state-preparation fidelity.
  This has been implemented as **`qprogram.qblox.measure_reset(measure_bus: str, waveform: IQPair, weights: IQPair, control_bus: str, reset_pulse: IQPair, trigger_address: int = 1, save_adc: bool = False)`** 

  It is compiled by the QBlox compiler as:
    1. `latch_rst 4` on the control_bus
    2. play readout pulse 
    3. acquire 
    4. sync the readout and control buses
    5. wait 400 ns on the control bus (trigger-network propagation)
    6. `set_conditional(1, mask, 0, duration of the reset pulse)` → enable the conditional
    7. Play the reset pulse on the control bus
    8. `set_conditional(0, 0, 0, 4)` → disable the conditional  
    For the control bus, `latch_en 4` is added to the top of the Q1ASM to enable trigger latching.

  Notes:
    - The 400 ns wait inside `measure_reset` corresponds to the propagation delay of the Qblox trigger network. This figure is conservative as  the official guideline is 388ns.
    - Users may supply any IQPair for the reset_pulse, though DRAG pulses are recommended to minimize leakage.
    - After `measure_reset`, users should insert a further wait as needed to allow the readout resonator to ring down before subsequent operations.
    - On compilation, `cluster.reset_trigger_monitor_count(address)` is applied to zero the module’s trigger counter. And the qcodes parameters required to set up the trigger network are implemented by the QbloxQRM class.
    - The Qblox Draw class has been modified so that `latch_rst` instructions are interpreted as a `wait`, and all `set_conditional` commands are ignored.
    - Set-conditional and latch-rst commands are also available separately in the qblox interface of qprogram:
      - `qprogram.qblox.latch_rst(bus: str, duration: int)`
      - `qprogram.set_conditional(bus: str, enable: int, mask: int, operator: int, else_duration: int)`

[#955](https://github.com/qilimanjaro-tech/qililab/pull/955)


### Improvements

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
- The sims file used to test the qcode like driver file has been moved to a similar location as qcodes (\qililab\src\qililab\instruments\sims).
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
  - The _handle_play() used to loop through all the waveform indices, now it exits in the loop as soon as I and Q have been found, this is more efficient.
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

- QbloxDraw:
  - The sequencer offsets given from the runcard (offset_i and offset_q in the runcard) were being applied similarly to the DAC offsets, when they should have been treated like the Q1ASM offsets - this has been fixed and those sequencer offsets havee been renamed sequencer_runcard_offset_i and  sequencer_runcard_offset_q instead of ac_offsets_i and ac_offsets_q for improved clarity.
  - get_value() in the QbloxDraw class now checks that the given string is a float, it used to check x.isdigit() which didn't work for negative values.
[#945](https://github.com/qilimanjaro-tech/qililab/pull/945)

- Fixed a bug for `StreamArray` while using dictionary structures for the loops. Now the order is correct and the data is saved in the correct h5 file format.
[#953](https://github.com/qilimanjaro-tech/qililab/pull/953)
