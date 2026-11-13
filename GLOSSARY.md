# qililab

The quantum-control library at the base of Qilimanjaro's quantum-control stack. Terms shared across the company are in the [shared glossary](https://github.com/qilimanjaro-tech/claude-skills/blob/main/onboarding/qilimanjaro-agent-starter-kit/org-context/qilimanjaro-glossary.md); this file holds qililab's own terms.

## Language

<!-- Seed this in a team grill-with-docs session. Each entry below is taken from the class docstrings; the session adds the _Avoid_ lists. -->

### Platform

**Platform**:
The laboratory setup used to control a quantum device: its buses, instruments and instrument controllers, built from a runcard with `ql.build_platform` (`src/qililab/platform/platform.py`).

**Runcard**:
The serialized platform: a YAML file or dictionary listing the instruments, instrument controllers and buses (`src/qililab/settings/runcard.py`).

**Bus**:
A named line of the platform, identified by its alias, that groups the instruments and channels driving or reading one target, with its own delay in ns (`src/qililab/platform/components/bus.py`).

**Instrument controller**:
The object that owns the driver and connection of a physical device and the instruments (modules) it hosts (`src/qililab/instrument_controllers/instrument_controller.py`).

### Programs

**QProgram**:
A hardware-agnostic, pulse-level description of a quantum program, compiled per bus into instrument programs (`src/qililab/qprogram/qprogram.py`).

**Experiment**:
A structured program that sets platform parameters and executes QPrograms (`src/qililab/qprogram/experiment.py`).

**Domain**:
The physical quantity a QProgram variable stands for: Scalar, Time, Frequency, Phase, Voltage or Flux. Time variables are integers; the others are floats (`src/qililab/core/variables.py`).

**Calibration**:
The stored calibration data a QProgram can reuse: named waveforms, integration weights, blocks and the crosstalk matrices (`src/qililab/qprogram/calibration.py`).

**Crosstalk matrix**:
A matrix indexed by bus that describes how flux applied on one bus reaches the others, used to compensate flux crosstalk (`src/qililab/qprogram/crosstalk_matrix.py`).
