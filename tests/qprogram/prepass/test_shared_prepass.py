import numpy as np
import pytest

from qililab import Calibration, IQPair, QProgram, Square
from qililab.qprogram.blocks import Average, Block, ForLoop
from qililab.qprogram.operations import Play, SetOffset, Sync, Wait
from qililab.qprogram.prepass.shared_prepass import keep_instrument_operations, prepare_qprogram
from qililab.core.variables import Domain


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


class TestKeepInstrumentOperations:
    def test_keeps_operations_on_buses_syncs_and_every_block(self):
        qp = QProgram()
        offset = qp.variable(label="offset", domain=Domain.Voltage)
        qp.set_offset(bus="qdac", offset_path0=0.1)
        with qp.average(10):
            qp.play(bus="drive", waveform=IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)))
            qp.wait(bus="qdac", duration=100)
            qp.sync()
            with qp.for_loop(variable=offset, start=0.0, stop=0.5, step=0.1):
                qp.set_offset(bus="qdac", offset_path0=offset)

        kept = keep_instrument_operations(qp, {"drive", "readout"})

        assert kept.buses == {"drive"}
        (average,) = kept.body.elements
        assert isinstance(average, Average)
        play, sync, for_loop = average.elements
        assert isinstance(play, Play)
        assert isinstance(sync, Sync)
        assert isinstance(for_loop, ForLoop)
        assert for_loop.elements == []

        # The original QProgram is not modified
        assert qp.buses == {"drive", "qdac"}
        assert isinstance(qp.body.elements[0], SetOffset)
        assert [type(element) for element in qp.body.elements[1].elements] == [Play, Wait, Sync, ForLoop]

    def test_keeps_block_uuids(self):
        qp = QProgram()
        with qp.average(10):
            qp.wait(bus="qdac", duration=100)

        kept = keep_instrument_operations(qp, {"drive"})

        assert isinstance(kept.body.elements[0], Block)
        assert kept.body.elements[0].uuid == qp.body.elements[0].uuid

    def test_shares_waveforms(self):
        """The copy reuses the waveform objects instead of duplicating their samples."""
        waveform = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qp = QProgram()
        with qp.average(10):
            qp.play(bus="drive", waveform=waveform)

        kept = keep_instrument_operations(qp, {"drive"})

        (play,) = kept.body.elements[0].elements
        assert play is not qp.body.elements[0].elements[0]
        assert play.waveform is waveform
