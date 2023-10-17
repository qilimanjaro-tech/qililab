# pylint: disable=protected-access
import pytest
import qpysequence as QPy

from qililab.qprogram import QbloxCompiler, QProgram
from qililab.qprogram.blocks import ForLoop
from qililab.waveforms import DragPair, Gaussian, IQPair, Square


@pytest.fixture(name="no_loops_all_operations")
def fixture_no_loops_all_operations() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    qp.set_frequency(bus="drive", frequency=300)
    qp.set_phase(bus="drive", phase=90)
    qp.reset_phase(bus="drive")
    qp.set_gain(bus="drive", gain=0.5)
    qp.set_offset(bus="drive", offset_path0=0.5, offset_path1=0.5)
    qp.play(bus="drive", waveform=drag_pair)
    qp.sync()
    qp.wait(bus="readout", duration=100)
    qp.play(bus="readout", waveform=readout_pair)
    qp.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="average_loop")
def fixture_average_loop() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
    )
    qp = QProgram()
    with qp.average(shots=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync()
        qp.wait(bus="readout", duration=100)
        qp.play(bus="readout", waveform=readout_pair)
        qp.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="acquire_with_weights_of_different_length")
def fixture_acquire_with_weights_of_different_lengths() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=500, num_sigmas=2.5),
    )
    qp = QProgram()
    with qp.average(shots=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync()
        qp.wait(bus="readout", duration=100)
        qp.play(bus="readout", waveform=readout_pair)
        qp.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_for_loop")
def fixture_average_with_for_loop() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    wait_time = qp.variable(int)
    with qp.average(shots=1000):
        with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
            qp.play(bus="drive", waveform=drag_pair)
            qp.sync()
            qp.wait(bus="readout", duration=wait_time)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="acquire_loop_with_for_loop_with_weights_of_same_waveform")
def fixture_acquire_loop_with_for_loop_with_weights_of_same_waveform() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
    )
    qp = QProgram()
    wait_time = qp.variable(int)
    with qp.average(shots=1000):
        with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
            qp.play(bus="drive", waveform=drag_pair)
            qp.sync()
            qp.wait(bus="readout", duration=wait_time)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_multiple_for_loops_and_acquires")
def fixture_average_with_multiple_for_loops_and_acquires() -> QProgram:
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair_0 = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    weights_pair_1 = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair_2 = IQPair(I=Square(amplitude=1.0, duration=500), Q=Square(amplitude=0.0, duration=500))
    qp = QProgram()
    frequency = qp.variable(float)
    gain = qp.variable(float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=frequency, start=0, stop=500, step=10):
            qp.set_frequency(bus="readout", frequency=frequency)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout", weights=weights_pair_0)
        qp.acquire(bus="readout", weights=weights_pair_1)
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="readout", gain=gain)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout", weights=weights_pair_2)
    return qp


@pytest.fixture(name="average_with_nested_for_loops")
def fixture_average_with_nested_for_loops() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    wait_time = qp.variable(int)
    gain = qp.variable(float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1, step=0.1):
            qp.set_gain(bus="drive", gain=gain)
            with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
                qp.play(bus="drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus="readout", duration=wait_time)
                qp.play(bus="readout", waveform=readout_pair)
                qp.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="average_with_parallel_for_loops")
def fixture_average_with_parallel_for_loops() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    frequency = qp.variable(float)
    gain = qp.variable(float)
    with qp.average(shots=1000):
        with qp.parallel(
            loops=[
                ForLoop(variable=frequency, start=100, stop=200, step=10),
                ForLoop(variable=gain, start=0, stop=1, step=0.1),
            ]
        ):
            qp.set_gain(bus="drive", gain=gain)
            qp.set_frequency(bus="readout", frequency=frequency)
            qp.play(bus="drive", waveform=drag_pair)
            qp.sync()
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="for_loop_variable_with_no_target")
def fixture_for_loop_variable_with_no_target() -> QProgram:
    qp = QProgram()
    variable = qp.variable(float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=variable, start=0, stop=100, step=4):
            qp.set_frequency(bus="drive", frequency=100)
            qp.set_phase(bus="drive", phase=90)
    return qp


@pytest.fixture(name="for_loop_variable_with_different_targets")
def fixture_for_loop_variable_with_different_targets() -> QProgram:
    qp = QProgram()
    variable = qp.variable(float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=variable, start=0, stop=100, step=4):
            qp.set_frequency(bus="drive", frequency=variable)
            qp.set_phase(bus="drive", phase=variable)
    return qp


@pytest.fixture(name="play_operation_with_waveforms_of_different_length")
def fixture_play_operation_with_waveforms_of_different_length() -> QProgram:
    qp = QProgram()
    waveform_pair = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=1.0, duration=80))
    qp.play(bus="drive", waveform=waveform_pair)
    return qp


@pytest.fixture(name="multiple_play_operations_with_same_waveform")
def fixture_multiple_play_operations_with_same_waveform() -> QProgram:
    qp = QProgram()
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2))
    return qp


@pytest.fixture(name="multiple_play_operations_with_no_Q_waveform")
def fixture_multiple_play_operations_with_no_Q_waveform() -> QProgram:
    qp = QProgram()
    gaussian = Gaussian(amplitude=1.0, duration=40, num_sigmas=4)
    qp.play(bus="drive", waveform=gaussian)
    qp.play(bus="drive", waveform=gaussian)
    qp.play(bus="drive", waveform=Gaussian(amplitude=1.0, duration=40, num_sigmas=4))
    return qp


class TestQBloxCompiler:
    def test_no_loops_all_operations(self, no_loops_all_operations: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=no_loops_all_operations)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    set_freq         1200\n    set_ph           250000000\n    reset_ph\n    set_awg_gain     16383, 16383\n    set_awg_offs     16383, 16383\n    play             0, 1, 40\n    wait_sync        4\n    stop\n    \n"
        )

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    wait_sync        4\n    wait             100\n    play             0, 1, 1000\n    acquire_weighed  0, 0, 0, 1, 2000\n    stop\n    \n"
        )

    def test_average_with_weights(self, average_loop: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=average_loop)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        play             0, 1, 40\n        wait_sync        4\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(sequences["readout"]._weights._weights) == 1
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        wait_sync        4\n        wait             100\n        play             0, 1, 1000\n        acquire_weighed  0, 0, 0, 0, 1000\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_acquire_with_weights_of_different_length_throws_exception(
        self, acquire_with_weights_of_different_length: QProgram
    ):
        with pytest.raises(NotImplementedError, match="Weights should have equal lengths."):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=acquire_with_weights_of_different_length)

    def test_average_with_for_loop(self, average_with_for_loop: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=average_with_for_loop)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             4, R1\n        loop_0:\n            wait_sync        4\n            play             0, 1, 40\n            wait_sync        4\n            add              R1, 4, R1\n            nop\n            jlt              R1, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 24
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             1, R1\n        move             0, R2\n        move             0, R3\n        wait_sync        4\n        move             4, R4\n        loop_0:\n            wait_sync        4\n            wait_sync        4\n            wait             R4\n            play             0, 1, 1000\n            acquire_weighed  0, R3, R2, R1, 2000\n            add              R3, 1, R3\n            add              R4, 4, R4\n            nop\n            jlt              R4, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_acquire_loop_with_for_loop_with_weights_of_same_waveform(
        self, acquire_loop_with_for_loop_with_weights_of_same_waveform: QProgram
    ):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=acquire_loop_with_for_loop_with_weights_of_same_waveform)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             4, R1\n        loop_0:\n            wait_sync        4\n            play             0, 1, 40\n            wait_sync        4\n            add              R1, 4, R1\n            nop\n            jlt              R1, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 24
        assert len(sequences["readout"]._weights._weights) == 1
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        move             0, R2\n        move             0, R3\n        wait_sync        4\n        move             4, R4\n        loop_0:\n            wait_sync        4\n            wait_sync        4\n            wait             R4\n            play             0, 1, 1000\n            acquire_weighed  0, R3, R2, R1, 1000\n            add              R3, 1, R3\n            add              R4, 4, R4\n            nop\n            jlt              R4, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_multiple_for_loops_and_acquires(self, average_with_multiple_for_loops_and_acquires: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=average_with_multiple_for_loops_and_acquires)

        assert len(sequences) == 1
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 3
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 50
        assert sequences["readout"]._acquisitions._acquisitions[1].num_bins == 1
        assert sequences["readout"]._acquisitions._acquisitions[2].num_bins == 10
        assert len(sequences["readout"]._weights._weights) == 6
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             5, R1\n        move             4, R2\n        move             51, R3\n        move             1, R4\n        move             0, R5\n        move             0, R6\n        wait_sync        4\n        move             0, R7\n        loop_0:\n            wait_sync        4\n            set_freq         R7\n            play             0, 1, 1000\n            acquire_weighed  0, R6, R5, R4, 2000\n            add              R6, 1, R6\n            add              R7, 40, R7\n            nop\n            jlt              R7, 2000, @loop_0\n        acquire_weighed  1, 50, 2, 3, 1000\n        move             0, R8\n        loop_1:\n            wait_sync        4\n            set_awg_gain     R8, R8\n            play             0, 1, 1000\n            acquire_weighed  2, R3, R2, R1, 500\n            add              R3, 1, R3\n            add              R8, 3276, R8\n            nop\n            jlt              R8, 32767, @loop_1\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_nested_for_loops(self, average_with_nested_for_loops: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=average_with_nested_for_loops)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             0, R1\n        loop_0:\n            wait_sync        4\n            set_awg_gain     R1, R1\n            move             4, R2\n            loop_1:\n                wait_sync        4\n                play             0, 1, 40\n                wait_sync        4\n                add              R2, 4, R2\n                nop\n                jlt              R2, 100, @loop_1\n            add              R1, 3276, R1\n            nop\n            jlt              R1, 32767, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 240
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             1, R1\n        move             0, R2\n        move             0, R3\n        wait_sync        4\n        move             0, R4\n        loop_0:\n            wait_sync        4\n            move             4, R5\n            loop_1:\n                wait_sync        4\n                wait_sync        4\n                wait             R5\n                play             0, 1, 1000\n                acquire_weighed  0, R3, R2, R1, 2000\n                add              R3, 1, R3\n                add              R5, 4, R5\n                nop\n                jlt              R5, 100, @loop_1\n            add              R4, 3276, R4\n            nop\n            jlt              R4, 32767, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_parallel_for_loops(self, average_with_parallel_for_loops: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=average_with_parallel_for_loops)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             400, R1\n        move             0, R2\n        move             10, R3\n        loop_0:\n            wait_sync        4\n            set_awg_gain     R2, R2\n            play             0, 1, 40\n            wait_sync        4\n            add              R2, 3276, R2\n            add              R1, 40, R1\n            loop             R3, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 10
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled
        assert (
            repr(sequences["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             1, R1\n        move             0, R2\n        move             0, R3\n        wait_sync        4\n        move             400, R4\n        move             0, R5\n        move             10, R6\n        loop_0:\n            wait_sync        4\n            set_freq         R4\n            wait_sync        4\n            play             0, 1, 1000\n            acquire_weighed  0, R3, R2, R1, 2000\n            add              R3, 1, R3\n            add              R5, 3276, R5\n            add              R4, 40, R4\n            loop             R6, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_for_loop_variable_with_no_targets_throws_exception(self, for_loop_variable_with_no_target: QProgram):
        with pytest.raises(
            NotImplementedError, match="Variables referenced in loops should be used in at least one operation."
        ):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=for_loop_variable_with_no_target)

    def test_for_loop_variable_with_different_targets_throws_exception(
        self, for_loop_variable_with_different_targets: QProgram
    ):
        with pytest.raises(
            NotImplementedError, match="Variables referenced in a loop cannot be used in different types of operations."
        ):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=for_loop_variable_with_different_targets)

    def test_play_operation_with_waveforms_of_different_length_throws_exception(
        self, play_operation_with_waveforms_of_different_length: QProgram
    ):
        with pytest.raises(NotImplementedError, match="Waveforms should have equal lengths."):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=play_operation_with_waveforms_of_different_length)

    def test_multiple_play_operations_with_same_waveform(self, multiple_play_operations_with_same_waveform: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=multiple_play_operations_with_same_waveform)

        assert len(sequences) == 1
        assert "drive" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    play             0, 1, 40\n    play             0, 1, 40\n    play             0, 1, 40\n    stop\n    \n"
        )

    def test_multiple_play_operations_with_no_Q_waveform(self, multiple_play_operations_with_no_Q_waveform: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=multiple_play_operations_with_no_Q_waveform)

        assert len(sequences) == 1
        assert "drive" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 2
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled
        assert (
            repr(sequences["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    play             0, 1, 40\n    play             0, 1, 40\n    play             0, 1, 40\n    stop\n    \n"
        )
