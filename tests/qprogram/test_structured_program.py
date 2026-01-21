from collections import deque

import numpy as np
import pytest
import operator
import re
from qililab import Domain
from qililab.exceptions import VariableAllocated
from qililab.qprogram.blocks import Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.structured_program import StructuredProgram
from qililab.core.variables import FloatVariable, IntVariable, VariableExpression, Variable


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

    def test_variable_expression(self, instance: StructuredProgram):
        """Test VariableExpression creation and behavior"""
        time_variable_expression = instance.variable(label="time", domain=Domain.Time)

        expr1 = time_variable_expression + 5
        expr2 = 10 + time_variable_expression
        expr3 = time_variable_expression - 5
        expr4 = 10 - time_variable_expression
        expr5 = time_variable_expression + -5
        expr6 = -10 - time_variable_expression
        expr7 = time_variable_expression -- 10

        # Check that expressions are instances of VariableExpression
        assert isinstance(expr1, VariableExpression)
        assert isinstance(expr2, VariableExpression)
        assert isinstance(expr3, VariableExpression)
        assert isinstance(expr4, VariableExpression)
        assert isinstance(expr5, VariableExpression)
        assert isinstance(expr6, VariableExpression)
        assert isinstance(expr7, VariableExpression)

        # Check domain inference
        assert expr1.domain == Domain.Time
        assert expr2.domain == Domain.Time
        assert expr3.domain == Domain.Time
        assert expr4.domain == Domain.Time
        assert expr5.domain == Domain.Time
        assert expr6.domain == Domain.Time
        assert expr7.domain == Domain.Time

        # Check repr string
        assert repr(expr1) == f"({time_variable_expression} + 5)"
        assert repr(expr2) == f"({time_variable_expression} + 10)"
        assert repr(expr3) == f"({time_variable_expression} - 5)"
        assert repr(expr4) == f"(10 - {time_variable_expression})"
        assert repr(expr5) == f"({time_variable_expression} - 5)"
        assert repr(expr6) == f"(-10 - {time_variable_expression})"
        assert repr(expr7) == f"({time_variable_expression} + 10)"

        # Check extract methods
        assert expr1._extract_variables() == [time_variable_expression]
        assert expr2._extract_variables() == [time_variable_expression]
        assert expr3._extract_variables() == [time_variable_expression]
        assert expr4._extract_variables() == [time_variable_expression]
        assert expr5._extract_variables() == [time_variable_expression]
        assert expr6._extract_variables() == [time_variable_expression]
        assert expr7._extract_variables() == [time_variable_expression]
        assert expr1._extract_constant() == 5
        assert expr2._extract_constant() == 10
        assert expr3._extract_constant() == 5
        assert expr4._extract_constant() == 10
        assert expr5._extract_constant() == abs(-5)
        assert expr6._extract_constant() == -10
        assert expr7._extract_constant() == abs(-10)

    def test_variable_expression_unitary_operations(self, instance: StructuredProgram):
        """Test unitary expression with Variables"""
        time_variable = instance.variable(label="time", domain=Domain.Time)

        expr1 = +time_variable
        expr2 = -time_variable

        # Check that expressions are instances of the correct class
        assert isinstance(expr1, (Variable, IntVariable))
        assert not isinstance(expr1, VariableExpression)
        assert isinstance(expr2, (Variable, IntVariable, VariableExpression))

        # Check domain inference
        assert expr1.domain == Domain.Time
        assert expr2.domain == Domain.Time

        # Check repr string
        assert repr(expr1) == f"{time_variable}"
        assert repr(expr2) == f"(0 - {time_variable})"

        # Check extract methods
        assert expr2._extract_variables() == [time_variable]
        assert expr2._extract_constant() == 0
        
        with pytest.raises(NotImplementedError, match="Taking the absolute of a variable is not implemented in QProgram."):
            abs(time_variable)

    def test_variable_expression_infer_domain_error(self):
        # Pure-constant expression should fail to infer a domain
        with pytest.raises(ValueError, match="Cannot infer domain from constants."):
            VariableExpression(5, "+", 3)

    def test_extract_variables_raises_error_when_no_variables(self, instance):
        # Create a valid VariableExpression with a Time variable
        time_var = instance.variable(label="time", domain=Domain.Time)
        expr = time_var + 5

        # Overwrite operands to simulate pure constants (bypass domain inference)
        expr.left = 5
        expr.right = 3

        # Now extract_variables should fail because no Variable remains
        with pytest.raises(ValueError, match="No Variable instance found in expression"):
            expr._extract_variables()

    def test_two_variables_time_domain(self, instance):
        # More than 2 variable is not allowed for time domains
        time1 = instance.variable(label="time1", domain=Domain.Time)
        time2 = instance.variable(label="time2", domain=Domain.Time)
        with pytest.raises(NotImplementedError, match='For the Time domain, combining several variables in one expression is not implemented.'):
            time1 + time2

    def test_three_variable_raises_error(self, instance):
        # Freqeuncy doe snot support Variable Expressions
        gain1 = instance.variable(label="gain1", domain=Domain.Voltage)
        gain2 = instance.variable(label="gain2", domain=Domain.Voltage)
        gain3 = instance.variable(label="gain3", domain=Domain.Voltage)
        with pytest.raises(NotImplementedError, match=f"Chaining Variable expressions is not supported; use at most one binary operation."):
            gain1 + gain2 + gain3

    def test_frequency_domain_raises_error(self, instance):
        # Substractions are not implemented for non time domains
        freq1 = instance.variable(label="freq1", domain=Domain.Frequency)
        freq2 = instance.variable(label="freq2", domain=Domain.Frequency)
        with pytest.raises(NotImplementedError, match=f"For the {Domain.Frequency.name} domain, VariableExpression is not supported yet."):
            freq1 + freq2

    def test_forbidden_operation(self,instance):
        # Only addition and substraction are possible
        freq1 = instance.variable(label="freq1", domain=Domain.Frequency)
        freq2 = instance.variable(label="freq2", domain=Domain.Frequency)
        with pytest.raises(TypeError, match=f"'multiplication \(\*\)' is not a valid operation for QProgram variables."):
            freq1 * freq2


    def test_combine_domains_raises_error(self,instance):
        # Only one type of domain per expression is allowed
        gain = instance.variable(label="gain", domain=Domain.Voltage)
        freq = instance.variable(label="freq", domain=Domain.Frequency)
        with pytest.raises(ValueError, match="All variables should have the same domain."):
            gain + freq

    @pytest.mark.parametrize(
        "op, operation_str",
        [
            (operator.mul, "multiplication (*)"),
            (operator.matmul, "matrix multiplication (@)"),
            (operator.truediv, "division (/)"),
            (operator.floordiv, "floor division (//)"),
            (operator.mod, "modulo (%)"),
            (operator.pow, "power (**)"),
            (operator.and_, "bitwise and (&)"),
            (operator.or_, "bitwise or (|)"),
            (operator.xor, "bitwise xor (^)"),
            (operator.lshift, "left shift (<<)"),
            (operator.rshift, "right shift (>>)"),
            (operator.gt, "greater-than (>)"),
            (operator.ge, "greater-or-equal (>=)"),
            (operator.lt, "less-than (<)"),
            (operator.le, "lesser-or-equal (<=)"),
            # reflected ops
            (operator.mul, "reflected multiplication (*)"),      # 10 * gain
            (operator.truediv, "reflected division (/)"),         # 10 / gain
        ],
    )
    def test_unsupported_operations(self, instance, op, operation_str):
        gain = instance.variable(label="gain", domain=Domain.Voltage)

        if operation_str.startswith("reflected"):
            expr = lambda: op(10, gain)
        else:
            expr = lambda: op(gain, 10)

        with pytest.raises(
            TypeError,
            match=re.escape( f"'{operation_str}' is not a valid operation for QProgram variables."),
        ):
            expr()

    def test_unsupported_inplace_operations(self, instance):
        gain = instance.variable(label="gain", domain=Domain.Voltage)
        with pytest.raises(
            TypeError,
            match=re.escape("'in-place addition (+=)' is not a valid operation for QProgram variables."),
        ):
            gain += 10

        with pytest.raises(
            TypeError,
            match=re.escape("'in-place subtraction (-=)' is not a valid operation for QProgram variables."),
        ):
            gain -= 10

        with pytest.raises(
            TypeError,
            match=re.escape("'in-place multiplication (*=)' is not a valid operation for QProgram variables."),
        ):
            gain *= 10

        with pytest.raises(
            TypeError,
            match=re.escape("'in-place division (/=)' is not a valid operation for QProgram variables."),
        ):
            gain /= 10

    def test_non_int_constant_raise_error(self, instance):
        gain = instance.variable(label="gain", domain=Domain.Voltage)
        with pytest.raises(
            ValueError,
            match=re.escape("Constants must be integers."),
        ):
            gain + 0.5
