# Release dev (development release)

### New features since last release

- Added the Qblox-specific `set_markers()` method in `QProgram`. This method takes a 4-bit binary mask as input, where `0` means that the associated marker will be open (no signal) and `1` means that the associated marker will be closed (signal). The mapping between bit indexes and markers depends on the Qblox module that the compiled `QProgram` will run on.

  Example:

  ```Python
  qp = QProgram()
  qp.qblox.set_markers(bus='drive_q0', mask='0111')
  ```

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `set_markers_override_enabled_by_port` and `set_markers_override_value_by_port` methods in `QbloxModule` to set markers through QCoDeS, overriding Q1ASM values.

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added `threshold_rotations` argument to `compile()` method in `QProgram`. This argument allows to use rotation angles on measurement instructions if not specified. Currently used to use the angle rotations specified on the runcard (if any) so the user does not have to explicitly pass it as argument to the measure instruction.  Used for classification of results in Quantum Machines's modules. The following example shows how to specify this value on the runcard.

  Example:

  ```JSON
  buses:
  - alias: readout_q0_bus
    system_control:
      name: readout_system_control
      instruments: [QMM]
    port: readout_line_q0
    distortions: []
  ...
  instruments:
    - name: quantum_machines_cluster
      alias: QMM
      firmware: ...
      ...
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
      ...
  ```

  [#759](https://github.com/qilimanjaro-tech/qililab/pull/759)

- Added loopbacks in the octave config file for qua following the documentation at https://docs.quantum-machines.co/1.2.0/qm-qua-sdk/docs/Guides/octave/?h=octaves#setting-the-octaves-clock. By default only port 1 of the octave is linked with a local demodulator, to work with the rest of the ports at the back ports must be connected based on the Octave Block Diagram [https://docs.quantum-machines.co/1.2.0/qm-qua-sdk/docs/Hardware/octave/#octave-block-diagram]. Where `Synth` is one of the possible 3 synths and `Dmd` is one of the 2 demodulators.

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
### Improvements

- Now platform.get_parameter works for QM without the need of connecting to the machine.

- Added the option to get the time of flight and smearing information from the QM cluster
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

### Breaking changes

### Deprecations / Removals

- Deleted all the files in `execution` and `experiment` directories (Already obsolete).
  [#749](https://github.com/qilimanjaro-tech/qililab/pull/749)

### Documentation

### Bug fixes

- get_parameter for QM did not work due to the lack of the variable `bus_alias in self.system_control.get_parameter`. The variable has been added to the function and now get parameter does not return a crash.
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)
