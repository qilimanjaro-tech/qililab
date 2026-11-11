import os
from collections import deque

import numpy as np
import pytest
from qprogram import Range, Values
from qprogram.blocks import Block, Parallel, Sweep

from qililab import IQPair, Square
from qililab.exceptions import VariableAllocated
from qililab.qprogram.blocks import ForLoop, Loop
from qililab.qprogram.crosstalk.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.experiment.experiment import Experiment
from qililab.qprogram.operations import ExecuteQProgram, SetParameter
from qililab.qprogram.operations.set_crosstalk import SetCrosstalk
from qililab.qprogram.qprogram import QProgram
from qililab.typings.enums import Parameter
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


class TestExperiment:
    """Unit tests checking the Experiment attributes and methods"""

    @pytest.fixture
    def instance(self):
        return Experiment(label="experiment")

    def test_init(self, instance: Experiment):
        """Test init method"""
        assert isinstance(instance._body, Block)
        assert len(instance._body.elements) == 0
        assert isinstance(instance._block_stack, deque)
        assert len(instance._block_stack) == 1
        assert isinstance(instance._variables, list)
        assert len(instance._variables) == 0
        assert instance.label == "experiment"

    def test_active_block_property(self, instance: Experiment):
        """Test _active_block property"""
        assert isinstance(instance._active_block, Block)
        assert instance._active_block is instance._body

    def test_block_method(self, instance: Experiment):
        """Test block method"""
        with instance.block() as block:
            # __enter__
            assert isinstance(block, Block)
            assert instance._active_block is block
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is block

    def test_parallel_method(self, instance: Experiment):
        """Test parallel method"""
        var1 = instance.variable("int_scalar")
        var2 = instance.variable("float_scalar")
        with instance.parallel(
            loops=[
                ForLoop(variable=var1, start=0, stop=10, step=1),
                ForLoop(variable=var2, start=0.0, stop=1.0, step=0.1),
            ]
        ) as loop:
            # __enter__
            assert isinstance(loop, Parallel)
            assert len(loop.loops) == 2
            assert all(isinstance(sweep, Sweep) for sweep in loop.loops)
            assert [sweep.variable for sweep in loop.loops] == [var1, var2]
            assert loop.loops[0].source == Range(0, 10, 1)
            assert loop.loops[1].source == Range(0.0, 1.0, 0.1)
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_for_loop_method(self, instance: Experiment):
        """Test for_loop method"""
        variable = instance.variable("int_scalar")
        start, stop, step = 0, 100, 5
        with instance.for_loop(variable=variable, start=start, stop=stop, step=step) as loop:
            # __enter__
            assert isinstance(loop, Sweep)
            assert loop.variable == variable
            assert isinstance(loop.source, Range)
            assert loop.source.start == start
            assert loop.source.stop == stop
            assert loop.source.step == step
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_loop_method(self, instance: Experiment):
        """Test loop method"""
        variable = instance.variable("int_scalar")
        values = np.ones(10, dtype=int)
        with instance.loop(variable=variable, values=values) as loop:
            # __enter__
            assert isinstance(loop, Sweep)
            assert loop.variable == variable
            assert isinstance(loop.source, Values)
            assert np.array_equal(loop.source.values(), values)
            assert instance._active_block is loop
        # __exit__
        assert len(instance._body.elements) == 1
        assert instance._body.elements[0] is loop
        assert instance._active_block is instance._body

    def test_loops_raise_error_if_variable_is_allocated(self, instance: Experiment):
        """Test loop methods raise an error when the loop variable is already swept by an enclosing loop"""
        variable = instance.variable("int_scalar")
        values = np.arange(10)
        loops = [Loop(variable=variable, values=values)]
        # test when ForLoop allocates variable
        with instance.for_loop(variable=variable, start=0, stop=10, step=1):
            with pytest.raises(VariableAllocated):
                with instance.for_loop(variable=variable, start=100, stop=110, step=1):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.loop(variable=variable, values=values):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.parallel(loops=loops):
                    pass
        # test when Loop allocates variable
        with instance.loop(variable=variable, values=values):
            with pytest.raises(VariableAllocated):
                with instance.for_loop(variable=variable, start=100, stop=110, step=1):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.loop(variable=variable, values=values):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.parallel(loops=loops):
                    pass
        # test when Parallel allocates variable
        with instance.parallel(loops=loops):
            with pytest.raises(VariableAllocated):
                with instance.for_loop(variable=variable, start=100, stop=110, step=1):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.loop(variable=variable, values=values):
                    pass
            with pytest.raises(VariableAllocated):
                with instance.parallel(loops=loops):
                    pass

    def test_set_parameter_with_unary_plus_stores_the_variable(self, instance: Experiment):
        """``+x`` is ``x`` in an Experiment too."""
        bias = instance.variable("bias")
        with instance.for_loop(variable=bias, start=0.0, stop=1.0, step=0.5):
            instance.set_parameter(alias="flux_q0", parameter=Parameter.VOLTAGE, value=+bias)

        (set_parameter,) = instance.body.elements[0].elements
        assert set_parameter.value is bias

    def test_set_parameter(self, instance: Experiment):
        """Test set_awg_gain method"""
        instance.set_parameter(alias="flux_bus", parameter=Parameter.VOLTAGE, value=0.5)

        assert len(instance._active_block.elements) == 1
        assert len(instance._body.elements) == 1
        assert isinstance(instance._body.elements[0], SetParameter)
        assert instance._body.elements[0].alias == "flux_bus"
        assert instance._body.elements[0].parameter == Parameter.VOLTAGE
        assert instance._body.elements[0].value == 0.5

    def test_set_parameter_flux(self, instance: Experiment):
        """Test set_parameter method with FLUX parameter and crosstalk"""
        instance.set_crosstalk(CrosstalkMatrix.from_buses({"flux_bus": {"flux_bus": 1.0}}))
        instance.set_parameter(alias="flux_bus", parameter=Parameter.FLUX, value=0.5)

        assert len(instance._active_block.elements) == 2
        assert len(instance._body.elements) == 2
        assert isinstance(instance._body.elements[1], SetParameter)
        assert isinstance(instance._body.elements[0], SetCrosstalk)
        assert instance._body.elements[1].alias == "flux_bus"
        assert instance._body.elements[1].parameter == Parameter.FLUX
        assert instance._body.elements[1].value == 0.5

    def test_execute_qprogram(self, instance: Experiment):
        """Test execute_qprogram method"""
        qp = QProgram()
        instance.execute_qprogram(qprogram=qp)

        assert len(instance._active_block.elements) == 1
        assert len(instance._body.elements) == 1
        assert isinstance(instance._body.elements[0], ExecuteQProgram)
        assert instance._body.elements[0].qprogram is qp

    def test_serialization_deserialization(self, instance: Experiment):
        """Test serialization and deserialization works."""
        file = "test_serialization_deserialization_experiment.yml"
        qp = QProgram()
        gain = qp.variable("gain")
        with qp.sweep(gain).from_range(0.0, 1.0, 0.1):
            qp.set_gain(bus="drive_bus", gain=gain)
            qp.play(bus="drive_bus", waveform=IQPair(I=Square(1.0, 200), Q=Square(1.0, 200)))

        voltage = instance.variable("voltage")
        with instance.for_loop(variable=voltage, start=0.0, stop=1.0, step=0.1):
            instance.set_parameter(alias="flux_bus", parameter=Parameter.VOLTAGE, value=voltage)
            instance.execute_qprogram(qp)

        serialized = serialize(instance)
        deserialized_experiment = deserialize(serialized, Experiment)

        assert isinstance(deserialized_experiment, Experiment)
        assert deserialized_experiment.label == "experiment"
        (loop,) = deserialized_experiment.body.elements
        assert isinstance(loop, Sweep)
        assert loop.source == Range(0.0, 1.0, 0.1)
        set_parameter, execute_qprogram = loop.elements
        assert isinstance(set_parameter, SetParameter)
        assert set_parameter.value == loop.variable
        assert isinstance(execute_qprogram, ExecuteQProgram)
        assert isinstance(execute_qprogram.qprogram, QProgram)
        assert str(QProgram.from_qp(str(execute_qprogram.qprogram))) == str(qp)

        serialize_to(instance, file=file)
        deserialized_experiment = deserialize_from(file, Experiment)

        assert isinstance(deserialized_experiment, Experiment)

        os.remove(file)
