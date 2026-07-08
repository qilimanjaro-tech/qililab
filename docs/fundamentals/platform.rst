.. _platform:

Platform
=========

The platform represents the laboratory setup used to control the quantum devices.

The :class:`.Platform` object is the responsible for managing the initializations, connections, setups, and executions of the laboratory, which mainly consists of:

- Buses

- Instruments

Below you can find a beginner's tutorial on how to use the :class:`.Platform` class to execute quantum experiments on your hardware.

.. note::

    The following examples contain made up results. These will soon be updated with real results.

Building and printing a Platform:
----------------------------------

To build a platform, you need to use the :meth:`ql.build_platform()` function:

.. code-block:: python

    import qililab as ql

    platform = ql.build_platform(runcard="runcards/galadriel.yml")

where ``"runcards/galadriel.yml"`` is the path to a YAML file containing the :ref:`runcard <runcards>`, a dictionary of the serialized platform. This dictionary contains the information to connect, set up, and control the laboratory.

.. note::

    You can find more information about the actual structure of such dictionary, in the :ref:`Runcards <runcards>` section of the documentation.

You can verify if the platform has been built correctly, by printing the platform ``name``, and its ``chip`` and ``buses`` structures:

>>> print(platform.name)
galadriel

>>> print(platform.chip)
Chip with 2 qubits and 6 ports:
* Port drive_line_q0 (drive): ----|qubit_0|----
* Port drive_line_q1 (drive): ----|qubit_1|----
* Port flux_line_q0 (flux): ----|qubit_0|----
* Port flux_line_q1 (flux): ----|qubit_1|----
* Port feedline_input (feedline_input): ----|resonator_q0|--|resonator_q1|----
* Port feedline_output (feedline_output): ----|resonator_q0|--|resonator_q1|----

>>> print(platform.buses)
Bus feedline_bus:  -----|QRM1|--|rs_1|------|resonator_q0|------|resonator_q1|----
Bus drive_line_q0_bus:  -----|QCM-RF1|------|qubit_0|----
Bus flux_line_q0_bus:  -----|QCM1|------|qubit_0|----
Bus drive_line_q1_bus:  -----|QCM-RF1|------|qubit_1|----
Bus flux_line_q1_bus:  -----|QCM1|------|qubit_1|----

which displays the connections between the buses, instruments and elements of the chip.

|

Connecting and setting up the instruments with Platform:
---------------------------------------------------------

After building the platform, you need to connect to the instruments, set all the parameters defined in the runcard, and turn on the sources outputs using the following methods:

.. code-block:: python

    platform.connect()
    # Connects to all the instruments and blocks the connection for other users.
    # You must be connected to proceed with the following steps.

    platform.initial_setup()
    # Sets the values of the runcard (serialized platform) to the connected instruments.
    # You might want to skip this step if you think no parameters have been modified since last time, but we recommend doing it anyway.

    platform.turn_on_instruments()
    # Turns on the signal output for the generator instruments (RF, voltage sources and current sources).
    # This does not actually turn on the instruments of the laboratory, it only opens the signal output generation of the sources.
    # You might want to skip this step if the instruments outputs are already open, but again, we recommend doing it anyway.

.. note::

    To connect, your computer must be in the same network of the instruments specified in the runcard (with their IP's addresses).

|

Executing a circuit with Platform:
-----------------------------------
Once the platform is built, connected and set up, you can execute a circuit defined with ``qilisdk.digital``. For example, a
pi pulse followed by a measurement gate on qubit ``q`` (``int``):

.. code-block:: python3

    from qilisdk.digital import Circuit, X, M

    circuit = Circuit(q + 1)
    circuit.add(X(q))
    circuit.add(M(q))

The circuit is transpiled to the platform's native gate set and executed with :meth:`.Platform.execute_circuit`, which
returns a dictionary of measurement samples:

>>> result = platform.execute_circuit(circuit, nshots=1000)

.. note::

    See :meth:`.Platform.execute_circuit` and :meth:`.Platform.compile_circuit` for the full signature and options, and
    :ref:`Transpilation <transpilation>` for details on how circuits are transpiled and compiled.

