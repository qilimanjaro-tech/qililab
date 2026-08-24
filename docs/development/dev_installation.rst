Development Installation
========================

Qililab uses `uv <https://docs.astral.sh/uv/>`_ for dependency management and packaging. To install Qililab in development mode, please run:

.. code-block:: console

    $ git clone https://github.com/qilimanjaro-tech/qililab
    $ cd qililab
    $ uv sync --group dev --all-extras

This creates a ``.venv`` with all runtime and development dependencies. Run tools through ``uv run <command>``, or activate the environment directly:

.. code-block:: console

    $ source .venv/bin/activate  # on Windows: .venv\\Scripts\\activate

Development Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

Qililab uses `ruff <https://docs.astral.sh/ruff/>`_ for linting and formatting, `mypy <https://mypy-lang.org/>`_ for static type checking, and `mdformat <https://mdformat.readthedocs.io/>`_ for Markdown formatting.

Optionally, install the `pre-commit <https://pre-commit.com/>`_ hooks (via `prek <https://github.com/j178/prek>`_) so these checks run automatically on every commit:

.. code-block:: console

    $ uv run prek install

Now for every commit there will be several checks making sure the minimum quality requirements are met:

.. code-block:: console

    $ git commit -m "Test commit"
    ruff.....................................................................Passed
    ruff-format...............................................................Passed
    mypy......................................................................Passed
    mdformat..................................................................Passed
    nbqa-mypy.................................................................Passed
    commitizen check..........................................................Passed
    check for merge conflicts.................................................Passed
    debug statements (python).................................................Passed
    fix end of files..........................................................Passed
    mixed line ending..........................................................Passed
    trim trailing whitespace...................................................Passed
