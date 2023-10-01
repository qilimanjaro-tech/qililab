Development Installation
========================

To install Qililab in development mode, please run:

.. code-block:: console

    $ git clone https://github.com/qilimanjaro-tech/qililab
    $ cd qililab
    $ pip install -e .

The `-e` flag ensures that edits to the source code will be reflected when importing Qililab in Python.

Development Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

Qililab contains extra requirements used to run formatting and code quality checks for every commit.
To install them, please run:

.. code-block:: console

    $ pip install -r dev-requirements.txt
    $ pre-commit install

Now for every commit there will be several checks making sure the minimum quality requirements are met:

.. code-block:: console

    $ git commit -m "Test commit"
    black................................................(no files to check)Skipped
    flake8...............................................(no files to check)Skipped
    isort (python).......................................(no files to check)Skipped
    mypy.................................................(no files to check)Skipped
    check python ast.....................................(no files to check)Skipped
    check builtin type constructor use...................(no files to check)Skipped
    check for merge conflicts................................................Passed
    debug statements (python)............................(no files to check)Skipped
    fix end of files.........................................................Passed
    mixed line ending........................................................Passed
    trim trailing whitespace.................................................Passed
    bandit...............................................(no files to check)Skipped
    pylint...............................................(no files to check)Skipped
    mdformat.............................................(no files to check)Skipped
    nbqa-black...........................................(no files to check)Skipped
    nbqa-isort...........................................(no files to check)Skipped
    nbqa-flake8..........................................(no files to check)Skipped
    nbqa-mypy............................................(no files to check)Skipped
