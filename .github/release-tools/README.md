# Release tools

Publish installs this non-package Python 3.13 project once with `--locked --no-build --no-default-groups`. Artifact check and upload then use the same environment's Python directly, without another resolution. The separate `test` group is used only by the release-tools test job.

The tool files come from a sparse checkout at `github.workflow_sha`. The build still uses its requested ref, so workflow dispatch can publish an older tag that predates this lock. The dev-build caller uses a local reusable-workflow reference at the same workflow revision. Missing tool files or a stale lock fail the job, with no transient-tool fallback.

To update the tools, use uv 0.13.8 and Python 3.13:

```bash
uv lock --project .github/release-tools --upgrade --no-build
uv sync --project .github/release-tools --locked --no-build --no-default-groups --group test
RELEASE_TOOLS_INTEGRATION=1 uv run --project .github/release-tools --no-sync pytest --confcutdir=tests/ci tests/ci -q
```

Review every transitive version, artifact source and hash in the lock. Preserve the applicable security floors from the runtime project. Run the installation tests on Linux with fresh environments and empty caches. The job tests denied source builds, missing/stale locks, incorrect hashes, fixture distributions, validation failure and dry-run behavior. AWS and upload calls are stubbed.

This lock does not constrain Qililab's first-party build requirements or the third-party runtime dependencies installed by the other CI jobs.
