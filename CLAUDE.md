# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Qililab is a quantum control library for characterization and calibration of quantum chips. It provides hardware-agnostic pulse-level programming, multi-vendor instrument support (Qblox, QDevil QDAC, Quantum Machines), and high-level circuit execution via Qibo integration.

## Development Commands

**Install dependencies:**
```bash
uv sync --group dev --all-extras
```

**Run all tests (parallel):**
```bash
uv run pytest -n auto --dist loadfile tests
```

**Run a single test file:**
```bash
uv run pytest tests/path/to/test_file.py
```

**Run a single test:**
```bash
uv run pytest tests/path/to/test_file.py::TestClass::test_method
```

**Run tests with coverage:**
```bash
uv run pytest -n auto --dist loadfile --cov=qililab --cov-report=xml tests
```

**Linting and formatting:**
```bash
uv run ruff check .              # lint
uv run ruff check --fix .        # lint with auto-fix
uv run ruff format .             # format
uv run mypy src --ignore-missing-imports  # type check
uv run mdformat .                # markdown formatting
```

## Code Quality

- Ruff config: line-length 120, target Python 3.13, Google-style docstrings
- Commit messages must follow Commitizen conventional commits (enforced by pre-commit hook)
- Test files (`test_*.py`) and `data.py` are excluded from ruff linting
- Tests use the `qm` marker for Quantum Machines-specific tests

## Architecture

### Execution Flow

```
Qibo Circuit → CircuitTranspiler → QProgram → Compiler → Hardware Sequences → Results
```

### Key Layers

**Platform** (`platform/`) - Central orchestrator. Loads configuration from a YAML runcard, manages instruments + buses (control/readout lines), and routes execution to appropriate compilers. Entry point: `ql.build_platform("runcard.yml")`.

**QProgram** (`qprogram/`) - Hardware-agnostic pulse-level programming. Supports structured control flow (ForLoop, Parallel, Average) via context managers that manage an internal block stack. Operations: Play, Measure, Acquire, SetFrequency, SetGain, SetPhase, Wait, Sync. `Experiment` extends QProgram with platform parameter sweeps.

**Compilers** (`qprogram/`) - Translate QProgram into vendor-specific sequences:
- `QbloxCompiler` → qpysequence (Qblox hardware)
- `QdacCompiler` → QDAC pulse programs
- `QuantumMachinesCompiler` → QUA scripts (optional extra)

**Instruments** (`instruments/`) - Device abstractions inheriting from `Instrument` base class. Each exposes `get_parameter`/`set_parameter` with channel/output IDs. Connected to the platform via `InstrumentControllers` which manage physical hardware drivers.

**Digital** (`digital/`) - Transpiles Qibo circuits (gates) into pulse schedules using `DigitalCompilationSettings`.

**Analog** (`analog/`) - Handles continuous flux control via `AnnealingProgram` using `AnalogCompilationSettings`.

**Waveforms** (`waveforms/`) - Pulse shape definitions: Square, Gaussian, IQPair, FlatTop, Ramp, Arbitrary, etc.

**Calibration** (`qprogram/calibration.py`) - Stores pre-characterized waveforms, integration weights, reusable blocks, and a `CrosstalkMatrix` for flux crosstalk correction.

**Results** (`result/`) - HDF5-based storage via `ExperimentResults`. Database integration (SQLite ORM) for experiment metadata. Streaming support via `stream_results()`.

**Serialization** (`utils/serialization.py`) - YAML round-trip serialization using `ruamel.yaml`. Classes register via `@yaml.register_class`. Used for runcard loading/saving and platform state persistence.

### Design Patterns

- **Factory pattern**: `InstrumentFactory`, `InstrumentControllerFactory` instantiate components from runcard dicts
- **Settings dataclasses**: All components use `@dataclass` for configuration with `__post_init__` validation
- **Context managers**: QProgram control flow (`with qp.for_loop(...)`, `with qp.parallel()`) manages block stack
- **Decorator validation**: `@check_device_initialized` guards hardware operations

### Domain Variables

QProgram uses typed variables with domains: Scalar, Time (ns), Frequency (Hz), Phase (rad), Voltage (V), Flux (flux quanta). These enable parametric experiments with compile-time type checking.

### Source Layout

- Source: `src/qililab/`
- Tests: `tests/` (mirrors source structure)
- Runcard examples: `tests/runcards/`
