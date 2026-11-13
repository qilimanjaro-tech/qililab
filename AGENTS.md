# qililab

Qilimanjaro's quantum-control library: it builds a platform from a runcard, expresses pulse-level QPrograms and experiments, compiles them for Qblox, QDAC-II and Quantum Machines instruments, runs them and stores the results. qpysequence sits below it; qilitools, seqtante and seqtante-open build on it.

## Navigate by task

- Platform, buses and runcards: `src/qililab/platform/`, `src/qililab/settings/`.
- QProgram, experiments and the Qblox and QDAC-II compilers: `src/qililab/qprogram/`; QProgram variables and their domains: `src/qililab/core/`.
- Instruments, controllers and connections: `src/qililab/instruments/`, `src/qililab/instrument_controllers/`, `src/qililab/instrument_connections/`.
- Quantum Machines (optional `quantum-machines` extra): `src/qililab/extra/quantum_machines/`.
- Results, streaming and the measurement database: `src/qililab/result/`. Waveforms: `src/qililab/waveforms/`.
- Tests: `tests/`, mirroring `src/qililab/`. Test runcards: `tests/runcards/` and `tests/data.py`.
- User docs: `docs/` (Sphinx, built with `-W` on every PR). Path owners: `.github/CODEOWNERS`.
- Before writing or reviewing code or tests: read `CODING_STANDARDS.md` and `REVIEW.md`.
- Domain vocabulary: `GLOSSARY.md`; name code, tests and PRs with its terms. Decisions: `docs/adr/`. Tracker and triage: `docs/agents/`.
- Project knowledge base: TODO(human): link the domain wiki.

## Commands

- **Verify (run before calling work done):** `uv run ruff check . && uv run ruff format --diff . && uv run mypy src --ignore-missing-imports && uv run deptry src && uv run mdformat --check --exclude 'CHANGELOG.md' --exclude '.venv/**' . && uv run pytest -n auto --dist loadfile --cov=qililab --cov-report=xml tests && uv run sphinx-build -W -q -b html docs docs/_build --keep-going`
- Focused test: `uv run pytest tests/qprogram/test_qblox_compiler.py -k <name>`
- Fix lint and format: `uv run ruff check --fix . && uv run ruff format .`

<important if="you set up the environment or hit a dependency-resolution error">
- Setup: `uv sync --locked --group dev --group docs --all-extras`. `qpysequence` resolves only from the private `qilimanjaro` CodeArtifact index: set `UV_INDEX_QILIMANJARO_USERNAME=aws` and `UV_INDEX_QILIMANJARO_PASSWORD` to a CodeArtifact token first, as `.github/workflows/tests.yml` does.
</important>

<important if="you add, remove or upgrade dependencies">
- Dependency audit (advisory in CI): `uv run --with pip-audit==2.10.1 --no-build-package pip-audit pip-audit`
</important>

<important if="you add or check changelog fragments">
- Preview pending changelog fragments: `uv run towncrier build --draft --version unreleased`
</important>

## Boundaries

- Validate with synthetic inputs and offline tests; hardware, lab databases and production runcards are in scope only when the task names them.
- Report every gate you could not run and why.
- Keep credentials, runcards with real addresses and measurement data out of the repository and out of agent instructions.

## Critical invariants

- The repository is public: no internal links, hostnames, customer data or lab addresses in code, docs, commits or agent files, because anything merged is published.
- Keep Python 3.11 working, because mypy checks against 3.13 only (`[tool.mypy]`) and PRs run the tests on 3.11 and 3.13.

<important if="you add, remove or upgrade dependencies or change their sources, constraints or overrides">
- Keep `qpysequence` mapped to the explicit `qilimanjaro` index in `[tool.uv.sources]`, because an unmapped private name can resolve from a public mirror.
- Don't loosen the CVE floors in `[tool.uv] constraint-dependencies` or the `override-dependencies` pins without checking the note next to each, because they stop a re-resolve from regressing them.
</important>

<important if="you touch the package version, release tags or the publish workflow">
- The version comes from git tags (hatch-vcs): never set one in `pyproject.toml`, and tag releases as a bare `MAJOR.MINOR.PATCH`, because `.github/workflows/publish.yml` fails when the built version differs from the tag.
</important>

<important if="you make a user-facing change or touch CHANGELOG.md">
- Never edit `CHANGELOG.md` by hand; each PR adds a towncrier fragment (`[tool.towncrier]` in `pyproject.toml`, naming in README.md), because releases rebuild the changelog from fragments.
</important>

<important if="you touch numeric code, units, golden values or tolerances">
- Units: durations are integer ns, frequencies Hz, phases rad, Qblox gain and offset normalized to [-1, 1], QDAC-II offsets V, flux in Φ0; QDAC-II trigger widths and list delays are seconds and list dwell is µs. The full convention and its exceptions are in CODING_STANDARDS.md additions.
- Every numeric change ships with the before-and-after evidence REVIEW.md asks for.
</important>

## Branches and PRs

<important if="you create a branch, commit, or open or update a pull request">
Decision 2 (Qilimanjaro Software branch conventions):
- Branch from `main`, named after the ticket: `qhc-####-<topic>` (Linear team QHC). PR title `[QHC-####] Name`, with the ticket linked.
- Experiments: `exp/<topic>`, no ticket key. Deliveries: `delivery/<project>-<topic>`.
- Existing delivery branches keep their names until retired: `BSC`, `BSC-branch`, `BSC-AQPU-calibration`, `BSC-file_path_seqtante_temp`.
</important>

## Agent workflow

- Gardener: TODO(human) (owns the environment-change list after each retro)
- Trust rung: 1 (Pair), proposed: the human drives and reads every diff live.
- Scratch output (research, specs, evidence) goes to `.agents/artifacts/`, which is gitignored.

## Agent skills

### Issue tracker

<important if="you read, file or triage issues">
Work is tracked in Linear, team QHC; GitHub issues come from external users of the public repo. See `docs/agents/issue-tracker.md`.
</important>

### Triage labels

The five default triage labels, unchanged. See `docs/agents/triage-labels.md`.

### Domain docs

<important if="you name code, tests or PRs, or record an architectural decision">
Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
</important>

## Completion

Work is ready for review when the verify command passes and its output is attached to the PR. The verify command runs the gates of the workflows that run on pull requests. Codecov also expects every changed line to be covered (`.github/codecov.yml`).
