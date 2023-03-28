Hello World
=============

These notebook is our Hello World, is a very simple program to veify that everithing is going according to plan.

The program consist of creating a platform from where experiments may be performed.
This tutorial can be performed entierly in any computer. Although, for any experiment to be performed it must be run in a computer connected to the instruments.
This is accomplished via ``qiboconnection`` explained in the following page :doc:`Hello Lab<HelloL>`.

::

    # Import everything needed

    import os

    from pathlib import Path
    from qililab import Experiment, build_platform

::

    # adding the path of our runcards

    fname = os.path.abspath("")
    os.environ["RUNCARDS"] = str(Path(fname) / "runcards")

Load a platform
------------------

::

    # Selecct a simple runcard and build the platform

    runcard_name = "HelloWorld"
    platform = build_platform(name=runcard_name)

Runcards are the way to explain qililab your hardware and allows us to use the instruments. An explanation of how to understad and create `runcards <../Documentation/runcards.rst>`_ is in the documentation section.

Print platform
-----------------

::

    # Lets print our chip (imported from the `HelloWorld` runcard).
    # As we can see, we have connected a qubit to the Port 0 and a resonator to the Port 1.

    print(platform.chip)

.. code-block:: none

    Chip None with 1 qubits and 2 ports:

    * Port 0: ----|qubit|----
    * Port 1: ----|resonator|----

::

    # Printing the schema shows how the buses are connected according to de runcard.
    # A more detailed explanation about runcartd is in the documentation section.

    print(platform.schema)

::

    Bus 1 (time_domain readout):  -----|rs_1|--|QRM|------|resonator|----

So there it is, we have created a platform with a simple runcard. From here we could begin our experiments.
