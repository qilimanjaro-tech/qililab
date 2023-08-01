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


@pytest.fixture(name="acquire_loop")
def fixture_acquire_loop() -> QProgram:
    """Return a QProgram containing all operations and no loops."""
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    with qp.acquire_loop(iterations=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync()
        qp.wait(bus="readout", time=100)
        qp.play(bus="readout", waveform=readout_pair)
        qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="acquire_loop_with_for_loop")
def fixture_acquire_loop_with_for_loop() -> QProgram:
    """Return a QProgram containing all operations and no loops."""
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    wait_time = qp.variable(int)
    with qp.acquire_loop(iterations=1000):
        with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
            qp.play(bus="drive", waveform=drag_pair)
            qp.sync()
            qp.wait(bus="readout", time=wait_time)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="acquire_loop_with_nested_for_loops")
def fixture_acquire_loop_with_nested_for_loops() -> QProgram:
    """Return a QProgram containing all operations and no loops."""
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    wait_time = qp.variable(int)
    gain = qp.variable(float)
    with qp.acquire_loop(iterations=1000):
        with qp.for_loop(variable=gain, start=0, stop=1, step=0.1):
            qp.set_gain(bus="drive", gain_path0=gain, gain_path1=gain)
            with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
                qp.play(bus="drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus="readout", time=wait_time)
                qp.play(bus="readout", waveform=readout_pair)
                qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="loop_variable_with_different_targets")
def fixture_loop_variable_with_different_targets() -> QProgram:
    """Return a QProgram containing all operations and no loops."""
    qp = QProgram()
    variable = qp.variable(float)
    with qp.acquire_loop(iterations=1000):
        with qp.for_loop(variable=variable, start=0, stop=100, step=4):
            qp.set_frequency(bus="drive", frequency=variable)
            qp.set_phase(bus="drive", phase=variable)
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

    def test_acquire_loop(self, acquire_loop: QProgram):
        compiler = QBloxCompiler(qprogram=acquire_loop, settings=Settings())
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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        play             0, 1, 4\n        wait_sync        4\n        loop             R0, @avg_0\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        wait_sync        4\n        wait             100\n        play             0, 1, 4\n        acquire          0, 0, 1000\n        loop             R0, @avg_0\n    \n"
        )

    def test_acquire_loop_with_for_loop(self, acquire_loop_with_for_loop: QProgram):
        compiler = QBloxCompiler(qprogram=acquire_loop_with_for_loop, settings=Settings())
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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             4, R1\n        loop_0:\n            wait_sync        4\n            play             0, 1, 4\n            wait_sync        4\n            add              R1, 4, R1\n            nop\n            jlt              R1, 100, @loop_0\n        loop             R0, @avg_0\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 24
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        wait_sync        4\n        move             4, R2\n        loop_0:\n            wait_sync        4\n            wait_sync        4\n            wait             R2\n            play             0, 1, 4\n            acquire          0, R1, 1000\n            add              R1, 1, R1\n            add              R2, 4, R2\n            nop\n            jlt              R2, 100, @loop_0\n        loop             R0, @avg_0\n    \n"
        )

    def test_acquire_loop_with_nested_for_loops(self, acquire_loop_with_nested_for_loops: QProgram):
        compiler = QBloxCompiler(qprogram=acquire_loop_with_nested_for_loops, settings=Settings())
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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             0, R1\n        loop_0:\n            wait_sync        4\n            set_awg_gain     R1, R1\n            move             4, R2\n            loop_1:\n                wait_sync        4\n                play             0, 1, 4\n                wait_sync        4\n                add              R2, 4, R2\n                nop\n                jlt              R2, 100, @loop_1\n            add              R1, 3276, R1\n            nop\n            jlt              R1, 32767, @loop_0\n        loop             R0, @avg_0\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 240
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        wait_sync        4\n        move             0, R2\n        loop_0:\n            wait_sync        4\n            move             4, R3\n            loop_1:\n                wait_sync        4\n                wait_sync        4\n                wait             R3\n                play             0, 1, 4\n                acquire          0, R1, 1000\n                add              R1, 1, R1\n                add              R3, 4, R3\n                nop\n                jlt              R3, 100, @loop_1\n            add              R2, 3276, R2\n            nop\n            jlt              R2, 32767, @loop_0\n        loop             R0, @avg_0\n    \n"
        )

    def test_loop_variable_with_different_targets_throws_exception(
        self, loop_variable_with_different_targets: QProgram
    ):
        with pytest.raises(
            NotImplementedError, match="Variables referenced in a loop cannot be used in different types of operations."
        ):
            _ = QBloxCompiler(qprogram=loop_variable_with_different_targets, settings=Settings())
