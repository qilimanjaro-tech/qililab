# pylint: disable=protected-access
import pytest
import qpysequence as QPy

from qililab import Domain, DragPair, Gaussian, IQPair, QbloxCompiler, QProgram, Square
from qililab.qprogram.blocks import ForLoop
from tests.test_utils import is_q1asm_equal


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
    gain = qp.variable(Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
            qp.play(bus="drive", waveform=drag_pair)
            qp.set_gain(bus="readout", gain=gain)
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
    gain = qp.variable(Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
            qp.play(bus="drive", waveform=drag_pair)
            qp.set_gain(bus="readout", gain=gain)
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
    frequency = qp.variable(Domain.Frequency)
    gain = qp.variable(Domain.Voltage)
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
    frequency = qp.variable(Domain.Frequency)
    gain = qp.variable(Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1, step=0.1):
            qp.set_gain(bus="drive", gain=gain)
            with qp.for_loop(variable=frequency, start=0, stop=500, step=10):
                qp.play(bus="drive", waveform=drag_pair)
                qp.sync()
                qp.set_frequency(bus="readout", frequency=frequency)
                qp.play(bus="readout", waveform=readout_pair)
                qp.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="average_with_parallel_for_loops")
def fixture_average_with_parallel_for_loops() -> QProgram:
    drag_pair = DragPair(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    frequency = qp.variable(Domain.Frequency)
    gain = qp.variable(Domain.Voltage)
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
    variable = qp.variable(Domain.Scalar, float)
    with qp.average(shots=1000):
        with qp.for_loop(variable=variable, start=0, stop=100, step=4):
            qp.set_frequency(bus="drive", frequency=100)
            qp.set_phase(bus="drive", phase=90)
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

        drive_str = """
            setup:
                            wait_sync        4

            main:
                            set_freq         1200
                            set_ph           250000000
                            reset_ph
                            set_awg_gain     16383, 16383
                            set_awg_offs     16383, 16383
                            play             0, 1, 40
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        readout_str = """
            setup:
                            wait_sync        4

            main:
                            wait             40
                            wait             100
                            play             0, 1, 1000
                            acquire_weighed  0, 0, 0, 1, 2000
                            stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_loop(self, average_loop: QProgram):
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

        drive_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            play             0, 1, 40
                            wait             2100
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(sequences["readout"]._weights._weights) == 1
        assert sequences["readout"]._program._compiled

        readout_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            wait             40
                            wait             100
                            play             0, 1, 1000
                            acquire_weighed  0, 0, 0, 0, 1000
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

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

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             11, R1
                            move             0, R2
            loop_0:
                            play             0, 1, 40
                            wait             2960
                            add              R2, 3276, R2
                            loop             R1, @loop_0
                            loop             R0, @avg_0
                            stop
        """
        readout_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             1, R1
                            move             0, R2
                            move             0, R3
                            move             11, R4
                            move             0, R5
            loop_0:
                            set_awg_gain     R5, R5
                            play             0, 1, 1000
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R5, 3276, R5
                            loop             R4, @loop_0
                            nop
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

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

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
        assert len(sequences["readout"]._weights._weights) == 1
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             11, R1
                            move             0, R2
            loop_0:
                            play             0, 1, 40
                            wait             1960
                            add              R2, 3276, R2
                            loop             R1, @loop_0
                            loop             R0, @avg_0
                            stop
        """
        readout_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             0, R1
                            move             0, R2
                            move             0, R3
                            move             11, R4
                            move             0, R5
            loop_0:
                            set_awg_gain     R5, R5
                            play             0, 1, 1000
                            acquire_weighed  0, R3, R2, R1, 1000
                            add              R3, 1, R3
                            add              R5, 3276, R5
                            loop             R4, @loop_0
                            nop
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_with_multiple_for_loops_and_acquires(self, average_with_multiple_for_loops_and_acquires: QProgram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(qprogram=average_with_multiple_for_loops_and_acquires)

        assert len(sequences) == 1
        assert "readout" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 3
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 51
        assert sequences["readout"]._acquisitions._acquisitions[1].num_bins == 1
        assert sequences["readout"]._acquisitions._acquisitions[2].num_bins == 11
        assert len(sequences["readout"]._weights._weights) == 6
        assert sequences["readout"]._program._compiled

        readout_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             5, R1
                            move             4, R2
                            move             0, R3
                            move             1, R4
                            move             0, R5
                            move             0, R6
                            move             51, R7
                            move             0, R8
            loop_0:
                            set_freq         R8
                            play             0, 1, 1000
                            acquire_weighed  0, R6, R5, R4, 2000
                            add              R6, 1, R6
                            add              R8, 40, R8
                            loop             R7, @loop_0
                            nop
                            acquire_weighed  1, 0, 2, 3, 1000
                            move             11, R9
                            move             0, R10
                            nop
            loop_1:
                            set_awg_gain     R10, R10
                            play             0, 1, 1000
                            acquire_weighed  2, R3, R2, R1, 500
                            add              R3, 1, R3
                            add              R10, 3276, R10
                            loop             R9, @loop_1
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

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

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 561
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             11, R1
                            move             0, R2
            loop_0:
                            set_awg_gain     R2, R2
                            move             51, R3
                            move             0, R4
            loop_1:
                            play             0, 1, 40
                            wait             3000
                            add              R4, 40, R4
                            loop             R3, @loop_1
                            add              R2, 3276, R2
                            loop             R1, @loop_0
                            nop
                            loop             R0, @avg_0
                            stop
        """
        readout_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             1, R1
                            move             0, R2
                            move             0, R3
                            move             11, R4
                            move             0, R5
            loop_0:
                            move             51, R6
                            move             0, R7
            loop_1:
                            wait             40
                            set_freq         R7
                            play             0, 1, 1000
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R7, 40, R7
                            loop             R6, @loop_1
                            add              R5, 3276, R5
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

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

        assert len(sequences["readout"]._waveforms._waveforms) == 2
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             11, R1
                            move             400, R2
                            move             0, R3
            loop_0:
                            set_awg_gain     R3, R3
                            play             0, 1, 40
                            wait             3000
                            add              R2, 40, R2
                            add              R3, 3276, R3
                            loop             R1, @loop_0
                            nop
                            loop             R0, @avg_0
                            stop
        """
        readout_str = """
            setup:
                wait_sync        4

            main:
                            move             1000, R0
            avg_0:
                            move             1, R1
                            move             0, R2
                            move             0, R3
                            move             11, R4
                            move             400, R5
                            move             0, R6
            loop_0:
                            set_freq         R5
                            wait             40
                            play             0, 1, 1000
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R5, 40, R5
                            add              R6, 3276, R6
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_for_loop_variable_with_no_targets_throws_exception(self, for_loop_variable_with_no_target: QProgram):
        with pytest.raises(
            NotImplementedError, match="Variables referenced in loops should be used in at least one operation."
        ):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=for_loop_variable_with_no_target)

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

        drive_str = """
            setup:
                wait_sync        4

            main:
                            play             0, 1, 40
                            play             0, 1, 40
                            play             0, 1, 40
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

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

        drive_str = """
            setup:
                wait_sync        4

            main:
                            play             0, 1, 40
                            play             0, 1, 40
                            play             0, 1, 40
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
