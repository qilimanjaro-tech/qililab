import os

import pytest

from qililab.qprogram.calibration import Calibration
from qililab.waveforms import Arbitrary, FlatTop, Gaussian, IQPair, Square
from qililab.yaml import yaml


class TestCalibration:
    """Unit tests checking the Calibration attributes and methods."""

    def test_init(self):
        """Test init method"""
        calibration = Calibration()

        assert isinstance(calibration, Calibration)
        assert isinstance(calibration.waveforms, dict)
        assert isinstance(calibration.weights, dict)
        assert len(calibration.waveforms) == 0
        assert len(calibration.weights) == 0

    def test_add_waveform(self):
        """Test add_operation method"""
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

    def test_add_weight(self):
        """Test add_operation method"""
        weights = IQPair(Square(1.0, 2000), Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_weights(bus="readout_bus", name="optimal_weights", weights=weights)

        assert len(calibration.weights) == 1
        assert "readout_bus" in calibration.weights

        assert isinstance(calibration.weights["readout_bus"], dict)
        assert len(calibration.weights["readout_bus"]) == 1
        assert "optimal_weights" in calibration.weights["readout_bus"]
        assert calibration.weights["readout_bus"]["optimal_weights"] == weights

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

    def test_dump_load_methods(self):
        """Test dump and load methods"""
        calibration = Calibration()
        calibration.add_waveform(bus="drive_bus", name="Xpi", waveform=Square(1.0, 100))
        calibration.add_waveform(bus="drive_bus", name="Xpi2", waveform=Square(1.0, 50))
        calibration.add_waveform(bus="readout_bus", name="readout", waveform=Square(1.0, 2000))
        calibration.add_weights(
            bus="readout_bus", name="optimal_weights", weights=IQPair(Square(1.0, 2000), Square(1.0, 2000))
        )

        calibration.save_to(file="calibration.yml")
        loaded_calibration = Calibration.load_from(file="calibration.yml")

        assert isinstance(loaded_calibration, Calibration)

        xpi = loaded_calibration.get_waveform(bus="drive_bus", name="Xpi")
        xpi2 = loaded_calibration.get_waveform(bus="drive_bus", name="Xpi2")
        readout = loaded_calibration.get_waveform(bus="readout_bus", name="readout")
        weights = calibration.get_weights(bus="readout_bus", name="optimal_weights")

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

        os.remove(path="calibration.yml")

        # Test that loading a different yaml produces an error
        square = Square(1.0, 100)

        with open(file="calibration.yml", mode="w", encoding="utf-8") as stream:
            yaml.dump(data=square, stream=stream)

        with pytest.raises(TypeError):
            _ = Calibration.load_from(file="calibration.yml")

        os.remove(path="calibration.yml")
