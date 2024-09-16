# Release dev (development release)

### New features since last release

### Improvements

- Improve Crosstalk matrix `from_buses` method so it can be a dictionary of buses and crosstalks coefficients.
  \[#784\]https://github.com/qilimanjaro-tech/qililab/pull/784

- Now platform.get_parameter works for QM without the need of connecting to the machine.

- Added the option to get the time of flight and smearing information from the QM cluster
  [#751](https://github.com/qilimanjaro-tech/qililab/pull/751)

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.
  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

- Added pulse distorsions in `execute_qprogram` for QBlox in a similar methodology to the distorsions implemented in pulse circuits. The runcard needs to contain the same structure for distorsions as the runcards for circuits and the code will modify the waveforms after compilation (inside `platform.execute_qprogram`).

  Example (for Qblox)
  
  ```
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

- Automatic method to implement the correct `upsampling_mode` when the output mode is selected as `amplified` (fluxes), the `upsampling_mode` is automatically defined as `pulse`. In this mode, the upsampling is optimized to produce cleaner step responses.
  [#783](https://github.com/qilimanjaro-tech/qililab/pull/783)

- Automatic method for `execute_qprogram` in quantum machines to restart the measurement in case the `StreamProcessingDataLossError` is risen by `qua-qm`, the new feature allows to try again the measurement a number of times equal to the value of `dataloss_tries` (default of three). We can define this value at `execute_qprogram(..., dataloss_tries = N)` and will only do its intended job in case of working with QM.
  [#788](https://github.com/qilimanjaro-tech/qililab/pull/788)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
