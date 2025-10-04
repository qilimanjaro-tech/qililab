import re
from unittest.mock import patch

import numpy as np
import pytest
import qpysequence as QPy

from qililab import Calibration, Domain, FlatTop, Gaussian, IQPair, IQDrag, QbloxCompiler, QProgram, Square
from qililab.qprogram.blocks import ForLoop
from tests.test_utils import is_q1asm_equal
from qililab.config import logger
import logging


def setup_q1asm(marker: str):
    return f"""
        setup:
                wait_sync        4
                set_mrk          {marker}
                upd_param        4
    """


@pytest.fixture(name="calibration")
def fixture_calibration() -> Calibration:
    calibration = Calibration()
    calibration.add_waveform(bus="drive_q0", name="Xpi", waveform=Square(1.0, 100))
    calibration.add_waveform(bus="drive_q1", name="Xpi", waveform=Square(1.0, 150))
    calibration.add_waveform(bus="drive_q2", name="Xpi", waveform=Square(1.0, 200))

    return calibration


@pytest.fixture(name="play_named_operation")
def fixture_play_named_operation() -> QProgram:
    drag_wf = IQDrag(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.play(bus="drive", waveform="Xpi")
    qp.play(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="measurement_blocked_operation")
def fixture_measurement_blocked_operation() -> QProgram:
    drag_wf = IQDrag(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    with qp.block():
        qp.play(bus="drive", waveform=drag_wf)
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)

    return qp


@pytest.fixture(name="no_loops_all_operations")
def fixture_no_loops_all_operations() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    qp.set_frequency(bus="drive", frequency=300)
    qp.set_phase(bus="drive", phase=np.pi / 2)
    qp.reset_phase(bus="drive")
    qp.set_gain(bus="drive", gain=0.5)
    qp.set_offset(bus="drive", offset_path0=0.5, offset_path1=0.5)
    qp.play(bus="drive", waveform=drag_pair)
    qp.sync()
    qp.wait(bus="readout", duration=100)
    qp.play(bus="readout", waveform=readout_pair)
    qp.qblox.set_markers(bus="readout", mask="0111")
    qp.qblox.play(bus="readout", waveform=readout_pair, wait_time=4)
    qp.qblox.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="offset_no_path1")
def fixture_offset_no_path1() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    qp.set_offset(bus="drive", offset_path0=0.5)
    qp.play(bus="drive", waveform=drag_pair)
    return qp


@pytest.fixture(name="dynamic_wait")
def fixture_dynamic_wait() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration)
    return qp


@pytest.fixture(name="dynamic_wait_multiple_buses")
def fixture_dynamic_wait_multiple_buses() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="readout", duration=duration)
        qp.play(bus="readout", waveform=drag_pair)
    return qp


@pytest.fixture(name="dynamic_wait_multiple_buses_with_disable_autosync")
def fixture_dynamic_wait_multiple_buses_with_disable_autosync() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    qp.qblox.disable_autosync = True
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="readout", duration=duration)
        qp.play(bus="readout", waveform=drag_pair)
    return qp


@pytest.fixture(name="sync_with_dynamic_wait")
def fixture_sync_with_dynamic_wait() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.play(bus="readout", waveform=drag_pair)
    return qp


@pytest.fixture(name="infinite_loop")
def fixture_infinite_loop() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    with qp.infinite_loop():
        qp.play(bus="drive", waveform=drag_pair)
    return qp


@pytest.fixture(name="average_loop")
def fixture_average_loop() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
        qp.qblox.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_loop_long_wait")
def fixture_average_loop_long_wait() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
    )
    qp = QProgram()
    with qp.average(shots=1000):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=100_000)
        qp.sync()
        qp.play(bus="readout", waveform=readout_pair)
        qp.qblox.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="acquire_with_weights_of_different_length")
def fixture_acquire_with_weights_of_different_lengths() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
        qp.qblox.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_for_loop")
def fixture_average_with_for_loop() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
            qp.play(bus="drive", waveform=drag_pair)
            qp.set_gain(bus="readout", gain=gain)
            qp.play(bus="readout", waveform=readout_pair)
            qp.qblox.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="average_with_for_loop_nshots")
def fixture_average_with_for_loop_nshots() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    nshots = qp.variable(label="nshots", domain=Domain.Scalar, type=int)
    with qp.average(shots=1000):
        with qp.for_loop(variable=nshots, start=0, stop=2, step=1):
            qp.play(bus="drive", waveform=drag_pair)
            qp.play(bus="readout", waveform=readout_pair)
            qp.qblox.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="acquire_loop_with_for_loop_with_weights_of_same_waveform")
def fixture_acquire_loop_with_for_loop_with_weights_of_same_waveform() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights = IQPair(
        I=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
        Q=Gaussian(amplitude=1.0, duration=1000, num_sigmas=2.5),
    )
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
            qp.play(bus="drive", waveform=drag_pair)
            qp.set_gain(bus="readout", gain=gain)
            qp.play(bus="readout", waveform=readout_pair)
            qp.qblox.acquire(bus="readout", weights=weights)
    return qp


@pytest.fixture(name="average_with_multiple_for_loops_and_acquires")
def fixture_average_with_multiple_for_loops_and_acquires() -> QProgram:
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair_0 = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    weights_pair_1 = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair_2 = IQPair(I=Square(amplitude=1.0, duration=500), Q=Square(amplitude=0.0, duration=500))
    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=frequency, start=0, stop=500, step=10):
            qp.set_frequency(bus="readout", frequency=frequency)
            qp.play(bus="readout", waveform=readout_pair)
            qp.qblox.acquire(bus="readout", weights=weights_pair_0)
        qp.qblox.acquire(bus="readout", weights=weights_pair_1)
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="readout", gain=gain)
            qp.play(bus="readout", waveform=readout_pair)
            qp.qblox.acquire(bus="readout", weights=weights_pair_2)
    return qp


@pytest.fixture(name="average_with_nested_for_loops")
def fixture_average_with_nested_for_loops() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.average(shots=1000):
        with qp.for_loop(variable=gain, start=0, stop=1, step=0.1):
            qp.set_gain(bus="drive", gain=gain)
            with qp.for_loop(variable=frequency, start=0, stop=500, step=10):
                qp.play(bus="drive", waveform=drag_pair)
                qp.sync()
                qp.set_frequency(bus="readout", frequency=frequency)
                qp.play(bus="readout", waveform=readout_pair)
                qp.qblox.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="measure_program")
def fixture_measure_program() -> QProgram:
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)
    return qp


@pytest.fixture(name="average_with_parallel_for_loops")
def fixture_average_with_parallel_for_loops() -> QProgram:
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    gain = qp.variable(label="gain", domain=Domain.Voltage)
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
            qp.qblox.acquire(bus="readout", weights=weights_pair)
    return qp


@pytest.fixture(name="for_loop_variable_with_no_target")
def fixture_for_loop_variable_with_no_target() -> QProgram:
    qp = QProgram()
    variable = qp.variable(label="float_scalar", domain=Domain.Scalar, type=float)
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
    drag_pair = IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2))
    return qp


@pytest.fixture(name="multiple_play_operations_with_no_Q_waveform")
def fixture_multiple_play_operations_with_no_Q_waveform() -> QProgram:
    qp = QProgram()
    gaussian = Gaussian(amplitude=1.0, duration=40, num_sigmas=4)
    qp.play(bus="drive", waveform=gaussian)
    qp.play(bus="drive", waveform=gaussian)
    qp.play(bus="drive", waveform=Gaussian(amplitude=1.0, duration=40, num_sigmas=4))
    return qp


@pytest.fixture(name="play_square_waveforms_with_optimization")
def fixture_play_square_waveforms_with_optimization() -> QProgram:
    qp = QProgram()
    qp.play(bus="drive", waveform=IQPair(I=Square(1.0, duration=25), Q=Square(0.5, duration=25)))
    qp.play(bus="drive", waveform=Square(1.0, duration=50))
    qp.play(bus="drive", waveform=Square(1.0, duration=500))
    qp.play(bus="drive", waveform=IQPair(I=Square(1.0, duration=500), Q=Square(0.0, duration=500)))
    qp.play(bus="drive", waveform=Square(1.0, duration=50_000))
    qp.play(bus="drive", waveform=Square(1.0, duration=9790223))
    qp.play(bus="drive", waveform=IQPair(I=Square(1.0, duration=9790223), Q=Square(1.0, duration=9790223)))
    qp.play(bus="drive", waveform=Square(0.5, duration=1234567))
    return qp


@pytest.fixture(name="play_square_smooth_waveforms_with_optimization")
def fixture_play_square_smooth_waveforms_with_optimization() -> QProgram:
    qp = QProgram()
    qp.play(
        bus="drive",
        waveform=IQPair(
            I=FlatTop(1.0, duration=25, smooth_duration=10), Q=FlatTop(0.5, duration=25, smooth_duration=10)
        ),
    )
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=50, smooth_duration=10))
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=500, smooth_duration=10))
    qp.play(
        bus="drive",
        waveform=IQPair(
            I=FlatTop(1.0, duration=25, smooth_duration=1, buffer=1),
            Q=FlatTop(0.5, duration=25, smooth_duration=1, buffer=1),
        ),
    )
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=50, smooth_duration=1, buffer=1))
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=104, smooth_duration=1, buffer=1))
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=500, smooth_duration=1, buffer=1))
    qp.play(
        bus="drive",
        waveform=IQPair(
            I=FlatTop(1.0, duration=500, smooth_duration=10), Q=FlatTop(0.5, duration=500, smooth_duration=10)
        ),
    )
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=50_000, smooth_duration=10))
    qp.play(bus="drive", waveform=FlatTop(1.0, duration=9790223, smooth_duration=10))
    qp.play(
        bus="drive",
        waveform=IQPair(
            I=FlatTop(1.0, duration=9790223, smooth_duration=10), Q=FlatTop(1.0, duration=9790223, smooth_duration=10)
        ),
    )
    qp.play(bus="drive", waveform=FlatTop(0.5, duration=1234567, smooth_duration=10))
    qp.play(
        bus="drive",
        waveform=IQPair(
            I=FlatTop(1.0, duration=1234567, smooth_duration=10), Q=FlatTop(1.0, duration=1234567, smooth_duration=10)
        ),
    )
    return qp


@pytest.fixture(name="play_operation_with_variable_in_waveform")
def fixture_play_operation_with_variable_in_waveform() -> QProgram:
    qp = QProgram()
    amplitude = qp.variable(label="amplitude", domain=Domain.Voltage)
    qp.play(bus="drive", waveform=Square(amplitude=amplitude, duration=100))
    return qp


@pytest.fixture(name="update_latched_param")
def update_latched_param() -> QProgram:
    qp = QProgram()
    qp.set_offset("drive", 1, 0)
    qp.wait(bus="drive", duration=0)
    qp.play(bus="drive", waveform=Square(amplitude=1, duration=100))
    qp.set_phase("drive", 1)
    qp.wait(bus="drive", duration=4)
    qp.play(bus="drive", waveform=Square(amplitude=1, duration=100))
    qp.set_gain("drive", 1)
    qp.wait(bus="drive", duration=100)
    qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
    qp.set_frequency("drive", 1e6)
    qp.wait(bus="drive", duration=100000)
    qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
    qp.set_gain("drive", 1)
    qp.wait(bus="drive", duration=4)
    qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
    qp.set_offset("drive", 1, 0)
    qp.wait(bus="drive", duration=6)
    return qp

@pytest.fixture(name="wait_comprised_between_65532_65535")
def fixture_wait_comprised_between_65532_65535() -> QProgram:
    qp = QProgram()
    qp.wait("drive",duration=65532*2)
    qp.play("drive", Square(1,20))
    qp.wait(bus="drive", duration=65532)
    qp.play("drive", Square(1,20))
    qp.wait(bus="drive", duration=65534)

    return qp


class TestQBloxCompiler:
    def test_play_named_operation_and_bus_mapping(self, play_named_operation: QProgram, calibration: Calibration):
        compiler = QbloxCompiler()
        output = compiler.compile(
            qprogram=play_named_operation, bus_mapping={"drive": "drive_q0"}, calibration=calibration
        )

        assert len(output.sequences) == 1
        assert "drive_q0" in output.sequences
        assert isinstance(output.sequences["drive_q0"], QPy.Sequence)

    def test_block_handlers(self, measurement_blocked_operation: QProgram, calibration: Calibration):
        drag_wf = IQDrag(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
        readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
        weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qp_no_block = QProgram()
        qp_no_block.play(bus="drive", waveform=drag_wf)
        qp_no_block.measure(bus="readout", waveform=readout_pair, weights=weights_pair)

        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=measurement_blocked_operation)

        sequences_no_block, _ = compiler.compile(qprogram=qp_no_block)
        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        drive_str = """
                setup:
                                wait_sync        4
                                set_mrk          0
                                upd_param        4

                main:
                                play             0, 1, 100
                                set_mrk          0
                                upd_param        4
                                stop
            """
        assert is_q1asm_equal(sequences["drive"]._program, drive_str)
        assert is_q1asm_equal(sequences["drive"]._program, sequences_no_block["drive"]._program)

    def test_play_named_operation_raises_error_if_operations_not_in_calibration(self, play_named_operation: QProgram):
        calibration = Calibration()
        compiler = QbloxCompiler()
        with pytest.raises(RuntimeError):
            _ = compiler.compile(play_named_operation, bus_mapping={"drive": "drive_q0"}, calibration=calibration)

    def test_no_loops_all_operations(self, no_loops_all_operations: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=no_loops_all_operations)

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
                            set_mrk          0
                            upd_param        4

            main:
                            set_freq         1200
                            set_freq         1200
                            set_ph           250000000
                            reset_ph
                            set_awg_gain     16383, 16383
                            set_awg_gain     16383, 16383
                            set_awg_offs     16383, 16383
                            play             0, 1, 40
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

        assert len(sequences["readout"]._waveforms._waveforms) == 4
        assert len(sequences["readout"]._acquisitions._acquisitions) == 1
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            wait             140
                            move             10, R0
            square_0:
                            play             0, 1, 100
                            loop             R0, @square_0
                            set_mrk          7
                            play             2, 3, 4
                            acquire_weighed  0, 0, 0, 1, 2000
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_set_offset_without_path_1_throws_exception(self, caplog, offset_no_path1: QProgram):
        compiler = QbloxCompiler()
        with caplog.at_level(logging.WARNING):
            _ = compiler.compile(qprogram=offset_no_path1)
        assert (
            "Qblox requires an offset for the two paths, the offset of the second path has been set to the same as the first path."
            in caplog.text
        )

    def test_dynamic_wait(self, dynamic_wait: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_wait)

        assert len(sequences) == 1
        assert "drive" in sequences

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             11, R0
                            move             100, R1
            loop_0:
                            play             0, 1, 40
                            wait             R1
                            add              R1, 10, R1
                            loop             R0, @loop_0
                            set_mrk          0
                            upd_param        4
                            stop
        """

        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_dynamic_wait_multiple_buses_with_disable_autosync(
        self, dynamic_wait_multiple_buses_with_disable_autosync: QProgram
    ):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_wait_multiple_buses_with_disable_autosync)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             11, R0
                            move             100, R1
            loop_0:
                            play             0, 1, 40
                            add              R1, 10, R1
                            loop             R0, @loop_0
                            set_mrk          0
                            upd_param        4
                            stop
        """

        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             11, R0
                            move             100, R1
            loop_0:
                            wait             R1
                            play             0, 1, 40
                            add              R1, 10, R1
                            loop             R0, @loop_0
                            nop
                            set_mrk          0
                            upd_param        4
                            stop
        """

        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_dynamic_wait_multiple_buses_throws_exception(self, dynamic_wait_multiple_buses: QProgram):
        with pytest.raises(NotImplementedError, match="Dynamic syncing is not implemented yet."):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=dynamic_wait_multiple_buses)

    def test_sync_operation_with_dynamic_timings_throws_exception(self, sync_with_dynamic_wait: QProgram):
        with pytest.raises(NotImplementedError, match="Dynamic syncing is not implemented yet."):
            compiler = QbloxCompiler()
            _ = compiler.compile(qprogram=sync_with_dynamic_wait)

    def test_average_with_long_wait(self, average_loop_long_wait: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_loop_long_wait)

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
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
        assert len(sequences["readout"]._weights._weights) == 1
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4
            main:
                            move             1000, R0
            avg_0:
                            play             0, 1, 40
                            wait             65532
                            wait             36468
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """

        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            wait             65532
                            wait             34508
                            move             10, R1
            square_0:
                            play             0, 1, 100
                            loop             R1, @square_0
                            acquire_weighed  0, 0, 0, 0, 1000
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_infinite_loop(self, infinite_loop: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=infinite_loop)

        assert len(sequences) == 1
        assert "drive" in sequences

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
            infinite_loop_0:
                            play             0, 1, 40
                            jmp              @infinite_loop_0
                            set_mrk          0
                            upd_param        4
                            stop
        """

        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_average_loop(self, average_loop: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_loop)

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
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            play             0, 1, 40
                            wait             2100
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
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
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            wait             140
                            move             10, R1
            square_0:
                            play             0, 1, 100
                            loop             R1, @square_0
                            acquire_weighed  0, 0, 0, 0, 1000
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_with_for_loop_variable_does_nothing(self, average_with_for_loop_nshots: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_for_loop_nshots)

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
        assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 3
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             3, R1
                            move             0, R2
            loop_0:
                            play             0, 1, 40
                            wait             2960
                            add              R2, 1, R2
                            loop             R1, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                wait_sync        4
                set_mrk          0
                upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             1, R1
                            move             0, R2
                            move             0, R3
                            move             3, R4
                            move             0, R5
            loop_0:
                            move             10, R6
            square_0:
                            play             0, 1, 100
                            loop             R6, @square_0
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R5, 1, R5
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_with_for_loop(self, average_with_for_loop: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_for_loop)

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
                            set_mrk          0
                            upd_param        4

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
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

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
                            set_awg_gain     R5, R5
                            move             10, R6
            square_0:
                            play             0, 1, 100
                            loop             R6, @square_0
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R5, 3276, R5
                            loop             R4, @loop_0
                            nop
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_measure_calls_play_acquire(self, measure_program):
        compiler = QbloxCompiler()

        # Test measure with default time of flight
        with (
            patch.object(QbloxCompiler, "_handle_play") as handle_play,
            patch.object(QbloxCompiler, "_handle_acquire") as handle_acquire,
        ):
            compiler.compile(measure_program)

            measure = measure_program.body.elements[0]
            assert handle_play.call_count == 1
            assert handle_acquire.call_count == 1
            assert handle_play.call_args[0][0].bus == measure.bus
            assert handle_play.call_args[0][0].waveform == measure.waveform
            assert handle_play.call_args[0][0].wait_time == QbloxCompiler.minimum_wait_duration
            assert handle_acquire.call_args[0][0].bus == measure.bus
            assert handle_acquire.call_args[0][0].weights == measure.weights

        # Test measure with provided time of flight
        with (
            patch.object(QbloxCompiler, "_handle_play") as handle_play,
            patch.object(QbloxCompiler, "_handle_acquire") as handle_acquire,
        ):
            compiler.compile(measure_program, times_of_flight={"readout": 123})

            measure = measure_program.body.elements[0]
            assert handle_play.call_count == 1
            assert handle_acquire.call_count == 1
            assert handle_play.call_args[0][0].bus == measure.bus
            assert handle_play.call_args[0][0].waveform == measure.waveform
            assert handle_play.call_args[0][0].wait_time == 123
            assert handle_acquire.call_args[0][0].bus == measure.bus
            assert handle_acquire.call_args[0][0].weights == measure.weights

    def test_acquire_loop_with_for_loop_with_weights_of_same_waveform(
        self, acquire_loop_with_for_loop_with_weights_of_same_waveform: QProgram
    ):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=acquire_loop_with_for_loop_with_weights_of_same_waveform)

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
                            set_mrk          0
                            upd_param        4

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
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             0, R1
                            move             0, R2
                            move             11, R3
                            move             0, R4
            loop_0:
                            set_awg_gain     R4, R4
                            set_awg_gain     R4, R4
                            move             10, R5
            square_0:
                            play             0, 1, 100
                            loop             R5, @square_0
                            acquire_weighed  0, R2, R1, R1, 1000
                            add              R2, 1, R2
                            add              R4, 3276, R4
                            loop             R3, @loop_0
                            nop
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_with_multiple_for_loops_and_acquires(self, average_with_multiple_for_loops_and_acquires: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_multiple_for_loops_and_acquires)

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
                            set_mrk          0
                            upd_param        4

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
                            set_freq         R8
                            move             10, R9
            square_0:
                            play             0, 1, 100
                            loop             R9, @square_0
                            acquire_weighed  0, R6, R5, R4, 2000
                            add              R6, 1, R6
                            add              R8, 40, R8
                            loop             R7, @loop_0
                            nop
                            acquire_weighed  1, 0, 2, 3, 1000
                            move             11, R10
                            move             0, R11
                            nop
            loop_1:
                            set_awg_gain     R11, R11
                            set_awg_gain     R11, R11
                            move             10, R12
            square_1:
                            play             0, 1, 100
                            loop             R12, @square_1
                            acquire_weighed  2, R3, R2, R1, 500
                            add              R3, 1, R3
                            add              R11, 3276, R11
                            loop             R10, @loop_1
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_with_nested_for_loops(self, average_with_nested_for_loops: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_nested_for_loops)

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
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             11, R1
                            move             0, R2
            loop_0:
                            set_awg_gain     R2, R2
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
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

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
                            set_freq         R7
                            move             10, R8
            square_0:
                            play             0, 1, 100
                            loop             R8, @square_0
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R7, 40, R7
                            loop             R6, @loop_1
                            add              R5, 3276, R5
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_average_with_parallel_for_loops(self, average_with_parallel_for_loops: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_parallel_for_loops)

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
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             11, R1
                            move             400, R2
                            move             0, R3
            loop_0:
                            set_awg_gain     R3, R3
                            set_awg_gain     R3, R3
                            play             0, 1, 40
                            wait             3000
                            add              R2, 40, R2
                            add              R3, 3276, R3
                            loop             R1, @loop_0
                            nop
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

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
set_freq         R5
                            upd_param        4
                            wait             36
                            move             10, R7
            square_0:
                            play             0, 1, 100
                            loop             R7, @square_0
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R5, 40, R5
                            add              R6, 3276, R6
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_multiple_play_operations_with_same_waveform(self, multiple_play_operations_with_same_waveform: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=multiple_play_operations_with_same_waveform)

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
                            set_mrk          0
                            upd_param        4

            main:
                            play             0, 1, 40
                            play             0, 1, 40
                            play             0, 1, 40
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_multiple_play_operations_with_no_Q_waveform(self, multiple_play_operations_with_no_Q_waveform: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=multiple_play_operations_with_no_Q_waveform)

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
                            set_mrk          0
                            upd_param        4

            main:
                            play             0, 1, 40
                            play             0, 1, 40
                            play             0, 1, 40
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_play_square_waveforms_with_optimization(self, play_square_waveforms_with_optimization: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=play_square_waveforms_with_optimization)

        assert len(sequences["drive"]._waveforms._waveforms) == 11
        assert sequences["drive"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            play             0, 1, 25
                            play             2, 3, 50
                            move             5, R0
            square_0:
                            play             4, 5, 100
                            loop             R0, @square_0
                            move             5, R1
            square_1:
                            play             4, 6, 100
                            loop             R1, @square_1
                            move             500, R2
            square_2:
                            play             4, 5, 100
                            loop             R2, @square_2
                            move             97902, R3
            square_3:
                            play             4, 5, 100
                            loop             R3, @square_3
                            play             7, 8, 23
                            move             97902, R4
            square_4:
                            play             4, 4, 100
                            loop             R4, @square_4
                            play             7, 7, 23
                            move             9721, R5
            square_5:
                            play             9, 10, 127
                            loop             R5, @square_5
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_play_square_smooth_waveforms_with_optimization(
        self, play_square_smooth_waveforms_with_optimization: QProgram
    ):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=play_square_smooth_waveforms_with_optimization)

        assert len(sequences["drive"]._waveforms._waveforms) == 32
        assert sequences["drive"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            play             0, 1, 26
                            play             2, 3, 51
                            play             4, 5, 10
                            move             4, R0
            square_0:
                            play             6, 7, 120
                            loop             R0, @square_0
                            play             8, 5, 10
                            play             9, 10, 26
                            play             11, 3, 51
                            play             12, 13, 4
                            move             1, R1
            square_1:
                            play             14, 15, 96
                            loop             R1, @square_1
                            play             16, 13, 4
                            play             12, 13, 4
                            move             4, R2
            square_2:
                            play             17, 18, 123
                            loop             R2, @square_2
                            play             16, 13, 4
                            play             4, 19, 10
                            move             4, R3
            square_3:
                            play             6, 20, 120
                            loop             R3, @square_3
                            play             8, 21, 10
                            play             4, 5, 10
                            move             490, R4
            square_4:
                            play             22, 23, 102
                            loop             R4, @square_4
                            play             8, 5, 10
                            play             4, 5, 10
                            move             49197, R5
            square_5:
                            play             24, 25, 199
                            loop             R5, @square_5
                            play             8, 5, 10
                            play             4, 4, 10
                            move             49197, R6
            square_6:
                            play             24, 24, 199
                            loop             R6, @square_6
                            play             8, 8, 10
                            play             19, 5, 10
                            move             12345, R7
            square_7:
                            play             26, 27, 100
                            loop             R7, @square_7
                            play             28, 29, 47
                            play             21, 5, 10
                            play             4, 4, 10
                            move             12345, R8
            square_8:
                            play             30, 30, 100
                            loop             R8, @square_8
                            play             31, 31, 47
                            play             8, 8, 10
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_play_square_smooth_raise_error_async_iq(self):
        qp = QProgram()
        qp.play(
            bus="drive",
            waveform=IQPair(
                I=FlatTop(1.0, duration=250, smooth_duration=10, buffer=10),
                Q=FlatTop(0.5, duration=250, smooth_duration=10),
            ),
        )

        compiler = QbloxCompiler()
        with pytest.raises(ValueError, match=re.escape("smooth_duration + buffer of both I and Q must be the same.")):
            compiler.compile(qprogram=qp)

    def test_play_operation_with_variable_in_waveform(self, caplog, play_operation_with_variable_in_waveform: QProgram):
        compiler = QbloxCompiler()
        with caplog.at_level(logging.ERROR):
            _ = compiler.compile(qprogram=play_operation_with_variable_in_waveform)

        assert "Variables in waveforms are not supported in Qblox." in caplog.text

    def test_delay(self, average_with_for_loop_nshots: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_for_loop_nshots, delays={"drive": 20})

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             3, R1
                            move             0, R2
            loop_0:
                            wait             20
                            play             0, 1, 40
                            wait             2960
                            add              R2, 1, R2
                            loop             R1, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             1, R1
                            move             0, R2
                            move             0, R3
                            move             3, R4
                            move             0, R5
            loop_0:
                            move             10, R6
            square_0:
                            play             0, 1, 100
                            loop             R6, @square_0
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            wait             20
                            add              R5, 1, R5
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_negative_delay(self, average_with_for_loop_nshots: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=average_with_for_loop_nshots, delays={"drive": -20})

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             3, R1
                            move             0, R2
            loop_0:
                            play             0, 1, 40
                            wait             2980
                            add              R2, 1, R2
                            loop             R1, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        readout_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            move             1000, R0
            avg_0:
                            move             1, R1
                            move             0, R2
                            move             0, R3
                            move             3, R4
                            move             0, R5
            loop_0:
                            wait             20
                            move             10, R6
            square_0:
                            play             0, 1, 100
                            loop             R6, @square_0
                            acquire_weighed  0, R3, R2, R1, 2000
                            add              R3, 1, R3
                            add              R5, 1, R5
                            loop             R4, @loop_0
                            loop             R0, @avg_0
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    @pytest.mark.parametrize(
        "start,stop,step,expected_result",
        [(0, 10, 1, 11), (10, 0, -1, 11), (1, 2.05, 0.1, 11)],
    )
    def test_calculate_iterations(self, start, stop, step, expected_result):
        result = QbloxCompiler._calculate_iterations(start, stop, step)
        assert result == expected_result

    def test_calculate_iterations_with_zero_step_throws_error(self):
        with pytest.raises(ValueError, match="Step value cannot be zero"):
            QbloxCompiler._calculate_iterations(100, 200, 0)

    def test_update_latched_param_before_wait(self, update_latched_param: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=update_latched_param)

        assert len(sequences) == 1
        assert "drive" in sequences

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)

        assert len(sequences["drive"]._waveforms._waveforms) == 4
        assert len(sequences["drive"]._acquisitions._acquisitions) == 0
        assert len(sequences["drive"]._weights._weights) == 0
        assert sequences["drive"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            set_awg_offs     32767, 0
                            upd_param        4
                            move             1, R0
            square_0:
                            play             0, 1, 100
                            loop             R0, @square_0
                            set_ph           159154943
                            upd_param        4
                            move             1, R1
            square_1:
                            play             0, 1, 100
                            loop             R1, @square_1
                            set_awg_gain     32767, 32767
                            set_awg_gain     32767, 32767
                            upd_param        4
                            wait             96
                            play             2, 3, 5
                            set_freq         4000000
                            set_freq         4000000
                            upd_param        4
                            wait             65532
                            wait             34464
                            play             2, 3, 5
                            set_awg_gain     32767, 32767
                            set_awg_gain     32767, 32767
                            upd_param        4
                            play             2, 3, 5
                            set_awg_offs     32767, 0
                            upd_param        6
                            set_mrk          0
                            upd_param        4
                            stop
        """

        assert is_q1asm_equal(sequences["drive"], drive_str)

    def test_wait_comprised_between_65532_65535(self, wait_comprised_between_65532_65535: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=wait_comprised_between_65532_65535)

        assert "drive" in sequences

        drive_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              

            main:
                            wait             65532          
                            wait             65532          
                            play             0, 1, 20       
                            wait             65532          
                            play             0, 1, 20       
                            wait             65530          
                            wait             4              
                            set_mrk          0              
                            upd_param        4              
                            stop
        """

        assert is_q1asm_equal(sequences["drive"], drive_str)
