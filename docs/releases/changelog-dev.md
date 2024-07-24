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

- Added `from_qprogram` method to compute the counts of the quantum states obtained with `QProgram`. The `Counts` object is expected to work for circuits which has only a measurement per bus at the end of the eexcution of the circuit so is responsability of the user when it makes sense to compute the probabilities of the states or not of a `QProgram`.

  Example:

  ```Python
  from qililab.result.counts import Counts

  qp = QProgram()
  # Define instructions for QProgram
  # ...
  qp_results = platform.execute_qprogram(qp)  # Platform previously defined
  counts_object = Counts.from_qprogram(qp_results)
  probs = counts_object.probabilities()
  ```

  [#743](https://github.com/qilimanjaro-tech/qililab/pull/743)

### Improvements

- Improved the algorithm determining which markers should be ON during execution of circuits and qprograms. Now, all markers are OFF by default, and only the markers associated with the `outputs` setting of QCM-RF and QRM-RF sequencers are turned on.

  [#747](https://github.com/qilimanjaro-tech/qililab/pull/747)

### Breaking changes

### Deprecations / Removals

- Deleted all the files in `execution` and `experiment` directories (Already obsolete).
  [#749](https://github.com/qilimanjaro-tech/qililab/pull/749)

### Documentation

### Bug fixes
