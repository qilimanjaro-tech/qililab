# Release dev (development release)

### New features since last release

### Improvements

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

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fix typo in ExceptionGroup import statement for python 3.11+
  [#808](https://github.com/qilimanjaro-tech/qililab/pull/808)
