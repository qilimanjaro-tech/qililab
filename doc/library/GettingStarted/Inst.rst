Installation
+++++++++++++++
Let's begin with the installation of the library.
Make sure you have all the :doc:`Pre-requirements <Pre>` to follow along.

Some basics on Linux
=====================

.. note::
    The steps are going to be explained for a Unix environment, if your machine runs another operating system you may have to slightly change the commands.

* ``ls`` shows what is in the directory you are currently at.
* ``ls -a`` shows what is in the directory you are currently at, even the invisible elements.
* ``cd`` it is used to move in between directories, ``cd namedirectory`` goes to the directory *namedirectory*.
* ``mkdir namedirectory`` creates a directory called namedirectory.
* ``pip freeze`` shows the installed libraries.

.. _copyrepo:

Copy Repo
===============
In the directory you would like to work, create a directory called *repos*
::

    mkdir repos

Here is where our repos are going to be saved. If we type ``ls``, it should show the created folder.

Enter in said folder
::

    cd repos

Here is where qililab is going to be cloned from GitHub. To do that, execute the command ``git clone`` with the URL of the repository.
::

    git clone https://github.com/qilimanjaro-tech/qililab.git

To verify everything is going as planned, if we type ``ls`` a new directory (**qililab**) should appear.
Let us enter this directory.
::

    cd qililab

Create the Environment
=======================
In the folder qililab, :ref:`previously <copyrepo>` cloned.
For convenience, let us create a virtual environment in were will be installing *qililab*.
::

    virtualenv .venv

And let's enter the environment.
::

    source .venv/bin/activate

To verify that everything is going as planned it is recommended to type
::

    which python

this command tells which python is going to be used inside the virtual environment. The result should be the path of python inside the virtual environment.

.. note::
    `.venv` is just the name of the virtual environment, we use this name just for a meeting, if preferred any name can be used.

.. note::
    Once finished using the virtual environment use ``deactivate`` to exit the environment.

Install
=========
Let's finally install *qililab*. Type:
::

    pip install -e .

This command will install the library of the directory we are currently in (in our case *qililab*).

.. note::
    The ``-e`` will avoid making a copy of the current state of the library so that if any changes are made, when imported, those changes will be present.

Compute ``pip freeze`` to verify all the libraries are being installed properly.

Congratulations, you have succesfully installed **qililab**

Verification
===============
Let's make sure everything we have done is correct.
Launch python and import qililab
::

    python

::

    import qililab

Verify what version of qililab is installed
::

    qililab.__verison__

And exit python

::

    exit()

As a last verification let's run a simple program using *Jupyter Notebook*.
Enter de folder of examples:
::

    cd examples

And launch Jupyter Notebook

::

    jupyter notebook

A browser is opened with the folder *examples* of our repository.

Open the *example_using_soprano* and follow the indications.
