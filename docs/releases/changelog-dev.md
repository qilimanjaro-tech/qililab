# Release dev (development release)

### New features since last release

- QBlox: An oscilloscope simulator has been implemented. It takes the sequencer as input, plots its waveforms and returns a dictionary (data_draw) containing all data points used for plotting.

The user can access the Qblox drawing feature in two ways:
  1. Via platform (includes runcard knowledge)
  `platform.draw(self, qprogram: QProgram, averages_displayed: bool = False)`
  ```python
  with platform.session():
    platform.draw(qprogram = qprogram)
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

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
