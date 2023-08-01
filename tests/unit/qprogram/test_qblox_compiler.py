import pytest
import qpysequence as QPy
import qpysequence.program as QPyProgram
import qpysequence.program.instructions as QPyInstructions

from qililab.qprogram import QBloxCompiler, QProgram, Settings
from qililab.waveforms import DragPulse, IQPair, Square


@pytest.fixture(name="no_loops_all_operations")
def fixture_no_loops_all_operations() -> QProgram:
    """Return a QProgram containing all operations and no loops."""
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    qp.set_frequency(bus="drive", frequency=300)
    qp.set_phase(bus="drive", phase=90)
    qp.reset_phase(bus="drive")
    qp.set_gain(bus="drive", gain_path0=0.5, gain_path1=0.5)
    qp.set_offset(bus="drive", offset_path0=0.5, offset_path1=0.5)
    qp.play(bus="drive", waveform=drag_pair)
    qp.sync()
    qp.wait(bus="readout", time=100)
    qp.play(bus="readout", waveform=readout_pair)
    qp.acquire(bus="readout")
    return qp


class TestQBloxCompiler:
    def test_no_loops_all_operations(self, no_loops_all_operations: QProgram):
        compiler = QBloxCompiler(qprogram=no_loops_all_operations, settings=Settings())
        output = compiler.output

        assert len(output) == 2
        assert "drive" in output
        assert "readout" in output

        for bus in output:
            assert isinstance(output[bus], QPy.Sequence)

        assert len(output["drive"]._waveforms._waveforms) == 2
        assert len(output["drive"]._acquisitions._acquisitions) == 0
        assert len(output["drive"]._weights._weights) == 0
        assert output["drive"]._program._compiled
        assert (
            repr(output["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    set_freq         1200\n    set_ph           250000000\n    reset_ph\n    set_awg_gain     16383, 16383\n    set_awg_offs     16383, 16383\n    play             0, 1, 4\n    wait_sync        4\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    wait_sync        4\n    wait             100\n    play             0, 1, 4\n    acquire          0, 0, 1000\n    \n"
        )
