# Release dev (development release)

### New features since last release

- Added `Calibration` class to manage calibrated operations for QProgram, including methods to add (`add_operation`), retrieve (`get_operation`), save (`dump`), and load (`load`) calibration data.

Example:

```
# Create a Calibration instance
calibration = Calibration()

# Add operations to the calibration
calibration.add_operation(bus='bus1', operation='op1', waveform=Waveform())
calibration.add_operation(bus='bus2', operation='op2', waveform=IQPair())

# Save the calibration data to a file
calibration.dump('calibration_data.yml')

# Load the calibration data from a file
loaded_calibration = Calibration.load('calibration_data.yml')
```

[#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Introduced `qililab.yaml` namespace that exports a single `YAML` instance for common use throughout qililab. Classes can be registered to this instance with the `@yaml.register_class` decorator.

```
from qililab.yaml import yaml

@yaml.register_class
class MyClass:
    ...
```

`MyClass` can now be saved to and loaded from a yaml file.

```
from qililab.yaml import yaml

my_instance = MyClass()

with open(file="my_file.yml", mode="w", encoding="utf-8") as stream:
    yaml.dump(data=my_instance, stream=stream)

with open(file="my_file.yml", mode="r", encoding="utf8") as stream:
    loaded_instance = yaml.load(stream)
```

[#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

### Improvements

- Introduced `QProgram.with_bus_mapping` method to remap buses within the QProgram.

Example:

```
# Define the bus mapping
bus_mapping = {"drive": "drive_q0"}

# Apply the bus mapping to a QProgram instance
mapped_qprogram = qprogram.with_bus_mapping(bus_mapping=bus_mapping)
```

[#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

- Introduced `QProgram.with_calibration` method to apply calibration to operations within the QProgram.

Example:

```
# Load the calibration data from a file
calibration = Calibration.load('calibration_data.yml')

# Apply the calibration to a QProgram instance
calibrated_qprogram = qprogram.with_calibration(calibration=calibration)
```

[#729](https://github.com/qilimanjaro-tech/qililab/pull/729)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
