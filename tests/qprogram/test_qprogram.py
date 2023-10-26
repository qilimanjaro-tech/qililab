import math
from collections import deque

import numpy as np
import pytest

from qililab import Domain, IQPair, QProgram, Square
from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.operations import (
    Acquire,
    Measure,
    Operation,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.variable import FloatVariable, IntVariable

# pylint: disable=maybe-no-member


class TestQProgram:
    """Unit tests checking the QProgram attributes and methods"""

    def test_init(self):
        """Test init method"""
        qp = QProgram()
        assert isinstance(qp._program, Block)
        assert len(qp._program.elements) == 0
        assert isinstance(qp._block_stack, deque)
        assert len(qp._block_stack) == 1
        assert isinstance(qp._variables, list)
        assert len(qp._variables) == 0

    def test_active_block_property(self):
        """Test _active_block property"""
        qp = QProgram()
        assert isinstance(qp._active_block, Block)
        assert qp._active_block is qp._program

    def test_block_method(self):
        """Test block method"""
        qp = QProgram()
        with qp.block() as block:
            # __enter__
            assert isinstance(block, Block)
            assert qp._active_block is block
        # __exit__
        assert len(qp._program.elements) == 1
        assert qp._program.elements[0] is block

    def test_for_loop_method(self):
        """Test loop method"""
        qp = QProgram()
        variable = qp.variable(Domain.Scalar, int)
        start, stop, step = 0, 100, 5
        with qp.for_loop(variable=variable, start=start, stop=stop, step=step) as loop:
            # __enter__
            assert isinstance(loop, ForLoop)
            assert loop.variable == variable
            assert loop.start == start
            assert loop.stop == stop
            assert loop.step == step
            assert qp._active_block is loop
        # __exit__
        assert len(qp._program.elements) == 1
        assert qp._program.elements[0] is loop
        assert qp._active_block is qp._program

    def test_loop_method(self):
        """Test loop method"""
        qp = QProgram()
        variable = qp.variable(Domain.Scalar, int)
        values = np.ones(10, dtype=int)
        with qp.loop(variable=variable, values=values) as loop:
            # __enter__
            assert isinstance(loop, Loop)
            assert loop.variable == variable
            assert np.array_equal(loop.values, values)
            assert qp._active_block is loop
        # __exit__
        assert len(qp._program.elements) == 1
        assert qp._program.elements[0] is loop
        assert qp._active_block is qp._program

    def test_acquire_loop_method(self):
        """Test acquire_loop method"""
        qp = QProgram()
        with qp.average(shots=1000) as loop:
            # __enter__
            assert isinstance(loop, Average)
            assert loop.shots == 1000
            assert qp._active_block is loop
        # __exit__
        assert len(qp._program.elements) == 1
        assert qp._program.elements[0] is loop
        assert qp._active_block is qp._program

    def test_play_method(self):
        """Test play method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        qp.play(bus="flux", waveform=one_wf)
        qp.play(bus="drive", waveform=IQPair(I=one_wf, Q=zero_wf))

        assert len(qp._active_block.elements) == 2
        assert len(qp._program.elements) == 2
        assert isinstance(qp._program.elements[0], Play)
        assert qp._program.elements[0].bus == "flux"
        assert np.equal(qp._program.elements[0].waveform, one_wf)
        assert isinstance(qp._program.elements[1], Play)
        assert qp._program.elements[1].bus == "drive"
        assert np.equal(qp._program.elements[1].waveform.I, one_wf)
        assert np.equal(qp._program.elements[1].waveform.Q, zero_wf)

    def test_wait_method(self):
        """Test wait method"""
        qp = QProgram()
        qp.wait(bus="drive", duration=100)

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], Wait)
        assert qp._program.elements[0].bus == "drive"
        assert qp._program.elements[0].duration == 100

    def test_acquire_method_with_weights(self):
        """Test acquire method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        qp.acquire(bus="drive", weights=IQPair(I=one_wf, Q=zero_wf))

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], Acquire)
        assert qp._program.elements[0].bus == "drive"
        assert np.equal(qp._program.elements[0].weights.I, one_wf)
        assert np.equal(qp._program.elements[0].weights.Q, zero_wf)

    def test_sync_method(self):
        """Test sync method"""
        qp = QProgram()
        qp.sync(buses=["drive", "flux"])

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], Sync)
        assert qp._program.elements[0].buses == ["drive", "flux"]

    def test_reset_nco_phase(self):
        """Test reset_nco_phase method"""
        qp = QProgram()
        qp.reset_phase(bus="drive")

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], ResetPhase)
        assert qp._program.elements[0].bus == "drive"

    def test_set_nco_phase(self):
        """Test set_nco_phase method"""
        qp = QProgram()
        qp.set_phase(bus="drive", phase=2 * np.pi)

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], SetPhase)
        assert qp._program.elements[0].bus == "drive"
        assert qp._program.elements[0].phase == 2 * np.pi

    def test_set_nco_frequency(self):
        """Test set_nco_frequency method"""
        qp = QProgram()
        qp.set_frequency(bus="drive", frequency=1e6)

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], SetFrequency)
        assert qp._program.elements[0].bus == "drive"
        assert qp._program.elements[0].frequency == 1e6

    def test_set_awg_gain(self):
        """Test set_awg_gain method"""
        qp = QProgram()
        qp.set_gain(bus="drive", gain=1.0)

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], SetGain)
        assert qp._program.elements[0].bus == "drive"
        assert qp._program.elements[0].gain == 1.0

    def test_set_awg_offset(self):
        """Test set_awg_offset method"""
        qp = QProgram()
        qp.set_offset(bus="drive", offset_path0=1.0, offset_path1=0.0)

        assert len(qp._active_block.elements) == 1
        assert len(qp._program.elements) == 1
        assert isinstance(qp._program.elements[0], SetOffset)
        assert qp._program.elements[0].bus == "drive"
        assert qp._program.elements[0].offset_path0 == 1.0
        assert qp._program.elements[0].offset_path1 == 0.0

    def test_variable_method(self):
        """Test variable method"""
        qp = QProgram()
        frequency_variable = qp.variable(Domain.Frequency)
        phase_variable = qp.variable(Domain.Phase)
        voltage_variable = qp.variable(Domain.Voltage)
        time_variable = qp.variable(Domain.Time)
        int_scalar_variable = qp.variable(Domain.Scalar, int)
        float_scalar_variable = qp.variable(Domain.Scalar, float)

        # Test instantiation
        assert isinstance(frequency_variable, float)
        assert isinstance(frequency_variable, FloatVariable)
        assert frequency_variable.domain is Domain.Frequency
        assert frequency_variable.value is None

        assert isinstance(phase_variable, float)
        assert isinstance(phase_variable, FloatVariable)
        assert phase_variable.domain is Domain.Phase
        assert phase_variable.value is None

        assert isinstance(voltage_variable, float)
        assert isinstance(voltage_variable, FloatVariable)
        assert voltage_variable.domain is Domain.Voltage
        assert voltage_variable.value is None

        assert isinstance(time_variable, int)
        assert isinstance(time_variable, IntVariable)
        assert time_variable.domain is Domain.Time
        assert time_variable.value is None

        assert isinstance(int_scalar_variable, int)
        assert isinstance(int_scalar_variable, IntVariable)
        assert int_scalar_variable.domain is Domain.Scalar
        assert int_scalar_variable.value is None

        assert isinstance(float_scalar_variable, float)
        assert isinstance(float_scalar_variable, FloatVariable)
        assert float_scalar_variable.domain is Domain.Scalar
        assert float_scalar_variable.value is None

        # Test storing in QProgram's _variables
        assert len(qp._variables) == 6
