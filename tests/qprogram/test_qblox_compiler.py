import pytest
import qpysequence as QPy

from qililab.qprogram import QBloxCompiler, QProgram, Settings
from qililab.qprogram.blocks import ForLoop
from qililab.waveforms import DragPulse, Gaussian, IQPair, Square


@pytest.fixture(name="no_loops_all_operations")
def fixture_no_loops_all_operations() -> QProgram:
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


@pytest.fixture(name="average")
def fixture_average() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    with qp.average(shots=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync()
        qp.wait(bus="readout", time=100)
        qp.play(bus="readout", waveform=readout_pair)
        qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="average_with_weights")
def fixture_acquire_loop_with_weights() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
    )
    qp = QProgram()
    with qp.average(shots=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync()
        qp.wait(bus="readout", time=100)
        qp.play(bus="readout", waveform=readout_pair)
        qp.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_weights_of_different_length")
def fixture_average_with_weights_of_different_lengths() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=500, num_sigmas=2.5),
    )
    qp = QProgram()
    with qp.average(shots=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync()
        qp.wait(bus="readout", time=100)
        qp.play(bus="readout", waveform=readout_pair)
        qp.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_for_loop")
def fixture_average_with_for_loop() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    wait_time = qp.variable(int)
    with qp.average(shots=1000):
        with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
            qp.play(bus="drive", waveform=drag_pair)
            qp.sync()
            qp.wait(bus="readout", time=wait_time)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="acquire_loop_with_for_loop_with_weights")
def fixture_acquire_loop_with_for_loop_with_weights() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
            qp.wait(bus="readout", time=wait_time)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_multiple_for_loops_and_acquires")
def fixture_average_with_multiple_for_loops_and_acquires() -> QProgram:
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    frequency = qp.variable(float)
    gain = qp.variable(float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=frequency, start=0, stop=500, step=10):
            qp.set_frequency(bus="readout", frequency=frequency)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout")
        qp.acquire(bus="readout")
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="readout", gain_path0=gain, gain_path1=gain)
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="average_with_nested_for_loops")
def fixture_average_with_nested_for_loops() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    wait_time = qp.variable(int)
    gain = qp.variable(float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1, step=0.1):
            qp.set_gain(bus="drive", gain_path0=gain, gain_path1=gain)
            with qp.for_loop(variable=wait_time, start=0, stop=100, step=4):
                qp.play(bus="drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus="readout", time=wait_time)
                qp.play(bus="readout", waveform=readout_pair)
                qp.acquire(bus="readout")
    return qp


@pytest.fixture(name="average_with_parallel_for_loops")
def fixture_average_with_parallel_for_loops() -> QProgram:
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
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
            qp.set_gain(bus="drive", gain_path0=gain, gain_path1=gain)
            qp.set_frequency(bus="readout", frequency=frequency)
            qp.play(bus="drive", waveform=drag_pair)
            qp.sync()
            qp.play(bus="readout", waveform=readout_pair)
            qp.acquire(bus="readout")
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
    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2))
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
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=no_loops_all_operations)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    set_freq         1200\n    set_ph           250000000\n    reset_ph\n    set_awg_gain     16383, 16383\n    set_awg_offs     16383, 16383\n    play             0, 1, 40\n    wait_sync        4\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    wait_sync        4\n    wait             100\n    play             0, 1, 1000\n    acquire          0, 0, 1000\n    stop\n    \n"
        )

    def test_average(self, average: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=average)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        play             0, 1, 40\n        wait_sync        4\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        wait_sync        4\n        wait             100\n        play             0, 1, 1000\n        acquire          0, 0, 1000\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_weights(self, average_with_weights: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=average_with_weights)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        play             0, 1, 40\n        wait_sync        4\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(output["readout"]._weights._weights) == 1
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        wait_sync        4\n        wait             100\n        play             0, 1, 1000\n        acquire_weighed  0, 0, 0, 0, 1000\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_weights_of_different_length_throws_exception(
        self, average_with_weights_of_different_length: QProgram
    ):
        with pytest.raises(NotImplementedError, match="Weights should have equal lengths."):
            compiler = QBloxCompiler(settings=Settings())
            _ = compiler.compile(qprogram=average_with_weights_of_different_length)

    def test_average_with_for_loop(self, average_with_for_loop: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=average_with_for_loop)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             4, R1\n        loop_0:\n            wait_sync        4\n            play             0, 1, 40\n            wait_sync        4\n            add              R1, 4, R1\n            nop\n            jlt              R1, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 24
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        wait_sync        4\n        move             4, R2\n        loop_0:\n            wait_sync        4\n            wait_sync        4\n            wait             R2\n            play             0, 1, 1000\n            acquire          0, R1, 1000\n            add              R1, 1, R1\n            add              R2, 4, R2\n            nop\n            jlt              R2, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_acquire_loop_with_for_loop_with_weights(self, acquire_loop_with_for_loop_with_weights: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=acquire_loop_with_for_loop_with_weights)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             4, R1\n        loop_0:\n            wait_sync        4\n            play             0, 1, 40\n            wait_sync        4\n            add              R1, 4, R1\n            nop\n            jlt              R1, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 24
        assert len(output["readout"]._weights._weights) == 1
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        move             0, R2\n        move             0, R3\n        wait_sync        4\n        move             4, R4\n        loop_0:\n            wait_sync        4\n            wait_sync        4\n            wait             R4\n            play             0, 1, 1000\n            acquire_weighed  0, R3, R2, R1, 1000\n            add              R3, 1, R3\n            add              R4, 4, R4\n            nop\n            jlt              R4, 100, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_multiple_for_loops_and_acquires(self, average_with_multiple_for_loops_and_acquires: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=average_with_multiple_for_loops_and_acquires)

        assert len(output) == 1
        assert "readout" in output

        for bus in output:
            assert isinstance(output[bus], QPy.Sequence)

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 3
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 50
        assert output["readout"]._acquisitions._acquisitions[1].num_bins == 1
        assert output["readout"]._acquisitions._acquisitions[2].num_bins == 10
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             51, R1\n        move             0, R2\n        wait_sync        4\n        move             0, R3\n        loop_0:\n            wait_sync        4\n            set_freq         R3\n            play             0, 1, 1000\n            acquire          0, R2, 1000\n            add              R2, 1, R2\n            add              R3, 40, R3\n            nop\n            jlt              R3, 2000, @loop_0\n        acquire          1, 50, 1000\n        move             0, R4\n        loop_1:\n            wait_sync        4\n            set_awg_gain     R4, R4\n            play             0, 1, 1000\n            acquire          2, R1, 1000\n            add              R1, 1, R1\n            add              R4, 3276, R4\n            nop\n            jlt              R4, 32767, @loop_1\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_nested_for_loops(self, average_with_nested_for_loops: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=average_with_nested_for_loops)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             0, R1\n        loop_0:\n            wait_sync        4\n            set_awg_gain     R1, R1\n            move             4, R2\n            loop_1:\n                wait_sync        4\n                play             0, 1, 40\n                wait_sync        4\n                add              R2, 4, R2\n                nop\n                jlt              R2, 100, @loop_1\n            add              R1, 3276, R1\n            nop\n            jlt              R1, 32767, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 240
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        wait_sync        4\n        move             0, R2\n        loop_0:\n            wait_sync        4\n            move             4, R3\n            loop_1:\n                wait_sync        4\n                wait_sync        4\n                wait             R3\n                play             0, 1, 1000\n                acquire          0, R1, 1000\n                add              R1, 1, R1\n                add              R3, 4, R3\n                nop\n                jlt              R3, 100, @loop_1\n            add              R2, 3276, R2\n            nop\n            jlt              R2, 32767, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_average_with_parallel_for_loops(self, average_with_parallel_for_loops: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=average_with_parallel_for_loops)

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
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        wait_sync        4\n        move             400, R1\n        move             0, R2\n        move             10, R3\n        loop_0:\n            wait_sync        4\n            set_awg_gain     R2, R2\n            play             0, 1, 40\n            wait_sync        4\n            add              R2, 3276, R2\n            add              R1, 40, R1\n            loop             R3, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

        assert len(output["readout"]._waveforms._waveforms) == 2
        assert len(output["readout"]._acquisitions._acquisitions) == 1
        assert output["readout"]._acquisitions._acquisitions[0].num_bins == 10
        assert len(output["readout"]._weights._weights) == 0
        assert output["readout"]._program._compiled
        assert (
            repr(output["readout"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    move             1000, R0\n    avg_0:\n        move             0, R1\n        wait_sync        4\n        move             400, R2\n        move             0, R3\n        move             10, R4\n        loop_0:\n            wait_sync        4\n            set_freq         R2\n            wait_sync        4\n            play             0, 1, 1000\n            acquire          0, R1, 1000\n            add              R1, 1, R1\n            add              R3, 3276, R3\n            add              R2, 40, R2\n            loop             R4, @loop_0\n        loop             R0, @avg_0\n    stop\n    \n"
        )

    def test_for_loop_variable_with_no_targets_throws_exception(self, for_loop_variable_with_no_target: QProgram):
        with pytest.raises(
            NotImplementedError, match="Variables referenced in loops should be used in at least one operation."
        ):
            compiler = QBloxCompiler(settings=Settings())
            _ = compiler.compile(qprogram=for_loop_variable_with_no_target)

    def test_for_loop_variable_with_different_targets_throws_exception(
        self, for_loop_variable_with_different_targets: QProgram
    ):
        with pytest.raises(
            NotImplementedError, match="Variables referenced in a loop cannot be used in different types of operations."
        ):
            compiler = QBloxCompiler(settings=Settings())
            _ = compiler.compile(qprogram=for_loop_variable_with_different_targets)

    def test_play_operation_with_waveforms_of_different_length_throws_exception(
        self, play_operation_with_waveforms_of_different_length: QProgram
    ):
        with pytest.raises(NotImplementedError, match="Waveforms should have equal lengths."):
            compiler = QBloxCompiler(settings=Settings())
            _ = compiler.compile(qprogram=play_operation_with_waveforms_of_different_length)

    def test_multiple_play_operations_with_same_waveform(self, multiple_play_operations_with_same_waveform: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=multiple_play_operations_with_same_waveform)

        assert len(output) == 1
        assert "drive" in output

        for bus in output:
            assert isinstance(output[bus], QPy.Sequence)

        assert len(output["drive"]._waveforms._waveforms) == 2
        assert len(output["drive"]._acquisitions._acquisitions) == 0
        assert len(output["drive"]._weights._weights) == 0
        assert output["drive"]._program._compiled
        assert (
            repr(output["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    play             0, 1, 40\n    play             0, 1, 40\n    play             0, 1, 40\n    stop\n    \n"
        )

    def test_multiple_play_operations_with_no_Q_waveform(self, multiple_play_operations_with_no_Q_waveform: QProgram):
        compiler = QBloxCompiler(settings=Settings())
        output = compiler.compile(qprogram=multiple_play_operations_with_no_Q_waveform)

        assert len(output) == 1
        assert "drive" in output

        for bus in output:
            assert isinstance(output[bus], QPy.Sequence)

        assert len(output["drive"]._waveforms._waveforms) == 2
        assert len(output["drive"]._acquisitions._acquisitions) == 0
        assert len(output["drive"]._weights._weights) == 0
        assert output["drive"]._program._compiled
        assert (
            repr(output["drive"]._program)
            == "setup:\n    wait_sync        4\n    \nmain:\n    play             0, 1, 40\n    play             0, 1, 40\n    play             0, 1, 40\n    stop\n    \n"
        )
