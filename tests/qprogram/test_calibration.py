import os

import pytest

from qililab.qprogram.calibration import Calibration
from qililab.waveforms import Arbitrary, FlatTop, Gaussian, IQPair, Square


class TestCalibration:
    """Unit tests checking the Calibration attributes and methods."""

    def test_init(self):
        """Test init method"""
        calibration = Calibration()

        assert isinstance(calibration, Calibration)
        assert isinstance(calibration.operations, dict)
        assert len(calibration.operations) == 0

    def test_add_operation(self):
        """Test add_operation method"""
        xpi = Square(1.0, 100)
        xpi2 = Square(1.0, 50)
        readout = Square(1.0, 2000)

        calibration = Calibration()
        calibration.add_operation(bus="drive_bus", operation="Xpi", waveform=xpi)

        assert len(calibration.operations) == 1
        assert "drive_bus" in calibration.operations

        assert isinstance(calibration.operations["drive_bus"], dict)
        assert len(calibration.operations["drive_bus"]) == 1
        assert "Xpi" in calibration.operations["drive_bus"]
        assert calibration.operations["drive_bus"]["Xpi"] == xpi

        calibration.add_operation(bus="drive_bus", operation="Xpi2", waveform=xpi2)
        assert len(calibration.operations["drive_bus"]) == 2
        assert "Xpi2" in calibration.operations["drive_bus"]
        assert calibration.operations["drive_bus"]["Xpi2"] == xpi2

        calibration.add_operation(bus="readout_bus", operation="readout", waveform=readout)
        assert len(calibration.operations) == 2
        assert isinstance(calibration.operations["readout_bus"], dict)
        assert len(calibration.operations["readout_bus"]) == 1
        assert "readout" in calibration.operations["readout_bus"]
        assert calibration.operations["readout_bus"]["readout"] == readout

    def test_get_operation_method(self):
        """Test get_operation method"""
        xpi = Square(1.0, 100)
        xpi2 = Square(1.0, 50)

        calibration = Calibration()
        calibration.add_operation(bus="drive_bus", operation="Xpi", waveform=xpi)
        calibration.add_operation(bus="drive_bus", operation="Xpi2", waveform=xpi2)

        retrieved_xpi = calibration.get_operation(bus="drive_bus", operation="Xpi")
        assert xpi == retrieved_xpi

        retrieved_xpi2 = calibration.get_operation(bus="drive_bus", operation="Xpi2")
        assert xpi2 == retrieved_xpi2

        with pytest.raises(KeyError):
            _ = calibration.get_operation(bus="drive_bus", operation="non_existant")

        with pytest.raises(KeyError):
            _ = calibration.get_operation(bus="non_existant", operation="Xpi")

    def test_dump_load_methods(self):
        """Test dump and load methods"""
        calibration = Calibration()
        calibration.add_operation(bus="drive_bus", operation="Xpi", waveform=Square(1.0, 100))
        calibration.add_operation(bus="drive_bus", operation="Xpi2", waveform=Square(1.0, 50))
        calibration.add_operation(bus="readout_bus", operation="readout", waveform=Square(1.0, 2000))

        calibration.dump(file="calibration.yml")
        loaded_calibration = Calibration.load(file="calibration.yml")

        assert isinstance(loaded_calibration, Calibration)

        xpi = loaded_calibration.get_operation(bus="drive_bus", operation="Xpi")
        xpi2 = loaded_calibration.get_operation(bus="drive_bus", operation="Xpi2")
        readout = loaded_calibration.get_operation(bus="readout_bus", operation="readout")

        assert isinstance(xpi, Square)
        assert xpi.amplitude == 1.0
        assert xpi.duration == 100

        assert isinstance(xpi2, Square)
        assert xpi2.amplitude == 1.0
        assert xpi2.duration == 50

        assert isinstance(readout, Square)
        assert readout.amplitude == 1.0
        assert readout.duration == 2000

        os.remove(path="calibration.yml")
