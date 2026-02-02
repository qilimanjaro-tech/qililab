QProgram
=========

:class:`.QProgram` is a hardware-agnostic pulse-level programming interface for describing quantum programs.

Extracting the greatest performance from quantum hardware requires real-time pulse-level instructions. QProgram answers that need: it enables the quantum physicist user to specify the exact time dynamics of an experiment.

The input is given as arbitrary, time-ordered operations scheduled in parallel over multiple virtual hardware resources, called buses. The system also allows the user to recover the time dynamics of the measured output. This lower level of programming offers the user more control than programming with `Circuit`.

Moreover, it provides advanced features such as variables, and execution flow structures.

Buses
-----
QProgram is meant to be agnostic to the underlying hardware implementation, while still allowing low-level control. Therefore, our references are **virtual** buses. The backend which executes our programs is responsible for mapping these virtual buses to the proper physical instrument channel within the quantum control hardware.

Buses are identified by their alias.

Operations
-----------------------

Operations are a central part of :class:`QProgram`. They range from playing a pulse, acquiring data, or changing physical parameters of the system in real-time. All operations are exposed through public methods.

Variables
---------------------

The `variable` method in QProgram allows for the dynamic declaration of variables. These variables can be utilized to parameterize quantum operations, thereby facilitating easy adjustments and iterations over different experimental configurations. When declaring a variable, its `Domain` must be specified. The `Domain` associates a variable with a specific physical property.

For instance, you can define a variable with `Domain.Frequency` and use it to change the frequency of the NCO.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)

If the variable is not accossiated with any physical property, it should be declared as `Domain.Scalar`. In that case, the data type of the variable must also be specificied. Available data types are `int` and `float`.

.. code-block:: python3

    qp = QProgram()
    int_scalar = qp.variable(label="int_scalar", domain=Domain.Scalar, type=int)
    float_scalar = qp.variable(label="float_scalar", domain=Domain.Scalar, type=float)

In the future, these variables will be treated as mathematical objects, allowing the user to evaluate complex expressions.

For now, the only way to assign values to a variable is through loops.

Loops
-------

QProgram offers a rich set of control structures, including various types of loops.

These loops enable the user to iterate over a sequence of values for a given variable. Additionally, loops can be nested, which is invaluable for experiments that require multi-dimensional sweeps. There are currently three flavours of loops.

For-Loop
^^^^^^^^^
The `for_loop` method provides the traditional loop structure, allowing the user to specify the `start`, `stop`, and `step` values for a variable, thereby creating a range over which the loop will iterate. Both `start` and `stop` are inclusive.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    with qp.for_loop(variable=frequency, start=100e6, stop=200e6, step=10e6):
        qp.set_frequency(bus="drive_bus", frequency=frequency)

Loops with numpy
^^^^^^^^^^^^^^^^^

The `loop` method allows the user to iterate over a numpy array of arbitrary values.

.. code-block:: python3

    frequency_values = np.random.uniform(low=100e6, high=200e6, size=201)

    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    with qp.loop(variable=frequency, values=frequency_values):
        qp.set_frequency(bus="drive_bus", frequency=frequency)

Inner Loops
^^^^^^^^^^^^

Loops can be nested, which is invaluable for experiments that require multi-dimensional sweeps. In the following example, we loop over frequencies and for each frequency value we loop over gains.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.for_loop(variable=frequency, start=100e6, stop=200e6, step=10e6):
        qp.set_frequency(bus="drive_bus", frequency=frequency)
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="drive_bus", gain=gain)

Parallel Loops
^^^^^^^^^^^^^^^

Finally, the `parallel` method is provided, which allows multiple loops to be run in parallel.

.. code-block:: python3

    from qililab.qprogram.blocks import ForLoop

    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.parallel(loops=[ForLoop(variable=frequency, start=100e6, stop=200e6, step=10e6),
                            ForLoop(variable=gain, start=0.0, stop=1.0, step=0.1)]):
        qp.set_frequency(bus="drive_bus", frequency=frequency)
        qp.set_gain(bus="drive_bus", gain=gain)

Playing Waveforms
------------------------------

QProgram's play method is a versatile function that allows you to play either a singular waveform or an I/Q pair of waveforms on a designated bus. This provides granular control over the signal's amplitude, frequency, and phase. You can even use custom waveforms, making it adaptable for a wide range of quantum experiments.

.. code-block:: python3

    from qililab.waveforms import Square, Gaussian, IQPair

    square_wf = Square(amplitude=1.0, duration=40)
    gaussian_wf = Gaussian(amplitude=1.0, duration=100, num_sigmas=4.5)
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=4.5, drag_coefficient=-2.0)

    qp = QProgram()
    qp.play(bus="flux_bus", waveform=square_wf)
    qp.play(bus="drive_bus", waveform=gaussian_wf)
    qp.play(bus="drive_bus", waveform=IQPair(I=square_wf, Q=square_wf))
    qp.play(bus="drive_bus", waveform=drag_wf)

Acquisition and Real-Time Averaging
--------------------------------------

The average and acquire methods in QProgram are designed for experiments that require real-time data analysis. The average method performs real-time averaging over a specified number of shots, providing immediate feedback for optimizing parameters. The acquire method allows for data collection based on either a set duration or a set of weights, offering flexibility in how you gather and interpret your data.

Synchronization and Timing
----------------------------

The sync operation in QProgram is a powerful feature for experiments requiring precise timing. It ensures that all operations across specified buses are synchronized, allowing for a coordinated start. This is crucial in multi-qubit experiments where the timing between different qubit operations must be exact to achieve the desired quantum state.
