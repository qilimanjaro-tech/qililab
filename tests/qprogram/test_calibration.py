import os

import numpy as np
import pytest

from qililab.qprogram import QProgram
from qililab.qprogram.blocks import Block
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qilisdk.qprogram.waveforms import IQPair, Square
from qililab.utils.serialization import serialize_to, deserialize_from


class TestCalibration:
    """Unit tests checking the Calibration attributes and methods."""

    def test_init(self):
        """Test init method"""
        calibration = Calibration()

        assert isinstance(calibration, Calibration)
        assert isinstance(calibration.waveforms, dict)
        assert isinstance(calibration.weights, dict)
        assert isinstance(calibration.blocks, dict)
        assert isinstance(calibration.parameters, dict)
        assert calibration.crosstalk_matrix is None
        assert len(calibration.waveforms) == 0
        assert len(calibration.weights) == 0
        assert len(calibration.blocks) == 0
        assert len(calibration.parameters) == 0

    def test_add_waveform_method(self):
        """Test add_waveform method"""
        xpi = Square(1.0, 100)
        xpi2 = Square(1.0, 50)
        readout = Square(1.0, 2000)

        calibration = Calibration()
        calibration.add_waveform(bus="drive_bus", name="Xpi", waveform=xpi)

        assert len(calibration.waveforms) == 1
        assert "drive_bus" in calibration.waveforms

        assert isinstance(calibration.waveforms["drive_bus"], dict)
        assert len(calibration.waveforms["drive_bus"]) == 1
        assert "Xpi" in calibration.waveforms["drive_bus"]
        assert calibration.waveforms["drive_bus"]["Xpi"] == xpi

        calibration.add_waveform(bus="drive_bus", name="Xpi2", waveform=xpi2)
        assert len(calibration.waveforms["drive_bus"]) == 2
        assert "Xpi2" in calibration.waveforms["drive_bus"]
        assert calibration.waveforms["drive_bus"]["Xpi2"] == xpi2

        calibration.add_waveform(bus="readout_bus", name="readout", waveform=readout)
        assert len(calibration.waveforms) == 2
        assert isinstance(calibration.waveforms["readout_bus"], dict)
        assert len(calibration.waveforms["readout_bus"]) == 1
        assert "readout" in calibration.waveforms["readout_bus"]
        assert calibration.waveforms["readout_bus"]["readout"] == readout

    def test_add_weights_method(self):
        """Test add_weights method"""
        weights = IQPair(Square(1.0, 2000), Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_weights(bus="readout_bus", name="optimal_weights", weights=weights)

        assert len(calibration.weights) == 1
        assert "readout_bus" in calibration.weights

        assert isinstance(calibration.weights["readout_bus"], dict)
        assert len(calibration.weights["readout_bus"]) == 1
        assert "optimal_weights" in calibration.weights["readout_bus"]
        assert calibration.weights["readout_bus"]["optimal_weights"] == weights

    def test_add_block_method(self):
        """Test add_weights method"""
        qp = QProgram()
        qp.play(bus="flux_x", waveform=Square(1.0, 100))
        qp.play(bus="flux_y", waveform=Square(1.0, 100))

        calibration = Calibration()
        calibration.add_block(name="flux_block", block=qp.body)

        assert len(calibration.blocks) == 1
        assert "flux_block" in calibration.blocks
        assert isinstance(calibration.blocks["flux_block"], Block)

    def test_has_waveform_method(self):
        """Test has_operation method"""
        xpi = Square(1.0, 100)
        xpi2 = Square(1.0, 50)

        calibration = Calibration()
        calibration.add_waveform(bus="drive_bus", name="Xpi", waveform=xpi)
        calibration.add_waveform(bus="drive_bus", name="Xpi2", waveform=xpi2)

        assert calibration.has_waveform(bus="drive_bus", name="Xpi") is True
        assert calibration.has_waveform(bus="drive_bus", name="Xpi2") is True
        assert calibration.has_waveform(bus="drive_bus", name="non_existant") is False
        assert calibration.has_waveform(bus="non_existant", name="Xpi") is False

    def test_has_weights_method(self):
        """Test add_operation method"""
        weights = IQPair(Square(1.0, 2000), Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_weights(bus="readout_bus", name="optimal_weights", weights=weights)

        assert len(calibration.weights) == 1
        assert "readout_bus" in calibration.weights

        assert calibration.has_weights(bus="readout_bus", name="optimal_weights") is True
        assert calibration.has_weights(bus="readout_bus", name="non_existant_weights") is False
        assert calibration.has_weights(bus="non_existant", name="non_existant_weights") is False

    def test_has_block_method(self):
        """Test add_weights method"""
        qp = QProgram()
        qp.play(bus="flux_x", waveform=Square(1.0, 100))
        qp.play(bus="flux_y", waveform=Square(1.0, 100))

        calibration = Calibration()
        calibration.add_block(name="flux_block", block=qp.body)

        assert calibration.has_block("flux_block")

    def test_get_waveform_method(self):
        """Test get_operation method"""
        xpi = Square(1.0, 100)
        xpi2 = Square(1.0, 50)

        calibration = Calibration()
        calibration.add_waveform(bus="drive_bus", name="Xpi", waveform=xpi)
        calibration.add_waveform(bus="drive_bus", name="Xpi2", waveform=xpi2)

        retrieved_xpi = calibration.get_waveform(bus="drive_bus", name="Xpi")
        assert xpi == retrieved_xpi

        retrieved_xpi2 = calibration.get_waveform(bus="drive_bus", name="Xpi2")
        assert xpi2 == retrieved_xpi2

        with pytest.raises(KeyError):
            _ = calibration.get_waveform(bus="drive_bus", name="non_existant")

        with pytest.raises(KeyError):
            _ = calibration.get_waveform(bus="non_existant", name="Xpi")

    def test_get_weights_method(self):
        """Test add_operation method"""
        weights = IQPair(Square(1.0, 2000), Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_weights(bus="readout_bus", name="optimal_weights", weights=weights)

        retrieved_weights = calibration.get_weights(bus="readout_bus", name="optimal_weights")
        assert retrieved_weights == weights

        with pytest.raises(KeyError):
            _ = calibration.get_weights(bus="readout_bus", name="non_existant_weights")

        with pytest.raises(KeyError):
            _ = calibration.get_weights(bus="non_existant_bus", name="optimal_weights")

    def test_get_block_method(self):
        """Test add_weights method"""
        qp = QProgram()
        qp.play(bus="flux_x", waveform=Square(1.0, 100))
        qp.play(bus="flux_y", waveform=Square(1.0, 100))

        calibration = Calibration()
        calibration.add_block(name="flux_block", block=qp.body)

        retrieved_block = calibration.get_block(name="flux_block")
        assert retrieved_block == qp.body

        with pytest.raises(KeyError):
            _ = calibration.get_block(name="non_existant_block")

    def test_adding_crosstalk_matrix(self):
        """Test adding a crosstalk matrix to the calibration object"""
        buses = {
            "flux_0": {"flux_0": 1.47046905, "flux_1": 0.12276261},
            "flux_1": {"flux_0": -0.55322207, "flux_1": 1.58247856},
        }
        crosstalk_matrix = CrosstalkMatrix().from_buses(buses)
        calibration = Calibration()
        calibration.crosstalk_matrix = crosstalk_matrix

        assert calibration.crosstalk_matrix["flux_0"]["flux_0"] == crosstalk_matrix["flux_0"]["flux_0"]
        assert calibration.crosstalk_matrix["flux_0"]["flux_1"] == crosstalk_matrix["flux_0"]["flux_1"]
        assert calibration.crosstalk_matrix["flux_1"]["flux_0"] == crosstalk_matrix["flux_1"]["flux_0"]
        assert calibration.crosstalk_matrix["flux_1"]["flux_1"] == crosstalk_matrix["flux_1"]["flux_1"]

    def test_dump_load_methods(self):
        """Test dump and load methods"""
        qp = QProgram()
        qp.play(bus="flux_x", waveform=Square(1.0, 100))
        qp.play(bus="flux_y", waveform=Square(1.0, 100))

        buses = {
            "flux_0": {"flux_0": 1.47046905, "flux_1": 0.12276261},
            "flux_1": {"flux_0": -0.55322207, "flux_1": 1.58247856},
        }
        crosstalk_matrix = CrosstalkMatrix().from_buses(buses)
        calibration = Calibration()
        calibration.add_waveform(bus="drive_bus", name="Xpi", waveform=Square(1.0, 100))
        calibration.add_waveform(bus="drive_bus", name="Xpi2", waveform=Square(1.0, 50))
        calibration.add_waveform(bus="readout_bus", name="readout", waveform=Square(1.0, 2000))
        calibration.add_weights(
            bus="readout_bus", name="optimal_weights", weights=IQPair(Square(1.0, 2000), Square(1.0, 2000))
        )
        calibration.add_block(name="flux_block", block=qp.body)
        calibration.crosstalk_matrix = crosstalk_matrix

        serialize_to(calibration, "calibration.yml")
        loaded_calibration = deserialize_from("calibration.yml", Calibration)

        assert isinstance(loaded_calibration, Calibration)

        xpi = loaded_calibration.get_waveform(bus="drive_bus", name="Xpi")
        xpi2 = loaded_calibration.get_waveform(bus="drive_bus", name="Xpi2")
        readout = loaded_calibration.get_waveform(bus="readout_bus", name="readout")
        weights = calibration.get_weights(bus="readout_bus", name="optimal_weights")
        block = calibration.get_block(name="flux_block")

        assert isinstance(xpi, Square)
        assert xpi.amplitude == 1.0
        assert xpi.duration == 100

        assert isinstance(xpi2, Square)
        assert xpi2.amplitude == 1.0
        assert xpi2.duration == 50

        assert isinstance(readout, Square)
        assert readout.amplitude == 1.0
        assert readout.duration == 2000

        assert isinstance(weights, IQPair)
        assert isinstance(weights.I, Square)
        assert weights.I.amplitude == 1.0
        assert weights.I.duration == 2000
        assert isinstance(weights.Q, Square)
        assert weights.Q.amplitude == 1.0
        assert weights.Q.duration == 2000

        assert isinstance(block, Block)
        assert len(block.elements) == 2

        assert calibration.crosstalk_matrix["flux_0"]["flux_0"] == crosstalk_matrix["flux_0"]["flux_0"]
        assert calibration.crosstalk_matrix["flux_0"]["flux_1"] == crosstalk_matrix["flux_0"]["flux_1"]
        assert calibration.crosstalk_matrix["flux_1"]["flux_0"] == crosstalk_matrix["flux_1"]["flux_0"]
        assert calibration.crosstalk_matrix["flux_1"]["flux_1"] == crosstalk_matrix["flux_1"]["flux_1"]

        os.remove(path="calibration.yml")
