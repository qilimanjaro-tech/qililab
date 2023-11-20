What is Qililab?
==================

Qililab is a generic and scalable quantum control library used for fast characterization
and calibration of quantum chips. Qililab also offers the ability to execute high-level
quantum algorithms with your quantum hardware.

At the core of the Qililab package we have the :class:`~qililab.platform.Platform` object. This is your quantum
laboratory. It contains all the needed information to execute quantum sequences in your hardware, which include:

- Instruments: addresses, connectivity, calibrated parameters and more.
- Chip: number of qubits, couplers, resonators, ports and its connectivity.
- Native gates: a list of the gates supported by your hardware together with its pulse representation.

The :class:`~qililab.platform.Platform` class supports executing high-level quantum circuits (which are decomposed and
transpiled into pulses) and low-level quantum programs, which are represented by the :class:`~qililab.QProgram` class.

The :class:`~qililab.QProgram` class is a hardware-agnostic representation of a quantum FPGA program. It allows you to
define a set of operations that will be executed in real time by the FPGA of your choice.

.. note::

    Qililab is currently compatible with Qblox hardware, and we are actively in the process of expanding
    its compatibility to include Quantum Machines.
