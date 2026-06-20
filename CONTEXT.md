# Qililab

Quantum control library that wraps QCodes instrument drivers, adding experiment-level parameter management, validation, and pulse/circuit execution on real hardware.

## Language

### Instrument layer

**Instrument**:
A Qililab wrapper around a QCodes driver. Owns the settings loaded from the Runcard, exposes Channels and BoundParameters, and forwards hardware calls to the underlying QCodes device.
_Avoid_: driver, device (reserve "device" for the raw QCodes object inside an Instrument)

**Channel**:
A first-class object representing one addressable output of a multi-channel Instrument (e.g. one DAC on a QDAC-II). Accessed as a zero-padded attribute: `qdac.ch01`. Holds the BoundParameters for that output and the limits that govern them.
_Avoid_: channel_id (that is an integer identifier, not the Channel object)

**BoundParameter**:
A callable object attached to an Instrument or Channel that wraps the corresponding QCodes Parameter. Calling it with a value sets the parameter (`ch01.voltage(0.5)`); calling it with no argument reads the current value (`ch01.voltage()`). Owns the Active Limits and enforces them before delegating to the QCodes layer.
_Avoid_: Parameter (that is the QCodes class), ParameterName (that is the Qililab enum)

**ParameterName**:
An enum that identifies a parameter by name (e.g. `ParameterName.VOLTAGE`, `ParameterName.FREQUENCY`). Used internally by `set_parameter` / `get_parameter` shims. Not a value-holder — just a name token.
_Avoid_: Parameter (ambiguous with the QCodes callable class and BoundParameter)

### Limits

**Hardware Limits**:
The physical bounds of an instrument parameter, hardcoded as class constants on the Instrument (e.g. `_VOLTAGE_HW_MIN`). Represent what the hardware can do. Never configurable at runtime.
_Avoid_: device limits, QCodes limits

**Runcard Limits**:
The per-channel min/max bounds declared in the runcard YAML for a BoundParameter. Must be within Hardware Limits — validated by Pydantic at load time. Stored immutably on the BoundParameter; never mutated at runtime.
_Avoid_: configured limits, default limits

**Active Limits**:
The limits currently enforced by a BoundParameter at call time. Start equal to the Runcard Limits. Can be tightened (but never widened past Runcard Limits) via `set_limits()`; restored to Runcard Limits via `reset_limits()`.
_Avoid_: current limits, session limits

### Config

**Runcard**:
The YAML configuration file that defines a Platform: its instruments, chip topology, and native gates. The source of truth for Runcard Limits and initial parameter values.
_Avoid_: config file, settings file, YAML

**Platform**:
The central object representing a quantum laboratory setup. Owns Instruments, the chip description, and native gate definitions. The entry point for circuit and QProgram execution.
_Avoid_: lab, setup, system
