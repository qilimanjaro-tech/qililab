# Release dev (development release)

### New features since last release

- Added `Calibration` class to manage calibrated waveforms and weights for QProgram. Included methods to add (`add_waveform`/`add_weights`), check (`has_waveform`/`has_weights`), retrieve (`get_waveform`/`get_weights`), save (`save_to`), and load (`load_from`) calibration data.

  Example:

  ```Python
  # Create a Calibration instance
  calibration = Calibration()

  # Define waveforms and weights
  drag_wf = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4.5, drag_coefficient=-2.5)
  readout_wf = ql.IQPair(I=ql.Square(amplitude=1.0, duration=200), Q=ql.Square(amplitude=0.0, duration=200))
  weights = ql.IQPair(I=ql.Square(amplitude=1.0, duration=200), Q=ql.Square(amplitude=1.0, duration=200))

  # Add waveforms to the calibration
  calibration.add_waveform(bus='drive_q0_bus', name='Xpi', waveform=drag_wf)
  calibration.add_waveform(bus='readout_q0_bus', name='Measure', waveform=readout_wf)

  # Add weights to the calibration
  calibration.add_weights(bus='readout_q0_bus', name='optimal_weights', weights=weights)

  # Save the calibration data to a file
  calibration.save_to('calibration_data.yml')

  # Load the calibration data from a file
  loaded_calibration = Calibration.load_from('calibration_data.yml')
  ```

  The contents of `calibration_data.yml` will be:

  ```YAML
  !Calibration
  waveforms:
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
  weights:
    readout_q0_bus:
      optimal_weights: !IQPair
        I: !Square {amplitude: 1.0, duration: 200}
        Q: !Square {amplitude: 1.0, duration: 200}
  ```

  Calibrated waveforms and weights can be used in QProgram by providing their name.

  ```Python
  qp = QProgram()
  qp.play(bus='drive_q0_bus', waveform='Xpi')
  qp.measure(bus='readout_q0_bus', waveform='Measure', weights='optimal_weights')
  ```

  In that case, a `Calibration` instance must be provided when executing the QProgram. (see following changelog entries)

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)
  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- Introduced `qililab.yaml` namespace that exports a single `YAML` instance for common use throughout qililab. Classes should be registered to this instance with the `@yaml.register_class` decorator.

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

- Added `serialize()`, `serialize_to()`, `deserialize()`, `deserialize_from()` functions to enable a unified method for serializing and deserializing Qililab classes to and from YAML memory strings and files.

  ```Python
  import qililab as ql

  qp = QProgram()

  # Serialize QProgram to a memory string and deserialize from it.
  yaml_string = ql.serialize(qp)
  deserialized_qprogram = ql.deserialize(yaml_string)

  # Specify the class for deserialization using the `cls` parameter.
  deserialized_qprogram = ql.deserialize(yaml_string, cls=ql.QProgram)

  # Serialize to and deserialize from a file.
  ql.serialize_to(qp, 'qprogram.yml')
  deserialized_qprogram = ql.deserialize_from('qprogram.yml', cls=ql.QProgram)
  ```

  [#737](https://github.com/qilimanjaro-tech/qililab/pull/737)

- Added Qblox support for QProgram's `measure` operation. The method can now be used for both Qblox
  and Quantum Machines, and the expected behaviour is the same.

  ```Python
  readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
  weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
  qp = QProgram()

  # The measure operation has the same behaviour in both vendors.
  # Time of flight between readout pulse and beginning of acquisition is retrieved from the instrument's settings.
  qp.measure(bus="readout_bus", waveform=readout_pair, weights=weights_pair, save_adc=True)
  ```

  [#734](https://github.com/qilimanjaro-tech/qililab/pull/734)
  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)
  [#738](https://github.com/qilimanjaro-tech/qililab/pull/738)

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
  [#740](https://github.com/qilimanjaro-tech/qililab/pull/740)

- Introduced `QProgram.with_calibration` method to apply calibrated waveforms and weights to the QProgram.

  Example:

  ```Python
  # Load the calibration data from a file
  calibration = Calibration.load_from('calibration_data.yml')

  # Apply the calibration to a QProgram instance
  calibrated_qprogram = qprogram.with_calibration(calibration=calibration)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)
  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- Extended `Platform.execute_qprogram` method to accept a calibration instance.

  ```Python
  # Load the calibration data from a file
  calibration = Calibration.load_from('calibration_data.yml')

  platform.execute_qprogram(qprogram=qprogram, calibration=calibration)
  ```

  [#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Added interfaces for Qblox and Quantum Machines to QProgram. The interfaces contain vendor-specific methods and parameters. They can be accessed by `qprogram.qblox` and `qprogram.quantum_machines` properties.

  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- Added `time_of_flight` setting to Qblox QRM and QRM-RF sequencers.

  [#738](https://github.com/qilimanjaro-tech/qililab/pull/738)

### Breaking changes

- QProgram interface now contains methods and parameters that have common functionality for all hardware vendors. Vendor-specific methods and parameters have been move to their respective interface.

  Examples:

  ```Python
  # Acquire method has been moved to Qblox interface. Instead of running
  # qp.acquire(bus="readout_q0_bus", weights=weights)
  # you should run
  qp.qblox.acquire(bus="readout_q0_bus", weights=weights)

  # Play method with `wait_time` parameter has been moved to Qblox interface. Instead of running
  # qp.play(bus="readout_q0_bus", waveform=waveform, wait_time=40)
  # you should run
  qp.qblox.play(bus="readout_q0_bus", waveform=waveform, wait_time=40)

  # `disable_autosync` parameter has been moved to Qblox interface. Instead of running
  # qp = QProgram(disable_autosync=True)
  # you should run
  qp = QProgram()
  qp.qblox.disable_autosync = True

  # Measure method with parameters `rotation` and `demodulation` has been moved to Quantum Machines interface. Instead of running
  # qp.measure(bus="readout_q0_bus", waveform=waveform, weights=weights, save_adc=True, rotation=np.pi, demodulation=True)
  # you should run
  qp.quantum_machines.measure(bus="readout_q0_bus", waveform=waveform, weights=weights, save_adc=True, rotation=np.pi, demodulation=True)
  ```

  [#736](https://github.com/qilimanjaro-tech/qililab/pull/736)

- `time_of_flight` parameter must be added to Qblox QRM and QRM-RF sequencers's runcard settings.

  [#738](https://github.com/qilimanjaro-tech/qililab/pull/738)

### Deprecations / Removals

- Remove the deprecated `path` argument from `build_platform()`.

  [#739](https://github.com/qilimanjaro-tech/qililab/pull/739)

### Documentation

### Bug fixes
