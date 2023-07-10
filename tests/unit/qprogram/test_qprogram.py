from collections import deque

import numpy as np
import pytest

from qililab.qprogram import QProgram
from qililab.qprogram.blocks.acquire_loop import AcquireLoop
from qililab.qprogram.blocks.block import Block
from qililab.qprogram.blocks.loop import Loop
from qililab.qprogram.operations.acquire import Acquire
from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.operations.play import Play
from qililab.qprogram.operations.reset_nco_phase import ResetNCOPhase
from qililab.qprogram.operations.set_awg_gain import SetAWGGain
from qililab.qprogram.operations.set_awg_offset import SetAWGOffset
from qililab.qprogram.operations.set_nco_frequency import SetNCOFrequency
from qililab.qprogram.operations.set_nco_phase import SetNCOPhase
from qililab.qprogram.operations.sync import Sync
from qililab.qprogram.operations.wait import Wait
from qililab.qprogram.variable import FloatVariable, IntVariable, Variable
from qililab.waveforms import IQPair, Square


class TestQProgram:
    """Unit tests checking the QProgram attributes and methods"""

    def test_init(self):
        """Test init method"""
        with QProgram() as qp:
            # __enter__
            assert isinstance(qp.program, Block)
            assert len(qp.program.elements) == 0
            assert isinstance(qp._block_stack, deque)
            assert len(qp._block_stack) == 1
            assert isinstance(qp.variables, list)
            assert len(qp.variables) == 0

        # __exit__
        assert len(qp._block_stack) == 0

    def test_active_block_property(self):
        """Test _active_block property"""
        with QProgram() as qp:
            # __enter__
            assert isinstance(qp._active_block, Block)
            assert qp._active_block is qp.program

    def test_block_method(self):
        """Test block method"""
        with QProgram() as qp:
            with qp.block() as block:
                # __enter__
                assert isinstance(block, Block)
                assert qp._active_block is block
            # __exit__
            assert len(qp.program.elements) == 1
            assert qp.program.elements[0] is block

    def test_loop_method(self):
        """Test loop method"""
        with QProgram() as qp:
            variable = qp.variable(int)
            values = np.ones(10, dtype=int)
            with qp.loop(variable=variable, values=values) as loop:
                # __enter__
                assert isinstance(loop, Loop)
                assert loop.variable == variable
                assert np.array_equal(loop.values, values)
                assert qp._active_block is loop
            # __exit__
            assert len(qp.program.elements) == 1
            assert qp.program.elements[0] is loop
            assert qp._active_block is qp.program

    def test_acquire_loop_method(self):
        """Test acquire_loop method"""
        with QProgram() as qp:
            with qp.acquire_loop(iterations=1000, bins=10) as loop:
                # __enter__
                assert isinstance(loop, AcquireLoop)
                assert loop.iterations == 1000
                assert loop.bins == 10
                assert qp._active_block is loop
            # __exit__
            assert len(qp.program.elements) == 1
            assert qp.program.elements[0] is loop
            assert qp._active_block is qp.program

    def test_play_method(self):
        """Test play method"""
        one_wf = Square(amplitude=1.0, duration=40, resolution=1)
        zero_wf = Square(amplitude=0.0, duration=40, resolution=1)
        with QProgram() as qp:
            # __enter__
            qp.play(bus="flux", waveform=one_wf)
            qp.play(bus="drive", waveform=IQPair(I=one_wf, Q=zero_wf))
            assert len(qp._active_block.elements) == 2
        # __exit__
        assert len(qp.program.elements) == 2
        assert isinstance(qp.program.elements[0], Play)
        assert qp.program.elements[0].bus == "flux"
        assert np.equal(qp.program.elements[0].waveform, one_wf)
        assert isinstance(qp.program.elements[1], Play)
        assert qp.program.elements[1].bus == "drive"
        assert np.equal(qp.program.elements[1].waveform.I, one_wf)
        assert np.equal(qp.program.elements[1].waveform.Q, zero_wf)

    def test_wait_method(self):
        """Test wait method"""
        with QProgram() as qp:
            # __enter__
            qp.wait(bus="drive", time=100)
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], Wait)
        assert qp.program.elements[0].bus == "drive"
        assert qp.program.elements[0].time == 100

    def test_acquire_method(self):
        """Test acquire method"""
        one_wf = Square(amplitude=1.0, duration=40, resolution=1)
        zero_wf = Square(amplitude=0.0, duration=40, resolution=1)
        with QProgram() as qp:
            # __enter__
            qp.acquire(bus="drive", weights=IQPair(I=one_wf, Q=zero_wf))
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], Acquire)
        assert qp.program.elements[0].bus == "drive"
        assert np.equal(qp.program.elements[0].weights.I, one_wf)
        assert np.equal(qp.program.elements[0].weights.Q, zero_wf)

    def test_sync_method(self):
        """Test sync method"""
        with QProgram() as qp:
            # __enter__
            qp.sync(buses=["drive", "flux"])
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], Sync)
        assert qp.program.elements[0].buses == ["drive", "flux"]

    def test_reset_nco_phase(self):
        """Test reset_nco_phase method"""
        with QProgram() as qp:
            # __enter__
            qp.reset_nco_phase(bus="drive")
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], ResetNCOPhase)
        assert qp.program.elements[0].bus == "drive"

    def test_set_nco_phase(self):
        """Test set_nco_phase method"""
        with QProgram() as qp:
            # __enter__
            qp.set_nco_phase(bus="drive", phase=2 * np.pi)
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], SetNCOPhase)
        assert qp.program.elements[0].bus == "drive"
        assert qp.program.elements[0].phase == 2 * np.pi

    def test_set_nco_frequency(self):
        """Test set_nco_frequency method"""
        with QProgram() as qp:
            # __enter__
            qp.set_nco_frequency(bus="drive", frequency=1e6)
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], SetNCOFrequency)
        assert qp.program.elements[0].bus == "drive"
        assert qp.program.elements[0].frequency == 1e6

    def test_set_awg_gain(self):
        """Test set_awg_gain method"""
        with QProgram() as qp:
            # __enter__
            qp.set_awg_gain(bus="drive", gain_path0=1.0, gain_path1=0.0)
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], SetAWGGain)
        assert qp.program.elements[0].bus == "drive"
        assert qp.program.elements[0].gain_path0 == 1.0
        assert qp.program.elements[0].gain_path1 == 0.0

    def test_set_awg_offset(self):
        """Test set_awg_offset method"""
        with QProgram() as qp:
            # __enter__
            qp.set_awg_offset(bus="drive", offset_path0=1.0, offset_path1=0.0)
            assert len(qp._active_block.elements) == 1
        # __exit__
        assert len(qp.program.elements) == 1
        assert isinstance(qp.program.elements[0], SetAWGOffset)
        assert qp.program.elements[0].bus == "drive"
        assert qp.program.elements[0].offset_path0 == 1.0
        assert qp.program.elements[0].offset_path1 == 0.0

    def test_variable_method(self):
        """Test variable method"""
        with QProgram() as qp:
            # __enter__
            int_variable = qp.variable(int)
            float_variable = qp.variable(float)
            assert isinstance(int_variable, int)
            assert isinstance(int_variable, IntVariable)
            assert int_variable == 0
            assert str(int_variable) == "0"
            assert isinstance(float_variable, float)
            assert isinstance(float_variable, FloatVariable)
            assert float_variable == 0.0
            assert str(float_variable) == "0.0"
            assert len(qp.variables) == 2
            assert qp.variables[0] is int_variable
            assert qp.variables[1] is float_variable
        # __exit__
        assert len(qp.variables) == 2
