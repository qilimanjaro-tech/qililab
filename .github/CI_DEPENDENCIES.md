# CI dependency builds

Use uv 0.13.8 or newer for this repository. GitHub Code Quality, Tests and Documentation pin uv 0.13.8 because its build-hash and source-exception behavior is covered by the compatibility checks. Older uv versions cannot read the hashed build constraints.

The three workflows sync the committed lock with `--no-build --no-cache --require-build-hashes`. Their dependency installs start without cached wheels, so a previously built cache cannot hide an unavailable wheel. First-party Qililab editable builds remain enabled. Its hatch-vcs version scheme and tags are unchanged.

uv 0.13.8 treats explicit `--no-binary-package` names as exceptions to `--no-build`. Only the following third-party source builds are permitted:

| Package | Locked version | Why the exception is necessary |
| --- | --- | --- |
| qblox-instruments | 1.0.3 | The firmware-compatible hardware pin has no wheel in the committed lock. Removing its exception makes a clean install fail. |
| marshmallow-polyfield | 5.11 | Source-only dependency of the pinned qm-qua 1.2.4 extra, which all-extras CI installs. Removing its exception makes a clean install fail. |

The exact reviewed sdist hashes and reasons are recorded in [ci-build-exceptions.toml](ci-build-exceptions.toml). Regression checks match them against uv.lock and each workflow's allowlist. A version, artifact or exception change requires a fresh compatibility review. Hardware pins, runtime overrides, CVE floors and the explicit QPySequence index mapping must be preserved.

Isolated first-party and approved third-party builds use the exact build-tool versions and wheel hashes in `tool.uv.build-constraint-dependencies`. This includes Hatchling, hatch-vcs and their transitive requirements, including the editable-build hook, plus setuptools and wheel for the two legacy source distributions. `--require-build-hashes` rejects an unreviewed backend dependency before the source backend runs. Build isolation stays enabled.

The Tests workflow checks Python 3.11, 3.12 and 3.13 on pull requests as well as main. Its local source-fixture regressions prove that an unapproved source package is rejected, named exceptions can build, first-party editable builds still work, and an unreviewed build dependency is rejected. They use no instrument, database, scheduler or upload service.

To recheck compatibility, start with an empty environment and no uv cache, then run the exact workflow sync commands on Linux for all three supported Python versions, plus the docs group on Python 3.13. Temporarily remove each named exception to confirm it is still needed. Verify import smoke tests, the repository checks and strict docs. A local source-first QPySequence substitute can support development, but final CI must also prove the approved private wheel is available.

This policy covers GitHub Code Quality, Tests and Documentation. The release-tool environment has its own policy. Read the Docs uses its separate installation configuration. Do not add a source exception merely to make a dependency upgrade pass.
