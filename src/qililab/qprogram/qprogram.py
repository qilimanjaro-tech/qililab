# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import deque
from copy import deepcopy
from dataclasses import replace
from typing import overload

import numpy as np

from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.operations import (
    Acquire,
    AcquireWithCalibratedWeights,
    Measure,
    MeasureWithCalibratedWaveform,
    MeasureWithCalibratedWaveformWeights,
    MeasureWithCalibratedWeights,
    Play,
    PlayWithCalibratedWaveform,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.variable import Domain, FloatVariable, IntVariable, ValueSource, Variable
from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
class QProgram:  # pylint: disable=too-many-public-methods
    """QProgram is a hardware-agnostic pulse-level programming interface for describing quantum programs.

    This class provides an interface for building quantum programs,
    including defining operations, managing variables, and handling blocks.
    It contains methods for creating, manipulating and controlling
    the execution flow of quantum operations within a program.

    Examples:

        The following example illustrates how to define a Rabi sequence using QProgram.

        .. code-block:: python3

            from qililab import QProgram, Domain, IQPair, Square

            qp = QProgram()

            # Pulse used for changing the state of qubit
            control_wf = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4.0, drag_correction=-2.5)

            # Pulse used for exciting the resonator for readout
            readout_wf = IQPair(I=Square(amplitude=1.0, duration=400), Q=Square(amplitude=0.0, duration=400))

            # Weights used during integration
            weights = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=1.0, duration=2000))

            # Declare a variable
            gain = qp.variable(Domain.Voltage)

            # Loop the variable's value over the range [0.0, 1.0]
            with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.01):
                # Change the gain output of the drive_bus
                qp.set_gain(bus="drive_bus", gain=gain)

                # Play the control pulse
                qp.play(bus="drive_bus", waveform=control_wf)

                # Sync the buses
                qp.sync()

                # Measure
                qp.measure(bus="readout_bus", waveform=readout_wf, weights=weights)

    """

    def __init__(self) -> None:
        self.qblox = self._QbloxInterface(self)
        self.quantum_machines = self._QuantumMachinesInterface(self)

        self._body: Block = Block()
        self._buses: set[str] = set()
        self._variables: list[Variable] = []
        self._block_stack: deque[Block] = deque([self._body])

    def _append_to_block_stack(self, block: Block):
        self._block_stack.append(block)

    def _pop_from_block_stack(self):
        return self._block_stack.pop()

    @property
    def body(self) -> Block:
        """Get the body of the QProgram

        Returns:
            Block: The block of the body
        """
        return self._body

    @property
    def buses(self) -> set[str]:
        """Get the buses of the QProgram

        Returns:
            set[str]: A set of the names of the buses
        """
        return self._buses

    @property
    def variables(self) -> list[Variable]:
        """Get the variables

        Returns:
            list[Variable]: A list of variables
        """
        return self._variables

    @property
    def _active_block(self) -> Block:
        return self._block_stack[-1]

    def has_calibrated_waveforms_or_weights(self) -> bool:
        """Checks if QProgram has named waveforms or weights. These need to be mapped before compiling to hardware-native code.

        Returns:
            bool: True, if QProgram has waveforms or weights that need to be mapped from calibration.
        """

        def traverse(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    if traverse(element):
                        return True
                elif isinstance(
                    element,
                    (
                        PlayWithCalibratedWaveform,
                        AcquireWithCalibratedWeights,
                        MeasureWithCalibratedWaveform,
                        MeasureWithCalibratedWeights,
                        MeasureWithCalibratedWaveformWeights,
                    ),
                ):
                    return True
            return False

        return traverse(self.body)

    def with_bus_mapping(self, bus_mapping: dict[str, str]) -> "QProgram":
        """Returns a copy of the QProgram with bus mappings applied.

        Args:
            bus_mapping (dict[str, str]): A dictionary mapping old bus names to new bus names.

        Returns:
            QProgram: A new instance of QProgram with updated bus names.
        """

        def traverse(block: Block):
            for index, element in enumerate(block.elements):
                if isinstance(element, Block):
                    traverse(element)
                elif hasattr(element, "bus"):
                    bus = getattr(element, "bus")
                    if isinstance(bus, str) and bus in bus_mapping:
                        block.elements[index] = replace(block.elements[index], bus=bus_mapping[bus])  # type: ignore[call-arg]
                elif hasattr(element, "buses"):
                    buses = getattr(element, "buses")
                    if isinstance(buses, list):
                        block.elements[index] = replace(block.elements[index], buses=[bus_mapping[bus] if bus in bus_mapping else bus for bus in buses])  # type: ignore[call-arg]

        # Copy qprogram so the original remain unaffected
        copied_qprogram = deepcopy(self)

        # Recursively traverse qprogram applying the bus mapping
        traverse(copied_qprogram.body)

        # Apply the mapping to buses property
        for bus in list(copied_qprogram.buses):
            if bus in bus_mapping:
                copied_qprogram.buses.remove(bus)
                copied_qprogram.buses.add(bus_mapping[bus])

        return copied_qprogram

    def with_calibration(self, calibration: Calibration):
        """Apply calibration to the operations within the QProgram.

        This method traverses the elements of the QProgram, replacing any
        named operations with the corresponding calibrated waveforms specified
        in the given Calibration instance.

        Args:
            calibration (Calibration): The calibration data to apply to the operations.

        Returns:
            QProgram: A new instance of QProgram with calibrated operations.
        """

        def traverse(block: Block):
            for index, element in enumerate(block.elements):
                if isinstance(element, Block):
                    traverse(element)
                elif isinstance(element, PlayWithCalibratedWaveform) and calibration.has_waveform(
                    bus=element.bus, name=element.waveform
                ):
                    waveform = calibration.get_waveform(bus=element.bus, name=element.waveform)
                    play_operation = Play(bus=element.bus, waveform=waveform, wait_time=element.wait_time)
                    block.elements[index] = play_operation
                elif isinstance(element, AcquireWithCalibratedWeights) and calibration.has_weights(
                    bus=element.bus, name=element.weights
                ):
                    weights = calibration.get_weights(bus=element.bus, name=element.weights)
                    acquire_operation = Acquire(bus=element.bus, weights=weights, save_adc=element.save_adc)
                    block.elements[index] = acquire_operation
                elif isinstance(element, MeasureWithCalibratedWaveform) and calibration.has_waveform(
                    bus=element.bus, name=element.waveform
                ):
                    waveform = calibration.get_waveform(bus=element.bus, name=element.waveform)
                    measure_operation = Measure(
                        bus=element.bus,
                        waveform=waveform,
                        weights=element.weights,
                        demodulation=element.demodulation,
                        save_adc=element.save_adc,
                    )
                    block.elements[index] = measure_operation
                elif isinstance(element, MeasureWithCalibratedWeights) and calibration.has_weights(
                    bus=element.bus, name=element.weights
                ):
                    weights = calibration.get_weights(bus=element.bus, name=element.weights)
                    measure_operation = Measure(
                        bus=element.bus,
                        waveform=element.waveform,
                        weights=weights,
                        demodulation=element.demodulation,
                        save_adc=element.save_adc,
                    )
                    block.elements[index] = measure_operation
                elif (
                    isinstance(element, MeasureWithCalibratedWaveformWeights)
                    and calibration.has_waveform(bus=element.bus, name=element.waveform)
                    and calibration.has_weights(bus=element.bus, name=element.weights)
                ):
                    waveform = calibration.get_waveform(bus=element.bus, name=element.waveform)
                    weights = calibration.get_weights(bus=element.bus, name=element.weights)
                    measure_operation = Measure(
                        bus=element.bus,
                        waveform=waveform,
                        weights=weights,
                        demodulation=element.demodulation,
                        save_adc=element.save_adc,
                    )
                    block.elements[index] = measure_operation

        copied_qprogram = deepcopy(self)
        traverse(copied_qprogram.body)
        return copied_qprogram

    def block(self):
        """Define a generic block for scoping operations.

        Blocks need to open a scope.

        Returns:
            Block: The block.

        Examples:

            >>> with qp.block() as block:
            >>>    # operations that shall be executed in the block
        """
        return QProgram._BlockContext(qprogram=self)

    def parallel(self, loops: list[Loop | ForLoop]):
        """Define a block for running multiple loops in parallel.

        Blocks need to open a scope.

        Examples:
            >>> gain = qp.variable(float)
            >>> frequency = qp.variable(float)
            >>> with qp.parallel(loops=[ForLoop(variable=frequency, start=0, stop=100, step=10),
                                        ForLoop(variable=gain, start=0.0, stop=1.0, step=0.1)]):
            >>>    # operations that shall be executed in the block

        Args:
            loops (list[Loop  |  ForLoop]): The loops to run in parallel

        Returns:
            Parallel: The parallel block.
        """
        return QProgram._ParallelContext(qprogram=self, loops=loops)

    def average(self, shots: int):
        """Define an acquire loop block with averaging in real time.

        Blocks need to open a scope.

        Args:
            iterations (int): The number of acquire iterations.

        Returns:
            Average: The average block.

        Examples:

            >>> with qp.average(shots=1000):
            >>>    # operations that shall be executed in the average block
        """
        return QProgram._AverageContext(qprogram=self, shots=shots)

    def infinite_loop(self):
        """Define an infinite loop.

        Blocks need to open a scope.

        Examples:

            >>> with qp.infinite_loop():
            >>>    # operations that shall be executed in the infinite loop block

        Returns:
            InfiniteLoop: The infinite loop block.
        """
        return QProgram._InfiniteLoopContext(qprogram=self)

    def loop(self, variable: Variable, values: np.ndarray):
        """Define a loop block to iterate values over a variable.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            values (np.ndarray): The values to iterate over.

        Returns:
            Loop: The loop block.

        Examples:

            >>> variable = qp.variable(int)
            >>> with qp.loop(variable=variable, values=np.array(range(100))):
            >>>    # operations that shall be executed in the loop block
        """

        return QProgram._LoopContext(qprogram=self, variable=variable, values=values)

    def for_loop(self, variable: Variable, start: int | float, stop: int | float, step: int | float = 1):
        """Define a for_loop block to iterate values over a variable.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            start (int | float): The start value.
            stop (int | float): The stop value.
            step (int | float, optional): The step value. Defaults to 1.

        Returns:
            Loop: The loop block.

        Examples:

            >>> variable = qp.variable(int)
            >>> with qp.for_loop(variable=variable, start=0, stop=100, step=5)):
            >>>    # operations that shall be executed in the for_loop block
        """

        return QProgram._ForLoopContext(qprogram=self, variable=variable, start=start, stop=stop, step=step)

    @overload
    def play(self, bus: str, waveform: Waveform | IQPair) -> None:
        """Play a single waveform or an I/Q pair of waveforms on the bus.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (Waveform | IQPair): A single waveform or an I/Q pair of waveforms
        """

    @overload
    def play(self, bus: str, waveform: str) -> None:
        """Play a named waveform on the bus.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (str): An identifier of a named waveform.
        """

    def play(self, bus: str, waveform: Waveform | IQPair | str) -> None:
        """Play a waveform, IQPair, or calibrated operation on the specified bus.

        This method handles both playing a waveform or IQPair, and playing a
        calibrated operation based on the type of the argument provided.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (Waveform | IQPair | str): The waveform, IQPair, or alias of named waveform to play.
        """
        operation = (
            PlayWithCalibratedWaveform(bus=bus, waveform=waveform)
            if isinstance(waveform, str)
            else Play(bus=bus, waveform=waveform)
        )
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("duration", Domain.Time)
    def wait(self, bus: str, duration: int):
        """Adds a delay on the bus with a specified time.

        Args:
            bus (str): Unique identifier of the bus.
            time (int): Duration of the delay.
        """
        operation = Wait(bus=bus, duration=duration)
        self._active_block.append(operation)
        self._buses.add(bus)

    @overload
    def measure(self, bus: str, waveform: IQPair, weights: IQPair, save_adc: bool = False):
        """Play a pulse and acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (IQPair): Waveform played during measurement.
            weights (IQPair): Weights used during demodulation/integration.
            save_adc (bool, optional): If ADC data should be saved. Defaults to False.
        """

    @overload
    def measure(self, bus: str, waveform: str, weights: IQPair, save_adc: bool = False):
        """Play a named pulse and acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (str): Waveform played during measurement.
            weights (IQPair): Weights used during demodulation/integration.
            save_adc (bool, optional): If ADC data should be saved. Defaults to False.
        """

    @overload
    def measure(self, bus: str, waveform: IQPair, weights: str, save_adc: bool = False):
        """Play a named pulse and acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (IQPair): Waveform played during measurement.
            weights (str): Weights used during demodulation/integration.
            save_adc (bool, optional): If ADC data should be saved. Defaults to False.
        """

    @overload
    def measure(self, bus: str, waveform: str, weights: str, save_adc: bool = False):
        """Play a named pulse and acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (str): Waveform played during measurement.
            weights (str): Weights used during demodulation/integration.
            save_adc (bool, optional): If ADC data should be saved. Defaults to False.
        """

    def measure(self, bus: str, waveform: IQPair | str, weights: IQPair | str, save_adc: bool = False):
        """Play a pulse and acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (IQPair): Waveform played during measurement.
            weights (IQPair): Weights used during demodulation/integration.
            save_adc (bool, optional): If ADC data should be saved. Defaults to False.
        """
        operation: Measure | MeasureWithCalibratedWaveform | MeasureWithCalibratedWeights | MeasureWithCalibratedWaveformWeights
        if isinstance(waveform, IQPair) and isinstance(weights, IQPair):
            operation = Measure(bus=bus, waveform=waveform, weights=weights, save_adc=save_adc)
        elif isinstance(waveform, str) and isinstance(weights, IQPair):
            operation = MeasureWithCalibratedWaveform(bus=bus, waveform=waveform, weights=weights, save_adc=save_adc)
        elif isinstance(waveform, IQPair) and isinstance(weights, str):
            operation = MeasureWithCalibratedWeights(bus=bus, waveform=waveform, weights=weights, save_adc=save_adc)
        elif isinstance(waveform, str) and isinstance(weights, str):
            operation = MeasureWithCalibratedWaveformWeights(
                bus=bus, waveform=waveform, weights=weights, save_adc=save_adc
            )
        self._active_block.append(operation)
        self._buses.add(bus)

    def sync(self, buses: list[str] | None = None):
        """Synchronize operations between buses, so the operations following will start at the same time.

        If no buses are given, then the synchronization will involve all buses present in the QProgram.

        Args:
            buses (list[str] | None, optional): List of unique identifiers of the buses. Defaults to None.
        """
        operation = Sync(buses=buses)
        self._active_block.append(operation)
        if buses:
            self._buses.update(buses)

    def reset_phase(self, bus: str):
        """Reset the absolute phase of the NCO associated with the bus.

        Args:
            bus (str): Unique identifier of the bus.
        """
        operation = ResetPhase(bus=bus)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("phase", Domain.Phase)
    def set_phase(self, bus: str, phase: float):
        """Set the absolute phase of the NCO associated with the bus.

        Args:
            bus (str): Unique identifier of the bus.
            phase (float): The new absolute phase of the NCO.
        """
        operation = SetPhase(bus=bus, phase=phase)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("frequency", Domain.Frequency)
    def set_frequency(self, bus: str, frequency: float):
        """Set the frequency of the NCO associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            frequency (float): The new frequency of the NCO.
        """
        operation = SetFrequency(bus=bus, frequency=frequency)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("gain", Domain.Voltage)
    def set_gain(self, bus: str, gain: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            gain (float): The new gain of the AWG.
        """
        operation = SetGain(bus=bus, gain=gain)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("offset_path0", Domain.Voltage)
    @requires_domain("offset_path1", Domain.Voltage)
    def set_offset(self, bus: str, offset_path0: float, offset_path1: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            offset_path0 (float): The new offset of the AWG for path0.
            offset_path1 (float): The new offset of the AWG for path1.
        """
        operation = SetOffset(bus=bus, offset_path0=offset_path0, offset_path1=offset_path1)
        self._active_block.append(operation)
        self._buses.add(bus)

    def variable(self, domain: Domain, type: type[int | float] | None = None):  # pylint: disable=redefined-builtin
        """Declare a variable.

        Args:
            type (int | float): The type of the variable.

        Raises:
            NotImplementedError: If an unsupported type is provided.

        Returns:
            IntVariable | FloatVariable: The variable.
        """

        def _int_variable(domain: Domain = Domain.Scalar) -> IntVariable:
            variable = IntVariable(domain)
            self._variables.append(variable)
            return variable

        def _float_variable(domain: Domain = Domain.Scalar) -> FloatVariable:
            variable = FloatVariable(domain)
            self._variables.append(variable)
            return variable

        if domain is Domain.Scalar and type is None:
            raise ValueError("You must specify a type in a scalar variable.")
        if domain is not Domain.Scalar and type is not None:
            raise ValueError("When declaring a variable of a specific domain, its type is inferred by its domain.")

        if domain is Domain.Scalar:
            if type == int:
                return _int_variable(domain)
            if type == float:
                return _float_variable(domain)

        if domain == Domain.Time:
            return _int_variable(domain)
        if domain in [Domain.Frequency, Domain.Phase, Domain.Voltage]:
            return _float_variable(domain)
        raise NotImplementedError

    class _BlockContext:
        def __init__(self, qprogram: "QProgram"):
            self.qprogram = qprogram
            self.block: Block = Block()

        def __enter__(self):
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.qprogram._pop_from_block_stack()
            self.qprogram._active_block.append(block)

    class _InfiniteLoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram"):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: InfiniteLoop = InfiniteLoop()

    class _ParallelContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram", loops: list[Loop | ForLoop]):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: Parallel = Parallel(loops=loops)

        def __enter__(self) -> Parallel:
            for loop in self.block.loops:
                loop.variable._source = ValueSource.Dependent
                loop.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            for loop in self.block.loops:
                loop.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)

    class _LoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, qprogram: "QProgram", variable: Variable, values: np.ndarray
        ):
            self.qprogram = qprogram
            self.block: Loop = Loop(variable=variable, values=values)

        def __enter__(self) -> Loop:
            self.block.variable._source = ValueSource.Dependent
            self.block.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.block.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)

    class _ForLoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, qprogram: "QProgram", variable: Variable, start: int | float, stop: int | float, step: int | float
        ):
            self.qprogram = qprogram
            self.block: ForLoop = ForLoop(variable=variable, start=start, stop=stop, step=step)

        def __enter__(self) -> ForLoop:
            self.block.variable._source = ValueSource.Dependent
            self.block.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.block.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)

    class _AverageContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram", shots: int):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: Average = Average(shots=shots)

    # pylint: disable=protected-access, too-few-public-methods
    @yaml.register_class
    class _QbloxInterface:
        def __init__(self, qprogram: "QProgram"):
            self.qprogram = qprogram
            self.disable_autosync: bool = False

        @overload
        def acquire(self, bus: str, weights: IQPair, save_adc: bool = False):
            """Acquire results based on the given weights.

            Args:
                bus (str): Unique identifier of the bus.
                weights (IQPair): Weights used during acquisition.
            """

        @overload
        def acquire(self, bus: str, weights: str, save_adc: bool = False):
            """Acquire results based on the given weights.

            Args:
                bus (str): Unique identifier of the bus.
                weights (str): Weights used during acquisition.
            """

        def acquire(self, bus: str, weights: IQPair | str, save_adc: bool = False):
            """Acquire results based on the given weights.

            Args:
                bus (str): Unique identifier of the bus.
                weights (IQPair | str): Weights used during acquisition.
            """
            operation = (
                Acquire(bus=bus, weights=weights, save_adc=save_adc)
                if isinstance(weights, IQPair)
                else AcquireWithCalibratedWeights(bus=bus, weights=weights, save_adc=save_adc)
            )
            self.qprogram._active_block.append(operation)
            self.qprogram._buses.add(bus)

        @overload
        def play(self, bus: str, waveform: Waveform | IQPair, wait_time: int) -> None:
            """Play a single waveform or an I/Q pair of waveforms on the bus.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (Waveform | IQPair): A single waveform or an I/Q pair of waveforms
            """

        @overload
        def play(self, bus: str, waveform: str, wait_time: int) -> None:
            """Play a named waveform on the bus.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (str): An identifier of a named waveform.
            """

        def play(self, bus: str, waveform: Waveform | IQPair | str, wait_time: int) -> None:
            """Play a waveform, IQPair, or calibrated operation on the specified bus.

            This method handles both playing a waveform or IQPair, and playing a
            calibrated operation based on the type of the argument provided.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (Waveform | IQPair | str): The waveform, IQPair, or alias of named waveform to play.
                wait_time (int): Overwrite the value of Q1ASM play instruction's wait_time parameter.
            """
            operation = (
                PlayWithCalibratedWaveform(bus=bus, waveform=waveform, wait_time=wait_time)
                if isinstance(waveform, str)
                else Play(bus=bus, waveform=waveform, wait_time=wait_time)
            )
            self.qprogram._active_block.append(operation)
            self.qprogram._buses.add(bus)

    # pylint: disable=protected-access, too-few-public-methods
    @yaml.register_class
    class _QuantumMachinesInterface:
        def __init__(self, qprogram: "QProgram"):
            self.qprogram = qprogram

        @overload
        def measure(
            self,
            bus: str,
            waveform: IQPair,
            weights: IQPair,
            save_adc: bool = False,
            rotation: float = 0.0,
            demodulation: bool = True,
        ):
            """Play a pulse and acquire results.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (IQPair): Waveform played during measurement.
                weights (IQPair): Weights used during demodulation/integration.
                save_adc (bool, optional): If ADC data should be saved. Defaults to False.
                rotation (float, optional): Angle in radians to rotate the IQ plane during demodulation/integration. Defaults to 0.0
                demodulation (bool, optional): If demodulation is enabled. Defaults to True.
            """

        @overload
        def measure(
            self,
            bus: str,
            waveform: str,
            weights: IQPair,
            save_adc: bool = False,
            rotation: float = 0.0,
            demodulation: bool = True,
        ):
            """Play a named pulse and acquire results.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (str): Waveform played during measurement.
                weights (IQPair): Weights used during demodulation/integration.
                save_adc (bool, optional): If ADC data should be saved. Defaults to False.
                rotation (float, optional): Angle in radians to rotate the IQ plane during demodulation/integration. Defaults to 0.0
                demodulation (bool, optional): If demodulation is enabled. Defaults to True.
            """

        @overload
        def measure(
            self,
            bus: str,
            waveform: IQPair,
            weights: str,
            save_adc: bool = False,
            rotation: float = 0.0,
            demodulation: bool = True,
        ):
            """Play a named pulse and acquire results.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (IQPair): Waveform played during measurement.
                weights (str): Weights used during demodulation/integration.
                save_adc (bool, optional): If ADC data should be saved. Defaults to False.
                rotation (float, optional): Angle in radians to rotate the IQ plane during demodulation/integration. Defaults to 0.0
                demodulation (bool, optional): If demodulation is enabled. Defaults to True.
            """

        @overload
        def measure(
            self,
            bus: str,
            waveform: str,
            weights: str,
            save_adc: bool = False,
            rotation: float = 0.0,
            demodulation: bool = True,
        ):
            """Play a named pulse and acquire results.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (str): Waveform played during measurement.
                weights (str): Weights used during demodulation/integration.
                save_adc (bool, optional): If ADC data should be saved. Defaults to False.
                rotation (float, optional): Angle in radians to rotate the IQ plane during demodulation/integration. Defaults to 0.0
                demodulation (bool, optional): If demodulation is enabled. Defaults to True.
            """

        def measure(
            self,
            bus: str,
            waveform: IQPair | str,
            weights: IQPair | str,
            save_adc: bool = False,
            rotation: float = 0.0,
            demodulation: bool = True,
        ):
            """Play a pulse and acquire results.

            Args:
                bus (str): Unique identifier of the bus.
                waveform (IQPair): Waveform played during measurement.
                weights (IQPair): Weights used during demodulation/integration.
                save_adc (bool, optional): If raw ADC data should be saved. Defaults to False.
                rotation (float, optional): Angle in radians to rotate the IQ plane during demodulation/integration. Defaults to 0.0
                demodulation (bool, optional): If demodulation is enabled. Defaults to True.
            """
            operation: Measure | MeasureWithCalibratedWaveform | MeasureWithCalibratedWeights | MeasureWithCalibratedWaveformWeights
            if isinstance(waveform, IQPair) and isinstance(weights, IQPair):
                operation = Measure(
                    bus=bus,
                    waveform=waveform,
                    weights=weights,
                    save_adc=save_adc,
                    rotation=rotation,
                    demodulation=demodulation,
                )
            elif isinstance(waveform, str) and isinstance(weights, IQPair):
                operation = MeasureWithCalibratedWaveform(
                    bus=bus,
                    waveform=waveform,
                    weights=weights,
                    save_adc=save_adc,
                    rotation=rotation,
                    demodulation=demodulation,
                )
            elif isinstance(waveform, IQPair) and isinstance(weights, str):
                operation = MeasureWithCalibratedWeights(
                    bus=bus,
                    waveform=waveform,
                    weights=weights,
                    save_adc=save_adc,
                    rotation=rotation,
                    demodulation=demodulation,
                )
            elif isinstance(waveform, str) and isinstance(weights, str):
                operation = MeasureWithCalibratedWaveformWeights(
                    bus=bus,
                    waveform=waveform,
                    weights=weights,
                    save_adc=save_adc,
                    rotation=rotation,
                    demodulation=demodulation,
                )
            self.qprogram._active_block.append(operation)
            self.qprogram._buses.add(bus)
