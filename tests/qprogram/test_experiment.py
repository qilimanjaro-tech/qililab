import os
from unittest.mock import patch

import pytest
from tests.qprogram.test_structured_program import TestStructuredProgram

from qililab.qprogram.calibration import Calibration
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.operations import ExecuteQProgram, SetParameter
from qililab.qprogram.operations.set_crosstalk import SetCrosstalk
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Domain
from qililab.typings.enums import Parameter
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to
from qililab.waveforms import IQPair, Square


class TestExperiment(TestStructuredProgram):
    """Unit tests checking the QProgram attributes and methods"""

    @pytest.fixture
    def instance(self):
        return Experiment(label="experiment")

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
        gain = qp.variable(label="gain", domain=Domain.Voltage)
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="drive_bus", gain=gain)
            qp.play(bus="drive_bus", waveform=IQPair(I=Square(1.0, 200), Q=Square(1.0, 200)))

        voltage = instance.variable(label="voltage", domain=Domain.Voltage)
        with instance.for_loop(variable=voltage, start=0.0, stop=1.0, step=0.1):
            instance.set_parameter(alias="flux_bus", parameter=Parameter.VOLTAGE, value=voltage)
            instance.execute_qprogram(qp)

        serialized = serialize(instance)
        deserialized_experiment = deserialize(serialized, Experiment)

        assert isinstance(deserialized_experiment, Experiment)

        serialize_to(instance, file=file)
        deserialized_experiment = deserialize_from(file, Experiment)

        assert isinstance(deserialized_experiment, Experiment)

        os.remove(file)
