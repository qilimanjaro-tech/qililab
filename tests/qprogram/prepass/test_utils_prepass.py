from qililab import IQPair, QProgram, Square
from qililab.qprogram.blocks import Average, Block, ForLoop
from qililab.qprogram.operations import Play, SetOffset, Sync, Wait
from qililab.qprogram.prepass.utils_prepass import keep_instrument_operations
from qililab.core.variables import Domain


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
