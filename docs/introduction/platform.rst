.. _platform:

Platform
=========

The platform represents the laboratory setup used to control the quantum devices.

The :class:`.Platform` object is the responsible for managing the initializations, connections, setups, and executions of the laboratory, which mainly consists of:

- :class:`.Chip`

- Buses

- Instruments

Tutorial for using the Platform class:
------------------------------------------------------------

Building and printing a Platform:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build a platform, you need to use the :meth:`qililab.build_platform()` function:

.. code-block:: python

    import qililab as ql

    platform = ql.build_platform(runcard="runcards/galadriel.yml")

where "runcards/galadriel.yml" is the path to a YAML file containing a dictionary of the serialized platform. This dictionary contains the information to connect, setup and control the laboratory.

.. note::

    You can find more information about the actual structure of such dictionary, in the :ref:`Runcards <runcards>` section of the documentation.

You can see if the platform has been set correctly printing the platform ``name``, or the ``chip`` and ``buses`` structure at any moment:

>>> print(platform.name)
galadriel

>>> print(platform.chip)
Chip with 5 qubits and 12 ports:
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

where you can see the connections between the buses and the chips.

|

Connecting and setting up the instruments with Platform:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First you need to build the platform as explained in the above example.

.. note::

    You need to have access to the IP's addresses provided in the serialized platform (runcard), in order to connect, and therefore in order to continue.

Now, to connect to the instruments, set them up and turn the signal outputs on, you need to use the following methods:

>>> platform.connect()

connects to all the instruments and blocks the connection for other users. You must be connected in order to proceed with the following steps.

>>> platform.initial_setup()

sets the values of the serialized platform (runcard) to the connected instruments. You might want to skip this step if you think no
parameters have been modified since last time, but we recommend you to do it always anyway.

>>> platform.turn_on_instruments()

turns on the signal output for the generator instruments (local oscillators, voltage sources and current sources). This does not
actually turn the instruments of the laboratory on, it only opens and closes their signal output generation. You might want to skip this
step aswell if the instruments outputs are already open, but again we recommend you to do it always anyway.

|

Executing a circuit with Platform:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To execute a circuit you first need to build, connect and setup the platform as explained in the above examples, which together look like:

.. code-block:: python

    import qililab as ql

    # Building the platform:
    platform = ql.build_platform(runcard="runcards/galadriel.yml")

    # Connecting and setting up the platform:
    platform.connect()
    platform.initial_setup()
    platform.turn_on_instruments()

|

Now you need to define your own Qibo circuit, for example you could build something like a pi pulse and a measurement gate on qubit q (``int``):

.. code-block:: python3

    from qibo.models import Circuit
    from qibo import gates

    circuit = Circuit(q+1)
    circuit.add(gates.X(q))
    circuit.add(gates.M(q))

|

And finally, you are ready to execute it the circuit with the platform:

>>> result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
>>> result.array
array([[5.],
        [5.]])

When disabling scope acquisition mode, the array obtained has shape `(#sequencers, 2, #bins)`. In this case,
given that you are using only 1 sequencer to acquire the results, you would obtain an array with shape `(2, #bins)`.

.. note::

    Remember that the values obtained correspond to the integral of the I/Q signals received by the
    digitizer.

|

Running a Rabi sequence with Platform:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To do a Rabi sequence, you need to build, connect and setup the platform, and you also need a circuit with a
pi pulse and a measurement gate in qubit q (``int``), as in the previous examples:

.. code-block:: python

    import qililab as ql

    import numpy as np

    from qibo.models import Circuit
    from qibo import gates

    # Defining the Rabi circuit:
    circuit = Circuit(q+1)
    circuit.add(gates.X(q))
    circuit.add(gates.M(q))

    # Building the platform:
    platform = ql.build_platform(runcard="runcards/galadriel.yml")

    # Connecting and setting up the platform:
    platform.connect()
    platform.initial_setup()
    platform.turn_on_instruments()

Now to run the Rabi sequence, you would need to run this sequence by looping over the gain of the AWG used
to create the pi pulse. To do so, you need to use the `set_parameter` method with the alias of the bus used
to drive qubit 0 (Let's assume it's called "drive_q0"):

.. code-block:: python3

    results = []
    gain_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.0]

    for gain in gain_values:
        platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
        result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
        results.append(result.array)

No you can use `np.hstack` to stack the obtained results horizontally. By doing this, you would obtain an
array with shape `(2, N)`, where N is the number of elements inside the loop:

>>> results = np.hstack(results)
>>> results
array([[5, 4, 3, 2, 1, 2, 3],
        [5, 4, 3, 2, 1, 2, 3]])

You can see how the integrated I/Q values oscillated, indicating that qubit 0 oscillates between ground and
excited state!

|

A faster Rabi sequence, translating the circuit to pulses:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since you are looping over variables that are independent of the circuit (in this case, the gain of the AWG),
you can speed up the experiment by translating the circuit into pulses only once:

.. code-block:: python3

    from qililab.pulse.circuit_to_pulses import CircuitToPulses

    pulse_schedule = CircuitToPulses(platform=platform).translate(circuits=[circuit])

and then, executing the obtained pulses inside the loop. Which is the same as before, but passing the
`pulse_schedule` instead than the `circuit`, to the `execute` method:

.. code-block:: python3

    results = []
    gain_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.0]

    for gain in gain_values:
        platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
        result = platform.execute(program=pulse_schedule, num_avg=1000, repetition_duration=6000)
        results.append(result.array)

If you now stack and print the results, you see how you obtain similar results, but much faster!

>>> results = np.hstack(results)
>>> results
array([[5, 4, 3, 2, 1, 2, 3],
        [5, 4, 3, 2, 1, 2, 3]])

|

Ramsey sequence, looping over a parameter inside a the circuit:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To do a Ramsey, you also need to build, connect and setup the platform, but the circuit is different from the previous,
basically for doing it in qubit q (``int``), you need:

.. code-block:: python

    import qililab as ql

    from qibo.models import Circuit
    from qibo import gates

    # Defining the Ramsey circuit:
    circuit = Circuit(q + 1)
    circuit.add(gates.RX(q, theta=np.pi/2))
    circuit.add(gates.Align(q, t=0))
    circuit.add(gates.RX(q, theta=np.pi/2))
    circuit.add(gates.M(q))

    # Building the platform:
    platform = ql.build_platform(runcard="runcards/galadriel.yml")

    # Connecting and setting up the platform:
    platform.connect()
    platform.initial_setup()
    platform.turn_on_instruments()

Now to run the Ramsey sequence, you would need to run this sequence by looping over the `t` parameter of the wait (Align) gate. To do so,
since the parameter is inside the Qibo circuit, you will need to use Qibo own `circuit.set_parameters` method, putting the parameters you want to
set in the order they appear in the circuit construction:

.. code-block:: python3

    results_list = []
    wait_times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    for wait in wait_times:
        circuit.set_parameters([np.pi/2, wait, np.pi/2])
        result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
        results_list.append(result.array)

which would change the gates parameters for each execution. Concretely, we  were always setting `np.pi/2` to the `theta` parameter of the first
`RX` gate, then the looped wait time `t` in the `Align` gate, and then another `np.pi/2` to the second `RX` gate.
