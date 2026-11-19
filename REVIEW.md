# qililab review contract

Shared core v0.2 (Qilimanjaro Software), a draft until the software leads agree it. Copied verbatim, followed by qililab additions. Applies to humans and agents. AI review is advisory: a qualified human reads every line of the same revision before merge.

## Findings

- Each finding gives `path:line` and quotes the line, then the trigger, the consequence, the evidence and a concrete next step. No citation, no finding.
- Separate confirmed defects from questions and missing evidence. Recheck earlier findings on the current revision and state the inspected scope.
- Review on two axes: standards (`CODING_STANDARDS.md`, citing the section) and spec (the linked ticket, PRD or TRD: missing, extra, wrong; quote the spec line).
- Green CI is evidence, not a verdict: say what it covers and what it misses.

## Severity

Lead with the highest.

- **blocker**: wrong results, data loss, a security hole, or a broken invariant from AGENTS.md. Fix before merge.
- **major**: a likely bug, or a design problem the next change will trip over. Fix, or justify in the PR.
- **minor**: worth fixing, not blocking.
- **nit**: taste. At most 3 per review; drop the rest.

## qililab additions

- **Compiled programs.** A change to `src/qililab/qprogram/` shows the emitted Q1ASM or QDAC-II program before and after, and compiling leaves the QProgram's operations unchanged. TODO(human): confirm.
- **Runcards.** A change to bus, instrument or controller settings keeps existing runcards loading, and `save_platform` writes back what `build_platform` read. A removed runcard field is deprecated first and listed in `docs/development/deprecations.rst`. TODO(human): confirm.
- **Hardware boundary.** A change under `src/qililab/instruments/`, `src/qililab/instrument_controllers/` or `src/qililab/instrument_connections/` says whether it ran on the instrument; behaviour that did not run on hardware is named as untested in the PR.
- **Downstream API.** qilitools, seqtante and seqtante-open import qililab: a renamed or removed public name goes through a deprecation release and `docs/development/deprecations.rst`.
- **Units.** Values follow the convention in CODING_STANDARDS.md additions; check every conversion where a value leaves this repo (compiler, driver, instrument).
- **Parity.** Any numeric change ships before-and-after output, with each difference explained: from a platform built from `tests/runcards/*.yml` where it reaches the changed code, otherwise from a synthetic input that does (for a compiler change, the emitted program; for result code, a synthetic dataset).
