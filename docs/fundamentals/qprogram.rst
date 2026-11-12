.. _qprogram:

QProgram
=========

:class:`.QProgram` is a hardware-agnostic pulse-level programming interface for describing quantum programs.

Extracting the greatest performance from quantum hardware requires real-time pulse-level instructions. QProgram answers that need: it enables the quantum physicist user to specify the exact time dynamics of an experiment.

The input is given as arbitrary, time-ordered operations scheduled in parallel over multiple virtual hardware resources, called buses. The system also allows the user to recover the time dynamics of the measured output. This lower level of programming offers the user more control than programming with `Circuit`.

Moreover, it provides advanced features such as variables, and execution flow structures.

qililab's :class:`.QProgram` is the ``QProgram`` of the `qprogram <https://github.com/qilimanjaro-tech/qprogram>`_ library, with its Qblox (``qp.qblox``) and QDAC (``qp.qdac``) operations, plus a few things only qililab has: ``infinite_loop()``, ``if_trigger()``, ``qp.qblox.play(..., wait_time)``, ``qp.qblox.measure_reset()``, and the ``with_*`` transforms the platform applies before compiling. qprogram can describe more than qililab can run: every program is validated when it is compiled, and anything qililab cannot run raises a ``qprogram.ValidationError`` naming the problem.

Buses
-----
QProgram is meant to be agnostic to the underlying hardware implementation, while still allowing low-level control. Therefore, our references are **virtual** buses. The backend which executes our programs is responsible for mapping these virtual buses to the proper physical instrument channel within the quantum control hardware.

Buses are identified by their alias.

Operations
-----------------------

Operations are a central part of :class:`QProgram`. They range from playing a pulse, acquiring data, or changing physical parameters of the system in real-time. All operations are exposed through public methods: the ones every instrument shares on the program itself (``play``, ``wait``, ``sync``, ``measure``, ``set_frequency``, ``set_phase``, ``reset_phase``, ``set_gain``, ``set_offset``), the Qblox ones under ``qp.qblox`` and the QDAC ones under ``qp.qdac``.

Variables
---------------------

The `variable` method in QProgram declares a variable, identified by a name made of letters, digits and underscores. These variables can be utilized to parameterize quantum operations, thereby facilitating easy adjustments and iterations over different experimental configurations. A variable can also carry a label and units, which the results use for their axes.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable("frequency", units="Hz")

A variable is given its values by a loop. An operation can use the variable itself, or the variable plus or minus a constant (``wait_time + 100``).

Loops
-------

These loops enable the user to iterate over a sequence of values for a given variable. Additionally, loops can be nested, which is invaluable for experiments that require multi-dimensional sweeps.

Sweeps
^^^^^^^
The `sweep` method opens a loop over a range of values, from `start` to `stop` by `step`. `start` is always the first value; `stop` is the last one when `step` divides `stop - start`.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable("frequency", units="Hz")
    with qp.sweep(frequency).from_range(100e6, 200e6, 10e6):
        qp.set_frequency(bus="drive_bus", frequency=frequency)

The former ``for_loop(variable, start, stop, step)`` still works but is deprecated: when `step` does not divide `stop - start`, it rounds the number of points down where ``from_range`` rounds it to the nearest.

Inner Loops
^^^^^^^^^^^^

Loops can be nested, which is invaluable for experiments that require multi-dimensional sweeps. In the following example, we loop over frequencies and for each frequency value we loop over gains.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable("frequency", units="Hz")
    gain = qp.variable("gain")
    with qp.sweep(frequency).from_range(100e6, 200e6, 10e6):
        qp.set_frequency(bus="drive_bus", frequency=frequency)
        with qp.sweep(gain).from_range(0.0, 1.0, 0.1):
            qp.set_gain(bus="drive_bus", gain=gain)

Parallel Loops
^^^^^^^^^^^^^^^

Several sweeps combined with ``|`` run in parallel, advancing together. They must have the same number of points.

.. code-block:: python3

    qp = QProgram()
    frequency = qp.variable("frequency", units="Hz")
    gain = qp.variable("gain")
    with qp.sweep(frequency).from_range(100e6, 200e6, 10e6) | qp.sweep(gain).from_range(0.0, 1.0, 0.1):
        qp.set_frequency(bus="drive_bus", frequency=frequency)
        qp.set_gain(bus="drive_bus", gain=gain)

Playing Waveforms
------------------------------

QProgram's play method is a versatile function that allows you to play either a singular waveform or an I/Q pair of waveforms on a designated bus. This provides granular control over the signal's amplitude, frequency, and phase. A waveform can also be given by the name a :class:`.Calibration` holds it under.

.. code-block:: python3

    from qililab import Gaussian, IQDrag, IQPair, Square

    square_wf = Square(amplitude=1.0, duration=40)
    gaussian_wf = Gaussian(amplitude=1.0, duration=100, num_sigmas=4.5)
    drag_wf = IQDrag(amplitude=1.0, duration=100, num_sigmas=4.5, drag_coefficient=-2.0)

    qp = QProgram()
    qp.play(bus="flux_bus", waveform=square_wf)
    qp.play(bus="drive_bus", waveform=gaussian_wf)
    qp.play(bus="drive_bus", waveform=IQPair(I=square_wf, Q=square_wf))
    qp.play(bus="drive_bus", waveform=drag_wf)

Acquisition and Real-Time Averaging
--------------------------------------

The `average` method repeats its body a number of times on the instruments and averages the measurements in it. `measure` plays a readout pulse and integrates the response with the given weights; ``qp.qblox.acquire`` only integrates. Both return a handle, which identifies the measurement in the results.

.. code-block:: python3

    readout = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=1.0, duration=2000))

    qp = QProgram()
    with qp.average(1000):
        measurement = qp.measure(bus="readout_bus", waveform=readout, weights=weights)

    result = platform.execute_qprogram(qp)
    iq = result.get(measurement)  # an xarray.DataArray with an "IQ" dimension

A measurement returns the integrated I/Q values by default. Ask for the thresholded state too with ``fields=[MeasurementField.IQ, MeasurementField.STATE]`` (``from qprogram.operations.operation import MeasurementField``), and read it with ``result.get(measurement, field="state")``.

``qp.qblox.scope(bus)`` records the scope trace of the bus's QRM, triggered by the bus's acquisitions: ``result.get(scope, field="raw")``.

QDAC
------

The QDAC plays a list of voltages, stepped by triggers. It is set up before the run: ``qp.qdac.play`` and ``qp.qdac.set_trigger`` go before the loops, and the loops on the Qblox buses wait for the QDAC's triggers. A QDAC operation inside a loop is rejected.

.. code-block:: python3

    qp = QProgram()
    qp.qdac.play(bus="flux_bus", waveform=Ramp(from_amplitude=0.0, to_amplitude=0.5, duration=100), dwell=2)
    qp.qdac.set_trigger(bus="flux_bus", duration=10e-6, position="step", outputs=[1])
    with qp.average(100):
        qp.qblox.wait_trigger(bus="readout_bus", duration=4)
        qp.measure(bus="readout_bus", waveform=readout, weights=weights)

Synchronization and Timing
----------------------------

The sync operation in QProgram is a powerful feature for experiments requiring precise timing. It ensures that all operations across specified buses are synchronized, allowing for a coordinated start. This is crucial in multi-qubit experiments where the timing between different qubit operations must be exact to achieve the desired quantum state.

Saving and loading
-------------------

A QProgram is saved as text in the ``.qp`` format: ``str(qp)``, read back with ``QProgram.from_qp(text)``. This is how the results database stores it. QPrograms saved as YAML by earlier qililab versions load with ``ql.deserialize(text)``.
