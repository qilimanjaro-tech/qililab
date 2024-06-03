# Release dev (development release)

### New features since last release

- Added `Calibration` class to manage calibrated operations for QProgram, including methods to add (`add_operation`), check (`has_operation`), retrieve (`get_operation`), save (`dump`), and load (`load`) calibration data.

  Example:

  ```Python
  # Create a Calibration instance
  calibration = Calibration()

  # Define waveforms
  drag_wf = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4.5, drag_coefficient=-2.5)
  readout_wf = ql.IQPair(I=ql.Square(amplitude=1.0, duration=200), Q=ql.Square(amplitude=0.0, duration=200))

  # Add waveforms to the calibration as named operations
  calibration.add_operation(bus='drive_q0_bus', operation='Xpi', waveform=drag_wf)
  calibration.add_operation(bus='readout_q0_bus', operation='Measure', waveform=readout_wf)

  # Save the calibration data to a file
  calibration.dump('calibration_data.yml')

  # Load the calibration data from a file
  loaded_calibration = Calibration.load('calibration_data.yml')
  ```

  The contents of `calibration_data.yml` will be:

  ```YAML
  !Calibration
  operations:
  drive_q0_bus:
      Xpi: !IQPair
      I: &id001 !Gaussian {amplitude: 1.0, duration: 40, num_sigmas: 4.5}
      Q: !DragCorrection
          drag_coefficient: -2.5
          waveform: *id001
  readout_q0_bus:
      Measure: !IQPair
      I: !Square {amplitude: 1.0, duration: 200}
      Q: !Square {amplitude: 0.0, duration: 200}
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Introduced `qililab.yaml` namespace that exports a single `YAML` instance for common use throughout qililab. Classes can be registered to this instance with the `@yaml.register_class` decorator.

  ```Python
  from qililab.yaml import yaml

  @yaml.register_class
  class MyClass:
      ...
  ```

  `MyClass` can now be saved to and loaded from a yaml file.

  ```Python
  from qililab.yaml import yaml

  my_instance = MyClass()

  # Save to file
  with open(file="my_file.yml", mode="w", encoding="utf-8") as stream:
      yaml.dump(data=my_instance, stream=stream)

  # Load from file
  with open(file="my_file.yml", mode="r", encoding="utf8") as stream:
      loaded_instance = yaml.load(stream)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Add qblox support for `qprogram.measure`. Now this method can be use for both Qblox Instruments
  and Quantum Machines. In the near future the `qprogram.acquire` method will be removed.
  [#734](https://github.com/qilimanjaro-tech/qililab/pull/734)

### Improvements

- Introduced `QProgram.with_bus_mapping` method to remap buses within the QProgram.

  Example:

  ```Python
  # Define the bus mapping
  bus_mapping = {"drive": "drive_q0"}

  # Apply the bus mapping to a QProgram instance
  mapped_qprogram = qprogram.with_bus_mapping(bus_mapping=bus_mapping)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Introduced `QProgram.with_calibration` method to apply calibration to operations within the QProgram.

  Example:

  ```Python
  # Load the calibration data from a file
  calibration = Calibration.load('calibration_data.yml')

  # Apply the calibration to a QProgram instance
  calibrated_qprogram = qprogram.with_calibration(calibration=calibration)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Extended `Platform.execute_qprogram` method to accept a calibration instance.

  ```Python
  # Load the calibration data from a file
  calibration = Calibration.load('calibration_data.yml')

  platform.execute_qprogram(qprogram=qprogram, calibration=calibration)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
