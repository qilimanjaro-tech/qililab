from collections import deque

import numpy as np
import pytest
from qililab import Domain
from qililab.exceptions import VariableAllocated
from qililab.qprogram.blocks import Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.structured_program import StructuredProgram



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
