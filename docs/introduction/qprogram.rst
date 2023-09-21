QProgram
=========

:class:`.QProgram` is a hardware-agnostic programming interface for describing quantum programs. It provides an intuitive API that simplifies the process of defining quantum operations, managing variables, and orchestrating the execution flow of quantum algorithms.

Blocks and Operations
-----------------------

Central to `QProgram`` is the :class:`Block` class, a versatile container designed to hold a sequence of quantum operations. These operations range from pulse manipulations like `Play` to data acquisition like `Acquire`. Each operation can be parameterized using variables, offering unparalleled control over the quantum program's behavior. All blocks and operations are exposed through methods.

Variable Management
---------------------

The `variable` method in QProgram allows for the dynamic declaration of variables of either `int` or `float` types. These variables can be utilized to parameterize quantum operations, thereby facilitating easy adjustments and iterations over different experimental configurations. For instance, you can define a `float` variable for amplitude and use it in a Play operation, allowing you to easily change the amplitude of the waveform.

Loops
-------

QProgram offers a rich set of control structures, including various types of loops. The `loop` method enables you to iterate over an array of values for a given variable. This is particularly useful for sweeping over a range of parameters in an experiment. Similarly, the `for_loop` method provides a more traditional loop structure, allowing you to specify the `start`, `stop`, and `step` values for a variable, thereby creating a range over which the loop will iterate. Additionally, loops can be nested, which is invaluable for experiments that require multi-dimensional sweeps. Finally, the `parallel` method is provided, which allows multiple loops to be run in parallel.

Synchronization and Timing
----------------------------

The sync operation in QProgram is a powerful feature for experiments requiring precise timing. It ensures that all operations across specified buses are synchronized, allowing for a coordinated start. This is crucial in multi-qubit experiments where the timing between different qubit operations must be exact to achieve the desired quantum state.

Waveforms
------------------------------

QProgram's play method is a versatile function that allows you to play either a singular waveform or an I/Q pair of waveforms on a designated bus. This provides granular control over the signal's amplitude, frequency, and phase. You can even use custom waveforms, making it adaptable for a wide range of quantum experiments.

Acquisition and Real-Time Averaging
--------------------------------------

The average and acquire methods in QProgram are designed for experiments that require real-time data analysis. The average method performs real-time averaging over a specified number of shots, providing immediate feedback for optimizing parameters. The acquire method allows for data collection based on either a set duration or a set of weights, offering flexibility in how you gather and interpret your data.

AWG and NCO manipulation
----------------------------

For those looking to fine-tune their quantum experiments, QProgram offers advanced operations like :meth:`.set_phase`, :meth:`.set_frequency`, set_gain, and set_offset. These methods allow you to make real-time adjustments to the Numerically Controlled Oscillator (NCO) and the Arbitrary Waveform Generator (AWG) associated with a specific bus, providing an extra layer of control.
