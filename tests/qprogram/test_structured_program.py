from collections import deque

import numpy as np
import pytest

from qililab import Domain
from qililab.exceptions import VariableAllocated
from qililab.qprogram.blocks import Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.structured_program import StructuredProgram
from qililab.core.variables import FloatVariable, IntVariable


class TestStructuredProgram:
    """Unit tests checking the QProgram attributes and methods"""

    @pytest.fixture
    def instance(self) -> StructuredProgram:
        return StructuredProgram()

    def test_init(self, instance: StructuredProgram):
        """Test init method"""
        assert isinstance(instance._body, Block)
        assert len(instance._body.elements) == 0
        assert isinstance(instance._block_stack, deque)
        assert len(instance._block_stack) == 1
        assert isinstance(instance._variables, dict)
        assert len(instance._variables) == 0

    def test_active_block_property(self, instance: StructuredProgram):
        """Test _active_block property"""
        assert isinstance(instance._active_block, Block)
        assert instance._active_block is instance._body

    def test_block_method(self, instance: StructuredProgram):
        """Test block method"""
        with instance.block() as block:
            # __enter__
            assert isinstance(block, Block)
            assert instance._active_block is block
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is block

    def test_infinite_loop_method(self, instance: StructuredProgram):
        """Test infinite_loop method"""
        with instance.infinite_loop() as loop:
            # __enter__
            assert isinstance(loop, InfiniteLoop)
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_parallel_method(self, instance: StructuredProgram):
        """Test parallel method"""
        var1 = instance.variable(label="int_scalar", domain=Domain.Scalar, type=int)
        var2 = instance.variable(label="float_scalar", domain=Domain.Scalar, type=float)
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
            assert all(instance._variables[loop.variable].is_allocated for loop in loop.loops)
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body
        assert all(not instance._variables[loop.variable].is_allocated for loop in loop.loops)

    def test_for_loop_method(self, instance: StructuredProgram):
        """Test loop method"""
        variable = instance.variable(label="int_scalar", domain=Domain.Scalar, type=int)
        start, stop, step = 0, 100, 5
        with instance.for_loop(variable=variable, start=start, stop=stop, step=step) as loop:
            # __enter__
            assert isinstance(loop, ForLoop)
            assert loop.variable == variable
            assert loop.start == start
            assert loop.stop == stop
            assert loop.step == step
            assert instance._active_block is loop
            assert instance._variables[loop.variable].is_allocated
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body
        assert not instance._variables[loop.variable].is_allocated

    def test_loop_method(self, instance: StructuredProgram):
        """Test loop method"""
        variable = instance.variable(label="int_scalar", domain=Domain.Scalar, type=int)
        values = np.ones(10, dtype=int)
        with instance.loop(variable=variable, values=values) as loop:
            # __enter__
            assert isinstance(loop, Loop)
            assert loop.variable == variable
            assert np.array_equal(loop.values, values)
            assert instance._active_block is loop
            assert instance._variables[loop.variable].is_allocated
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body
        assert not instance._variables[loop.variable].is_allocated

    def test_loops_raise_error_if_variable_is_allocated(self, instance: StructuredProgram):
        """Test loop method"""
        variable = instance.variable(label="int_scalar", domain=Domain.Scalar, type=int)
        # test when ForLoop allocates variable
        with instance.for_loop(variable=variable, start=0, stop=10, step=1):
            with pytest.raises(VariableAllocated):
                with instance.for_loop(variable=variable, start=100, stop=110, step=1):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.loop(variable=variable, values=np.arange(10)):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.parallel(loops=[Loop(variable=variable, values=np.arange(10))]):
                    pass
        # test when Loop allocates variable
        with instance.loop(variable=variable, values=np.arange(10)):
            with pytest.raises(VariableAllocated):
                with instance.for_loop(variable=variable, start=100, stop=110, step=1):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.loop(variable=variable, values=np.arange(10)):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.parallel(loops=[Loop(variable=variable, values=np.arange(10))]):
                    pass
        # test when Parallel allocates variable
        with instance.parallel(loops=[Loop(variable=variable, values=np.arange(10))]):
            with pytest.raises(VariableAllocated):
                with instance.for_loop(variable=variable, start=100, stop=110, step=1):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.loop(variable=variable, values=np.arange(10)):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.parallel(loops=[Loop(variable=variable, values=np.arange(10))]):
                    pass

    def test_variable_method(self, instance: StructuredProgram):
        """Test variable method"""
        frequency_variable = instance.variable(label="frequency", domain=Domain.Frequency)
        phase_variable = instance.variable(label="phase", domain=Domain.Phase)
        voltage_variable = instance.variable(label="voltage", domain=Domain.Voltage)
        time_variable = instance.variable(label="time", domain=Domain.Time)
        int_scalar_variable = instance.variable(label="int_scalar", domain=Domain.Scalar, type=int)
        float_scalar_variable = instance.variable(label="float_scalar", domain=Domain.Scalar, type=float)

        # Test instantiation
        assert isinstance(frequency_variable, float)
        assert isinstance(frequency_variable, FloatVariable)
        assert frequency_variable.domain is Domain.Frequency
        assert frequency_variable.label == "frequency"

        assert isinstance(phase_variable, float)
        assert isinstance(phase_variable, FloatVariable)
        assert phase_variable.domain is Domain.Phase
        assert phase_variable.label == "phase"

        assert isinstance(voltage_variable, float)
        assert isinstance(voltage_variable, FloatVariable)
        assert voltage_variable.domain is Domain.Voltage
        assert voltage_variable.label == "voltage"

        assert isinstance(time_variable, int)
        assert isinstance(time_variable, IntVariable)
        assert time_variable.domain is Domain.Time
        assert time_variable.label == "time"

        assert isinstance(int_scalar_variable, int)
        assert isinstance(int_scalar_variable, IntVariable)
        assert int_scalar_variable.domain is Domain.Scalar
        assert int_scalar_variable.label == "int_scalar"

        assert isinstance(float_scalar_variable, float)
        assert isinstance(float_scalar_variable, FloatVariable)
        assert float_scalar_variable.domain is Domain.Scalar
        assert float_scalar_variable.label == "float_scalar"

        # Test storing in program's _variables
        assert len(instance._variables) == 6
        assert all(not variable_info.is_allocated for variable_info in instance._variables.values())
        assert all(variable_info.allocated_by is None for variable_info in instance._variables.values())

    def test_variable_method_raises_error_if_domain_is_scalar_and_type_is_none(self, instance: StructuredProgram):
        """Test variable method"""
        with pytest.raises(ValueError, match="You must specify a type in a scalar variable."):
            instance.variable(label="error", domain=Domain.Scalar)

    def test_variable_method_raises_error_if_domain_is_not_scalar_and_type_is_set(self, instance: StructuredProgram):
        """Test variable method"""
        with pytest.raises(
            ValueError, match="When declaring a variable of a specific domain, its type is inferred by its domain."
        ):
            instance.variable(label="error", domain=Domain.Frequency, type=int)
