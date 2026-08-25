# Qililab

[![codecov](https://codecov.io/gh/qilimanjaro-tech/qililab/branch/main/graph/badge.svg?token=gSfTPmCeJw)](https://codecov.io/gh/qilimanjaro-tech/qililab)
[![Documentation Status](https://readthedocs.org/projects/qililab/badge/?version=latest)](https://qaas.readthedocs.io/projects/qililab/en/latest/?badge=latest)

Qililab is a generic and scalable quantum control library used for fast characterization and calibration of quantum chips. Qililab also offers the ability to execute high-level quantum algorithms with your quantum hardware.

You can find Qililab's documentation [here](https://qaas.readthedocs.io/projects/qililab/en/latest/index.html)

## Development Guide

We use a number of tools to maintain code quality and consistency:

- **[uv](https://docs.astral.sh/uv/)** for dependency management and packaging.
- **[ruff](https://docs.astral.sh/ruff/)** for linting and code formatting.
- **[mypy](https://mypy-lang.org/)** for static type checking.
- **[mdformat](https://mdformat.readthedocs.io/)** for Markdown formatting.
- **[towncrier](https://github.com/twisted/towncrier)** for automated changelog generation.

### Setup & Dependency Management

Clone the repository and sync the dev environment with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/qilimanjaro-tech/qililab.git
cd qililab
uv sync --group dev --all-extras
```

This creates a `.venv` with all runtime and development dependencies. Run tools through `uv run <command>`, or activate the environment directly:

```bash
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
```

Optionally, install the [pre-commit](https://pre-commit.com/) hooks (via [prek](https://github.com/j178/prek)) so the checks below run automatically on every commit:

```bash
uv run prek install
```

### Testing

We use **pytest** for the test suite:

```bash
pytest tests
```

To run it the same way CI does (parallelized, with coverage):

```bash
pytest -n auto --dist loadfile --cov=qililab --cov-report=xml tests
```

### Linting & Formatting

We enforce code style using [**ruff**](https://docs.astral.sh/ruff/):

```bash
ruff check          # lint
ruff check --fix    # lint and auto-fix
ruff format         # format
```

Markdown files are formatted with [**mdformat**](https://mdformat.readthedocs.io/):

```bash
mdformat .
```

*(We recommend running `ruff check --fix`, `ruff format`, and `mdformat .` before committing any changes.)*

### Type Checking

We use [**mypy**](https://mypy-lang.org/) for static type checking:

```bash
mypy src --ignore-missing-imports
```

### Changelog Management

We manage our changelog using [**towncrier**](https://github.com/twisted/towncrier). Instead of editing `CHANGELOG.md` directly, each pull request adds a small *news fragment* file in the `changes/` directory describing the user-facing change.

Each fragment is named `changes/<PR number>.<category>.md`, where `<category>` is one of:

| Category | Changelog section |
|-----------|----------------------------|
| `feature` | Features |
| `bugfix` | Bugfixes |
| `doc` | Improved Documentation |
| `removal` | Deprecations and Removals |
| `misc` | Misc |

For example, if you open a PR with id #1234 adding a new feature, add:

```
changes/1234.feature.md
```

Inside this file, briefly describe the new feature:

```md
Added a new `cool_feature` in the `qililab.something` module.
```

Instead of manually creating the file, you can run:

```bash
towncrier create --no-edit
```

When cutting a new release, update the version in `pyproject.toml` and run:

```bash
towncrier
```

This aggregates all the news fragments into `CHANGELOG.md` under the new version heading and removes the used fragments.

## Contributions

Thank you for your interest in our project. While we appreciate your enthusiasm and interest in contributing, we would like to clarify our policy regarding external contributions.

### Our Contribution Policy

This project is primarily intended for reference purposes, and we do not actively accept or manage external contributions, including pull requests and issue reports. Our development team maintains this codebase for internal use and does not have the capacity to review or merge contributions from the community.

### Why We Have This Policy

Our decision to limit external contributions is based on our specific project goals, resource constraints, and internal policies. While we understand the value of collaboration and open-source contributions, we have chosen to maintain this project as a reference rather than a collaborative, community-driven effort.

### Seeking Help and Support

If you have questions about using this project or encounter issues, please feel free to open an issue in the repository for discussion. However, please be aware that our ability to provide support or address issues may be limited.

Thank you for your understanding and for considering our project. We hope that you find it useful for your needs, and we wish you the best in your open-source endeavors.

Sincerely,

Qilimanjaro Quantum Tech
