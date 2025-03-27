# Release dev (development release)

### New features since last release

- QBlox: An oscilloscope simulator has been implemented. It takes the sequencer as input, plots its waveforms and returns a dictionary (data_draw) containing all data points used for plotting.

The user can access the Qblox drawing feature in two ways:

1. Via platform (includes runcard knowledge)
   `platform.draw(self, qprogram: QProgram, averages_displayed: bool = False)`

```python
with platform.session():
    platform.draw(qprogram=qprogram)
```

Note that if it is used with a Quantum Machine runcard, a ValueError will be generated.

2. Via QProgram (includes runcard knowledge)
   `qprogram.draw(self, averages_displayed=False)`

```python
qp = QProgram()
qprogram.draw()
```

Both methods compile the qprogram internally to generate the sequencer and call `QbloxDraw.draw(self, sequencer, runcard_data=None, averages_displayed=False) -> dict`.
Aditionally both

[#899](https://github.com/qilimanjaro-tech/qililab/pull/899)

### Improvements

- Now the Rohde & Schwarz will return an error after a limit of frequency or power is reached based on the machine's version.
  [#897](https://github.com/qilimanjaro-tech/qililab/pull/897)

- QBlox: Added support for executing multiple QProgram instances in parallel via the new method `platform.execute_qprograms_parallel(qprograms: list[QProgram])`. This method returns a list of `QProgramResults` corresponding to the input order of the provided qprograms. Note that an error will be raised if any submitted qprograms share a common bus.

  ```python
  with platform.session():
      results = platform.execute_qprograms_parallel([qprogram1, qprogram2, qprogram3])
  ```

  [#906](https://github.com/qilimanjaro-tech/qililab/pull/906)

### Breaking changes

### Deprecations / Removals

- Remove the check of forcing GRES in slurm.
  [#907](https://github.com/qilimanjaro-tech/qililab/pull/907)

### Documentation

### Bug fixes

- D5a instrument now does not raise error when the value of the dac is higher or equal than 4, now it raises an error when is higher or equal than 16 (the number of dacs).
  [#908](https://github.com/qilimanjaro-tech/qililab/pull/908)
