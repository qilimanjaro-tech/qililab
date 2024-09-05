import os
from collections import deque
from itertools import product

import numpy as np
import pytest

from qililab import Arbitrary, Domain, DragCorrection, Gaussian, IQPair, QProgram, Square
from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.operations import ExecuteQProgram, SetParameter
from qililab.qprogram.structured_program import StructuredProgram
from qililab.qprogram.variable import FloatVariable, IntVariable
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


# pylint: disable=maybe-no-member, protected-access
class TestStructuredProgram:
    """Unit tests checking the QProgram attributes and methods"""

    @pytest.fixture
    def instance(self):
        return StructuredProgram()

    def test_init(self, instance):
        """Test init method"""
        assert isinstance(instance._body, Block)
        assert len(instance._body.elements) == 0
        assert isinstance(instance._block_stack, deque)
        assert len(instance._block_stack) == 1
        assert isinstance(instance._variables, list)
        assert len(instance._variables) == 0

    def test_active_block_property(self, instance):
        """Test _active_block property"""
        assert isinstance(instance._active_block, Block)
        assert instance._active_block is instance._body

    def test_block_method(self, instance):
        """Test block method"""
        with instance.block() as block:
            # __enter__
            assert isinstance(block, Block)
            assert instance._active_block is block
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is block

    def test_infinite_loop_method(self, instance):
        """Test infinite_loop method"""
        with instance.infinite_loop() as loop:
            # __enter__
            assert isinstance(loop, InfiniteLoop)
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_parallel_method(self, instance):
        """Test parallel method"""
        var1 = instance.variable(Domain.Scalar, int)
        var2 = instance.variable(Domain.Scalar, float)
        with instance.parallel(
            loops=[
                ForLoop(variable=var1, start=0, stop=10, step=1),
                ForLoop(variable=var2, start=0.0, stop=1.0, step=0.1),
            ]
        ) as loop:
            # __enter__
            assert isinstance(loop, Parallel)
            assert len(loop.loops) == 2
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_for_loop_method(self, instance):
        """Test loop method"""
        variable = instance.variable(Domain.Scalar, int)
        start, stop, step = 0, 100, 5
        with instance.for_loop(variable=variable, start=start, stop=stop, step=step) as loop:
            # __enter__
            assert isinstance(loop, ForLoop)
            assert loop.variable == variable
            assert loop.start == start
            assert loop.stop == stop
            assert loop.step == step
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_loop_method(self, instance):
        """Test loop method"""
        variable = instance.variable(Domain.Scalar, int)
        values = np.ones(10, dtype=int)
        with instance.loop(variable=variable, values=values) as loop:
            # __enter__
            assert isinstance(loop, Loop)
            assert loop.variable == variable
            assert np.array_equal(loop.values, values)
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_variable_method(self, instance):
        """Test variable method"""
        frequency_variable = instance.variable(Domain.Frequency)
        phase_variable = instance.variable(Domain.Phase)
        voltage_variable = instance.variable(Domain.Voltage)
        time_variable = instance.variable(Domain.Time)
        int_scalar_variable = instance.variable(Domain.Scalar, int)
        float_scalar_variable = instance.variable(Domain.Scalar, float)

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
        assert len(instance._variables) == 6

    def test_variable_method_raises_error_if_domain_is_scalar_and_type_is_none(self, instance):
        """Test variable method"""
        with pytest.raises(ValueError, match="You must specify a type in a scalar variable."):
            instance.variable(Domain.Scalar)

    def test_variable_method_raises_error_if_domain_is_not_scalar_and_type_is_set(self, instance):
        """Test variable method"""
        with pytest.raises(
            ValueError, match="When declaring a variable of a specific domain, its type is inferred by its domain."
        ):
            instance.variable(Domain.Frequency, int)