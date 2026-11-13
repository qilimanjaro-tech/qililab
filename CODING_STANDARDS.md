# qililab coding standards

Shared core v0.2 (Qilimanjaro Software), a draft until the software leads agree it. Copied verbatim, followed by qililab additions. Mechanical rules live in the tools configured in `pyproject.toml` and in CI; this file holds the judgement they cannot make. The review contract is `REVIEW.md`; findings cite the section they apply.

## Tests

Tests are behaviour tests: they drive the public interface at an agreed seam and assert what a caller observes.

- **Seams.** Test at the seams listed in the additions below. A new seam is named in the PR description before tests target it.
- **Observable outcomes.** Assert returned values, raised errors, emitted programs and waveforms, and results read back through the public reader.
- **Independent expected values.** Take expected values from a literal, a worked example, the specification, a published reference or a hardware-validated fixture, never recomputed the way the code computes them.
- **Boundary mocks.** Mock instrument drivers and hardware execution, network, databases, the file system when needed, time and randomness. The package's own classes and functions run for real.
- **Public reach.** When a behaviour is visible only through a `_private` name, add a public accessor or move the test to the seam above.
- **Regressions.** A bug fix starts with a test that fails on the bug.
- **Coverage is evidence.** A line counts as covered when a behaviour test exercises it. Hardware-only code goes in the coverage `omit` list with a reason.

## Code

- **Design.** Prefer deep modules: a small interface over a lot of behaviour. Name things with the terms in `GLOSSARY.md`; a new concept gets a glossary entry first.
- **Units.** Physical quantities carry their unit in the name, a type alias or the docstring (Hz, ns, V, rad, dBm), fixtures included, in the convention the additions state.
- **Suppressions.** Every suppression (`# noqa`, `# type: ignore`, `# ty: ignore`, `# pragma: no cover`, a coverage `omit`) names its rule code and a one-line reason.
- **Comments.** Explain why. A comment that excuses a workaround becomes a type, a lint or a test.
- **Dependencies.** A dependency on another Qilimanjaro package names the released version that carries the needed behaviour.
- **Compatibility.** Public API changes go through a deprecation release unless the PR links an accepted decision to break compatibility.

## Change hygiene

- User-facing changes add a towncrier fragment in `changes/`, in repos that use towncrier.
- Interface or architecture decisions link their decision record; proposals stay labelled as proposals until accepted.

## qililab additions

- **Seams:** a platform built from a runcard with `ql.build_platform` (runcards in `tests/data.py` and `tests/runcards/`); a QProgram compiled by the Qblox or QDAC-II compiler, asserting the emitted program (`is_q1asm_equal` in `tests/test_utils.py`); results and database rows read back through `src/qililab/result/`. TODO(human): agree the seams.
- **Boundary mocks:** instrument drivers are patched with `MagicMock` (`mock_instruments` in `tests/test_utils.py`); VISA instruments run against the pyvisa-sim files in `src/qililab/instruments/sims/`; the database config and clock are patched in the result tests.
- **Units:** QProgram time variables are integers (`src/qililab/qprogram/structured_program.py:266`) in ns (`src/qililab/qprogram/qblox_compiler.py:1157`, `src/qililab/qprogram/qprogram.py:1415`; bus delay `src/qililab/platform/components/bus.py:53`). Frequencies are Hz and phases rad (`SetFrequencyHz`, `SetPhaseRad` at `src/qililab/qprogram/qblox_compiler.py:720` and `:731`). Qblox gain and offset are normalized to [-1, 1] and QDAC-II offsets are V (`src/qililab/qprogram/qprogram.py:1620`). Flux is in Φ0 (`src/qililab/qprogram/crosstalk_matrix.py:488`). Exceptions on QDAC-II buses: `set_trigger` widths are seconds (`src/qililab/qprogram/qprogram.py:1643`), and the list `dwell` is µs and the list `delay` seconds (`src/qililab/qprogram/qprogram.py:2042`).
- **Coverage:** `[tool.coverage]` sets no `fail_under`; Codecov's patch status expects 100% of changed lines (`.github/codecov.yml`). The instrument drivers in the coverage `omit` list wait on the instrument modernization. TODO(human): agree a coverage floor.
- **Tooling:** ruff and mypy skip test files (`extend-exclude` in `[tool.ruff]`, `exclude` in `[tool.mypy]`), so review is the only check on test code. Every source file starts with the Apache 2.0 header, as `src/qililab/utils/serialization.py` does; no lint rule enforces it. Tests marked `qm` never run because `--run-qm` is not registered (`tests/conftest.py:21`).
