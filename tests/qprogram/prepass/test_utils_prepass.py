from qprogram.blocks import Average, Sweep
from qprogram.operations import Play, Sync, Wait
from qprogram_qdac import SetOffset as QdacSetOffset

from qililab import IQPair, QProgram, Square
from qililab.qprogram.compilers.prepass.utils_prepass import keep_instrument_operations


class TestKeepInstrumentOperations:
    def test_keeps_operations_on_buses_syncs_and_every_block(self):
        qp = QProgram()
        offset = qp.variable("offset")
        qp.qdac.set_offset(bus="qdac", offset=0.1)
        with qp.average(10):
            qp.play(bus="drive", waveform=IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)))
            qp.wait(bus="qdac", duration=100)
            qp.sync()
            with qp.sweep(offset).from_range(0.0, 0.5, 0.1):
                qp.set_offset(bus="qdac", offset_path0=offset)

        kept = keep_instrument_operations(qp, {"drive", "readout"})

        assert kept.buses == {"drive"}
        (average,) = kept.body.elements
        assert isinstance(average, Average)
        play, sync, sweep = average.elements
        assert isinstance(play, Play)
        assert isinstance(sync, Sync)
        assert isinstance(sweep, Sweep)
        assert sweep.elements == []

        # The original QProgram is not modified
        assert qp.buses == {"drive", "qdac"}
        assert isinstance(qp.body.elements[0], QdacSetOffset)
        assert [type(element) for element in qp.body.elements[1].elements] == [Play, Wait, Sync, Sweep]

    def test_keeps_blocks_and_their_parameters(self):
        """Blocks are kept, as copies with the same type and parameters, even when they end up empty."""
        qp = QProgram()
        frequency = qp.variable("frequency")
        with qp.average(10):
            with qp.sweep(frequency).from_range(10e6, 100e6, 10e6):
                qp.wait(bus="qdac", duration=100)

        kept = keep_instrument_operations(qp, {"drive"})

        (average,) = kept.body.elements
        assert isinstance(average, Average)
        assert average is not qp.body.elements[0]
        assert average.shots == 10
        (sweep,) = average.elements
        assert isinstance(sweep, Sweep)
        assert sweep.variable == frequency
        assert sweep.source == qp.body.elements[0].elements[0].source
        assert sweep.elements == []

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
