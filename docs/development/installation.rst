Installation
============

To install Qililab in development mode, please run:

.. code-block:: bash

    $ git clone https://github.com/qilimanjaro-tech/qililab
    $ cd qililab
    $ pip install -e .

The `-e`` flag ensures that edits to the source code will be reflected when importing Qililab in Python.

Development Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

Qililab contains extra requirements used to run formatting and code quality checks for every commit.
To install them, please run:

.. code-block:: bash

    $ pip install -r dev-requirements.txt
    $ pre-commit install
