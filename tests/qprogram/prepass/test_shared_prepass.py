import numpy as np
import pytest

from qililab import Calibration, QProgram, Square
from qililab.qprogram.operations import Play
from qililab.qprogram.prepass.shared_prepass import prepare_qprogram


class TestPrepareQProgram:
    def test_bus_mapping_and_calibration_are_applied(self):
        calibration = Calibration()
        calibration.add_waveform(bus="drive_q0", name="Xpi", waveform=Square(amplitude=1.0, duration=40))
        qp = QProgram()
        qp.play(bus="drive", waveform="Xpi")

        prepared = prepare_qprogram(qp, bus_mapping={"drive": "drive_q0"}, calibration=calibration)

        assert prepared.buses == {"drive_q0"}
        (play,) = prepared.body.elements
        assert isinstance(play, Play)
        assert play.bus == "drive_q0"
        np.testing.assert_array_equal(play.get_waveforms()[0].envelope(), np.ones(40))
        assert qp.buses == {"drive"}

    def test_unmapped_named_operation_raises_error(self):
        qp = QProgram()
        qp.play(bus="drive", waveform="Xpi")
        calibration = Calibration()

        with pytest.raises(RuntimeError, match="contains named operations that are not mapped"):
            prepare_qprogram(qp, bus_mapping={"drive": "drive_q0"}, calibration=calibration)
