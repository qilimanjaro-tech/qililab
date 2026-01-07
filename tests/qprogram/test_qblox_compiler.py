import re
from unittest.mock import MagicMock, patch

import numpy as np
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.waveforms.arbitrary import Arbitrary
import pytest
import qpysequence as QPy

from qililab import Calibration, Domain, FlatTop, Gaussian, IQPair, QProgram, Square
from qililab.qprogram.qblox_compiler import QbloxCompilationOutput, QbloxCompiler
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
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.play(bus="drive", waveform="Xpi")
    qp.play(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="run_qdac_buses")
def fixture_run_qdac_buses() -> QProgram:
    wf = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    qp.play(bus="drive", waveform=wf)

    qp.set_frequency(bus="qdac_flux", frequency=1e6)
    qp.set_phase(bus="qdac_flux", phase=0.1)
    qp.reset_phase(bus="qdac_flux")
    qp.set_gain(bus="qdac_flux", gain=0.1)
    qp.qblox.set_markers(bus="qdac_flux", mask="0000")
    qp.set_trigger(bus="qdac_flux", duration=100)
    qp.wait(bus="qdac_flux", duration=100)
    qp.wait_trigger(bus="qdac_flux", duration=100)
    qp.measure(bus="qdac_flux", waveform=wf, weights=wf)
    qp.play(bus="qdac_flux", waveform=wf)
    qp.qblox.acquire(bus="qdac_flux", weights=wf)

    return qp


@pytest.fixture(name="run_qdac_sync")
def fixture_run_qdac_sync() -> QProgram:
    wf = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    qp.play(bus="drive", waveform=wf)

    qp.sync(buses=["qdac_flux"])

    return qp


@pytest.fixture(name="measurement_blocked_operation")
def fixture_measurement_blocked_operation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    with qp.block():
        qp.play(bus="drive", waveform=drag_wf)
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)

    return qp


@pytest.fixture(name="no_loops_all_operations")
def fixture_no_loops_all_operations() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    qp.set_offset(bus="drive", offset_path0=0.5)
    qp.play(bus="drive", waveform=drag_pair)
    return qp


@pytest.fixture(name="dynamic_wait")
def fixture_dynamic_wait() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration)
    return qp


@pytest.fixture(name="dynamic_wait_multiple_buses_with_disable_autosync")
def fixture_dynamic_wait_multiple_buses_with_disable_autosync() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    qp.qblox.disable_autosync = True
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="readout", duration=duration)
        qp.play(bus="readout", waveform=drag_pair)
    return qp


@pytest.fixture(name="infinite_loop")
def fixture_infinite_loop() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    with qp.infinite_loop():
        qp.play(bus="drive", waveform=drag_pair)
    return qp


@pytest.fixture(name="average_loop")
def fixture_average_loop() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
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
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=drag_pair)
    qp.play(bus="drive", waveform=IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2))
    return qp


@pytest.fixture(name="set_trigger")
def fixture_set_trigger() -> QProgram:
    qp = QProgram()
    qp.set_trigger(bus="drive", duration=100, outputs=1)
    qp.wait(bus="drive", duration=100)
    return qp


@pytest.fixture(name="wait_trigger")
def fixture_wait_trigger() -> QProgram:
    qp = QProgram()
    # With update parameter pending
    qp.set_frequency(bus="drive", frequency=1e6)
    qp.set_frequency(bus="readout", frequency=1e6)
    qp.wait_trigger(bus="drive", duration=4)
    qp.set_frequency(bus="drive", frequency=1e6)
    qp.wait_trigger(bus="drive", duration=1000, port=1)
    qp.set_frequency(bus="drive", frequency=1e6)
    qp.wait_trigger(bus="drive", duration=70000, port=1)

    # No instructions pending
    qp.wait_trigger(bus="drive", duration=1000, port=1)
    qp.wait_trigger(bus="drive", duration=70000, port=1)
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

@pytest.fixture(name="dynamic_sync")
def fixture_dynamic_sync() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.wait(bus="drive", duration=duration-30)
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)
    return qp

@pytest.fixture(name="dynamic_sync_long_wait")
def fixture_dynamic_sync_long_wait() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=0, stop=200_000, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)
        qp.sync()
    return qp

@pytest.fixture(name="dynamic_sync_variable_expression_difference")
def fixture_dynamic_sync_variable_expression_difference() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration-50)
        qp.sync()
        qp.wait(bus="drive", duration=50-duration)
        qp.sync() 
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)
        qp.sync()
    return qp

@pytest.fixture(name="dynamic_sync_variable_expression_sum")
def fixture_dynamic_sync_variable_expression_sum() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=50_000, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration+500)
        qp.sync()
        qp.wait(bus="drive", duration=duration+20_000)
        qp.sync()
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)
        qp.sync()
    return qp

@pytest.fixture(name="dynamic_sync_delay")
def fixture_dynamic_sync_delay() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.play(bus="drive", waveform=drag_pair)
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.measure(bus="readout", waveform=readout_pair, weights=weights_pair)
    return qp

@pytest.fixture(name="measure_reset_program")
def fixture_measure_reset_program() -> QProgram:
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    qp = QProgram()
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp.qblox.measure_reset(bus="readout", waveform=readout_pair, weights=weights_pair, control_bus="drive", reset_pulse=drag_wf)
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

@pytest.fixture(name="error_acquisition_index")
def fixture_error_acquisition_index() -> QProgram:
    qp = QProgram()
    weights_shape = Square(amplitude=1, duration=20)
    bins = qp.variable("bins", Domain.Scalar, int)
    for _ in range (40):
        with qp.for_loop(bins, 0, 100, 1):
            qp.qblox.acquire("readout", IQPair(I=weights_shape, Q=weights_shape))
    return qp

@pytest.fixture(name="single_bin_different_depth_qp")
def fixture_single_bin_different_depth_qp() -> QProgram:
    qp = QProgram()

    weights_shape = IQPair(I=Square(amplitude=1, duration=10), Q=Square(amplitude=0, duration=10))
    square_wf = IQPair(I=Square(amplitude=1, duration=10), Q=Square(amplitude=0, duration=10))

    with qp.average(100):
        qp.measure(bus=f"readout",
            waveform=square_wf,
            weights=weights_shape)
        qp.measure(bus=f"readout",
            waveform=square_wf,
            weights=weights_shape)

    qp.measure(bus=f"readout",
                waveform=square_wf,
                weights=weights_shape)
    qp.measure(bus=f"readout",
                waveform=square_wf,
                weights=weights_shape)
    return qp

@pytest.fixture(name="bus_mappping_acquire")
def fixture_bus_mappping_acquire() -> QProgram:
    qp = QProgram()
    square_wf = IQPair(I=Square(amplitude=1, duration=10), Q=Square(amplitude=0, duration=10))
    with qp.average(10):
        qp.play("drive", square_wf)
        qp.measure(bus=f"readout",
                    waveform=square_wf,
                    weights=square_wf,)
        qp.measure(bus=f"readout",
                waveform=square_wf,
                weights=square_wf,)
        qp.wait("readout",100)
    qp.measure(bus=f"readout",
                waveform=square_wf,
                weights=square_wf,)
    return qp

@pytest.fixture(name="calibration_reset")
def fixture_calibration_reset() -> Calibration:
    drag_reset = IQPair.DRAG(amplitude=0.5, duration=100, num_sigmas=4.5, drag_coefficient=-4.5)
    readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
    weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
    calibration_reset = Calibration()
    calibration_reset.add_waveform(bus="readout_q0_bus", name="readout", waveform=readout_pair)
    calibration_reset.add_weights(bus="readout_q0_bus", name="weights", weights=weights_pair)
    calibration_reset.add_waveform(bus="drive_q0_bus", name="drag_reset", waveform=drag_reset)
    return calibration_reset

@pytest.fixture(name="measure_reset_calibrated_bus_mapping")
def fixture_measure_reset_calibrated_bus_mapping() -> QProgram:
    qp = QProgram()
    qp.qblox.measure_reset(bus="readout_bus", waveform="readout", weights="weights", control_bus="drive_bus", reset_pulse="drag_reset")
    return qp



@pytest.fixture(name="cryoscope_qprogram")
def fixture_cryoscope_qprogram() -> QProgram:
    qp = QProgram()
    HW_AVG = 2000
    REPETITION_DURATION = 200_000
    POST_DRIVE_BUFFER = 30
    POST_FLUX_BUFFER = 30
    AMPLITUDE_VALUES = np.linspace(-.3, .3, num=21)
    DURATION_VALUES = np.arange(80, 160, step=1)
    T_SEP = np.max(DURATION_VALUES) + 100 
    flux_wf = Square(amplitude = 1, duration = 500)
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    flux_amplitude = qp.variable(label='flux_amplitude', domain = Domain.Voltage)
    square_wf = Square(amplitude=1, duration=1385)
    square_iq = IQPair(I=square_wf, Q=square_wf)
    time = qp.variable(label='time', domain = Domain.Time)
    qp.set_gain(bus=f"drive", gain=1)
    qp.set_gain(bus=f"readout", gain=1)
    with qp.average(HW_AVG):
        with qp.for_loop(variable = flux_amplitude, start=AMPLITUDE_VALUES[0], stop=AMPLITUDE_VALUES[-1], step=AMPLITUDE_VALUES[1]-AMPLITUDE_VALUES[0]):
            with qp.for_loop(variable = time, start=DURATION_VALUES[0], stop=DURATION_VALUES[-1], step=DURATION_VALUES[1]-DURATION_VALUES[0]):
            
                qp.set_gain(bus=f'flux', gain=flux_amplitude)
                qp.sync()
                qp.play(bus=f"drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus=f"flux",duration=POST_DRIVE_BUFFER)
                qp.sync()

                # play a flux pulse of varying duration
                qp.qblox.play(bus=f'flux', waveform=flux_wf,wait_time=4)
                qp.wait(bus=f"drive",duration=time)
                qp.sync()
                qp.qblox.play(bus=f'flux', waveform=Square(0,500),wait_time=4)

                qp.wait(bus=f"drive",duration=POST_FLUX_BUFFER+ T_SEP-time)
                qp.play(bus=f"drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus=f"readout",duration=POST_DRIVE_BUFFER)
                qp.measure(bus=f"readout", waveform=square_iq , weights=square_iq )
                qp.sync()
                qp.wait(bus=f"drive",duration=REPETITION_DURATION)

                qp.sync()
                qp.play(bus=f"drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus=f"flux",duration=POST_DRIVE_BUFFER)
                qp.sync()

                # play a flux pulse of varying duration
                qp.qblox.play(bus=f'flux', waveform=flux_wf,wait_time=4)
                qp.wait(bus=f"drive",duration=time)
                qp.sync()
                qp.qblox.play(bus=f'flux', waveform=Square(0,500),wait_time=4)
                
                qp.wait(bus=f"drive",duration=POST_FLUX_BUFFER+ T_SEP-time)
                qp.play(bus=f"drive", waveform=drag_pair)
                qp.sync()
                qp.wait(bus=f"readout",duration=POST_DRIVE_BUFFER)
                qp.measure(bus=f"readout", waveform=square_iq, weights=square_iq )
                qp.sync()
                qp.wait(bus=f"drive",duration=REPETITION_DURATION)
                qp.sync()
    return qp

@pytest.fixture(name="dynamic_wait_three_buses_dynamic_static")
def fixture_dynamic_wait_three_buses_dynamic_static() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync(["drive","readout"])
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.play(bus="flux", waveform=drag_pair)
        qp.sync()
    return qp

@pytest.fixture(name="dynamic_wait_three_buses_static_static")
def fixture_dynamic_wait_three_buses_static_static() -> QProgram:
    drag_pair = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    qp = QProgram()
    duration = qp.variable(label="time", domain=Domain.Time)
    with qp.for_loop(variable=duration, start=100, stop=200, step=10):
        qp.wait(bus="drive", duration=duration)
        qp.sync()
        qp.play(bus="drive", waveform=drag_pair)
        qp.sync(["drive","readout"])
        qp.wait(bus="drive", duration=10)
        qp.sync()
        qp.play(bus="flux", waveform=drag_pair)
        qp.sync()
    return qp


@pytest.fixture(name="calibration_crosstalk")
def fixture_calibration_crosstalk() -> Calibration:
    inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
    crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

    calibration_crosstalk = Calibration()
    calibration_crosstalk.crosstalk_matrix = crosstalk

    return calibration_crosstalk


@pytest.fixture(name="crosstalk_qprogram")
def fixture_crosstalk_qprogram() -> QProgram:
    square_wf = Square(amplitude=0.1, duration=50)
    square_iq = IQPair(I=square_wf, Q=square_wf)
    qp = QProgram()
    offset = qp.variable(label="offset", domain=Domain.Voltage)
    with qp.for_loop(variable=offset, start=0, stop=0.1, step=0.01):
        qp.set_offset(bus="flux1", offset_path0=offset)
        qp.wait(bus="drive", duration=10)
        qp.wait(bus="flux1", duration=10)
        qp.wait(bus="flux2", duration=10)
        qp.set_gain(bus="flux2", gain=0.05)
        qp.play(bus="flux1", waveform=square_wf)
        qp.play(bus="drive", waveform=square_iq)
        qp.sync(["drive","readout"])
        qp.measure(bus=f"readout", waveform=square_iq, weights=square_iq)
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

    def test_qdac_bus_ignored(self, run_qdac_buses: QProgram):

        compiler = QbloxCompiler()
        output = compiler.compile(
            qprogram=run_qdac_buses, bus_mapping={"drive": "drive_q0"}, qblox_buses=["drive_q0"]
        )

        assert len(output.sequences) == 1
        assert "drive_q0" in output.sequences
        assert isinstance(output.sequences["drive_q0"], QPy.Sequence)

    def test_qdac_sync_raises_error(self, run_qdac_sync: QProgram):

        compiler = QbloxCompiler()

        with pytest.raises(ValueError, match="Non QBLOX buses not allowed inside sync function"):
            compiler.compile(qprogram=run_qdac_sync, bus_mapping={"drive": "drive_q0"}, qblox_buses=["drive_q0"])

    def test_set_trigger(self, set_trigger: QProgram):

        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=set_trigger)
        assert len(sequences) == 1
        assert "drive" in sequences

        drive_str = """
                setup:
                                wait_sync        4
                                set_mrk          0
                                upd_param        4

                main:
                                set_mrk          1
                                upd_param        4
                                wait             96
                                set_mrk          0
                                upd_param        4
                                wait             96
                                set_mrk          0
                                upd_param        4
                                stop
            """
        assert is_q1asm_equal(sequences["drive"]._program, drive_str)

        # RF example with the right markers
        sequences, _ = compiler.compile(qprogram=set_trigger, markers={"drive": "1100"})
        assert len(sequences) == 1
        assert "drive" in sequences

        drive_str = """
                setup:
                                wait_sync        4
                                set_mrk          12
                                upd_param        4

                main:
                                set_mrk          13
                                upd_param        4
                                wait             96
                                set_mrk          12
                                upd_param        4
                                wait             96
                                set_mrk          0
                                upd_param        4
                                stop
            """
        assert is_q1asm_equal(sequences["drive"]._program, drive_str)

    def test_set_trigger_raises_no_output_error(self):
        qp = QProgram()
        qp.set_trigger(bus="drive", duration=10)

        compiler = QbloxCompiler()

        with pytest.raises(ValueError, match="Missing qblox trigger outputs at qp.set_trigger."):
            compiler.compile(qprogram=qp)

    def test_set_trigger_raises_output_out_of_range_error(self):
        qp = QProgram()
        qp.set_trigger(bus="drive", duration=10, outputs=5)

        compiler = QbloxCompiler()

        with pytest.raises(ValueError, match="Low frequency modules only have 4 trigger outputs, out of range"):
            compiler.compile(qprogram=qp)
            pass

        compiler._markers = {"drive": "1100"}
        with pytest.raises(ValueError, match="RF modules only have 2 trigger outputs, either 1 or 2"):
            compiler.compile(qprogram=qp, markers={"drive": "1100"})
            pass

    def test_wait_trigger(self, wait_trigger: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=wait_trigger, ext_trigger=True)

        assert sequences["drive"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4
                            set_mrk          0
                            upd_param        4

            main:
                            set_freq         4000000
                            set_freq         4000000
                            upd_param        4
                            wait_trigger     15, 4
                            wait_sync        4
                            set_freq         4000000
                            set_freq         4000000
                            upd_param        4
                            wait_trigger     1, 996
                            wait_sync        4
                            set_freq         4000000
                            set_freq         4000000
                            upd_param        4
                            wait_trigger     1, 4
                            wait             65532
                            wait             65532
                            wait_sync        4
                            wait_trigger     1, 1000
                            wait_sync        4
                            wait_trigger     1, 4
                            wait             65532
                            wait             65532
                            wait_sync        4
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
                            set_freq         4000000
                            set_freq         4000000
                            wait_sync        4
                            wait_sync        4
                            wait_sync        4
                            wait_sync        4
                            wait_sync        4
                            set_mrk          0
                            upd_param        4
                            stop
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_wait_trigger_no_ext_trigger_raises_error(self, wait_trigger: QProgram):

        compiler = QbloxCompiler()
        with pytest.raises(
            AttributeError, match="External trigger has not been set as True inside runcard's instrument controllers."
        ):
            compiler.compile(qprogram=wait_trigger, ext_trigger=False)

    def test_wait_trigger_var_durationraises_error(self):

        qp = QProgram()
        duration = qp.variable(label="duration", domain=Domain.Time)
        with qp.for_loop(variable=duration, start=4, stop=100, step=4):
            qp.wait_trigger(bus="drive", duration=duration, port=1)

        compiler = QbloxCompiler()
        with pytest.raises(ValueError, match="Wait trigger duration cannot be a Variable, it must be an int."):
            compiler.compile(qprogram=qp, ext_trigger=True)

    def test_block_handlers(self, measurement_blocked_operation: QProgram, calibration: Calibration):
        drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
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

    def test_32_acquisiton_raise_error(self, error_acquisition_index: QProgram):
        "Check that having acquisitions in 31+ nested level raises a Value error"
        compiler = QbloxCompiler()
        with pytest.raises(ValueError, match="Acquisition index 32 exceeds maximum of 31."):
            _ = compiler.compile(error_acquisition_index)


    def test_acquire_single_bin_different_nested_level(self, single_bin_different_depth_qp: QProgram):
        "Check that having single binned acquisitions at different nested level resets the bin index counter to 0"
        compiler = QbloxCompiler()
        sequences,_ = compiler.compile(single_bin_different_depth_qp)
        readout_str = """ 
        setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

        main:
                move             100, R0        
        avg_0:
                play             0, 1, 4        
                acquire_weighed  0, 0, 0, 1, 10 
                play             0, 1, 4        
                acquire_weighed  0, 1, 0, 1, 10 
                loop             R0, @avg_0     
                play             0, 1, 4        
                acquire_weighed  1, 0, 0, 1, 10 
                play             0, 1, 4        
                acquire_weighed  1, 1, 0, 1, 10 
                set_mrk          0              
                upd_param        4              
                stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)

    
    def test_bus_mapping_and_acquire(self, bus_mappping_acquire):
        """Test bus mapping and acquisition together"""
        compiler = QbloxCompiler()
        sequences = compiler.compile(bus_mappping_acquire)
        acquisition_dict = sequences.sequences["readout"]._acquisitions.to_dict()
        readout_str = """setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

        main:
                move             10, R0         
        avg_0:
                play             0, 1, 4        
                acquire_weighed  0, 0, 0, 1, 10 
                play             0, 1, 4        
                acquire_weighed  0, 1, 0, 1, 10 
                wait             100            
                loop             R0, @avg_0     
                play             0, 1, 4        
                acquire_weighed  1, 0, 0, 1, 10 
                set_mrk          0              
                upd_param        4              
                stop"""

        assert is_q1asm_equal(sequences.sequences["readout"], readout_str)
        assert acquisition_dict == {'Acquisition 0': {'num_bins': 2, 'index': 0}, 'Acquisition 1': {'num_bins': 1, 'index': 1}}

    def test_measure_reset(self, measure_reset_program: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=measure_reset_program)

        assert len(sequences) == 2
        assert "drive" in sequences
        assert "readout" in sequences

        drive_str = """
            setup:
                            set_latch_en     1, 4           
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              

            main:
                            latch_rst        4              
                            wait             2400          
                            set_cond         1, 1, 0, 100   
                            play             0, 1, 100      
                            set_cond         0, 0, 0, 4     
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
                play             0, 1, 4        
                acquire_weighed  0, 0, 0, 1, 2000
                set_mrk          0              
                upd_param        4              
                stop                            
        """
        print(sequences["drive"]._program)

        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)
        
    def test_dynamic_sync(self, dynamic_sync_delay: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_sync_delay)

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
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

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
                            move             0, R2          
                            add              R1, 40, R3     
                            nop                             
                            sub              R2, R3, R4     
                            nop                             
                            jlt              R4, 2147483648, @dynamic_sync_0
                            jge              R4, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:


                            wait             2004           
                            add              R1, 10, R1     
                            loop             R0, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:


                            jlt              R4, 1, @after_dynamic_sync_0
                            jlt              R4, 4, @one_two_three_0
                            jge              R4, 65532, @long_wait_sync_0
                            wait             R4             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:


                            add              R4, 4, R4      
                            nop                             
                            wait             R4             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:


                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:


                            wait             65532          
                            sub              R4, 65532, R4  
                            nop                             
                            jge              R4, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
        """
        
        readout_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              

            main:
                            move             1, R0          
                            move             0, R1          
                            move             0, R2          
                            move             11, R3         
                            move             100, R4        
            loop_0:
                            move             40, R5         
                            add              R4, 40, R6     
                            nop                             
                            sub              R5, R6, R7     
                            nop                             
                            jlt              R7, 2147483648, @other_max_duration_0
                            move             R6, R7         
            after_other_max_duration_0:


                            move             0, R8          
                            nop                             
                            sub              R7, R8, R9     
                            nop                             
                            jlt              R9, 2147483648, @dynamic_sync_0
                            jge              R9, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:


                            play             0, 1, 4        
                            acquire_weighed  0, R2, R1, R0, 2000
                            add              R2, 1, R2      
                            add              R4, 10, R4     
                            loop             R3, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:


                            jlt              R9, 1, @after_dynamic_sync_0
                            jlt              R9, 4, @one_two_three_0
                            jge              R9, 65532, @long_wait_sync_0
                            wait             R9             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:


                            add              R9, 4, R9      
                            nop                             
                            wait             R9             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:


                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:


                            wait             65532          
                            sub              R9, 65532, R9  
                            nop                             
                            jge              R9, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            other_max_duration_0:


                            move             R5, R7         
                            jmp              @after_other_max_duration_0
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_dynamic_sync_long_wait(self, dynamic_sync_long_wait: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_sync_long_wait)

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
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              
            main:
                            move             20001, R0      
                            move             4, R1          
            loop_0:
                            play             0, 1, 40       
                            nop                             
                            move             R1, R2         
                            nop                             
                            jge              R1, 65532, @long_wait_0
                            wait             R1             
            continue_after_long_wait_0:
                            move             0, R3          
                            add              R1, 40, R4     
                            nop                             
                            sub              R3, R4, R5     
                            nop                             
                            jlt              R5, 2147483648, @dynamic_sync_0
                            jge              R5, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            wait             1004           
                            add              R1, 9, R1      
                            loop             R0, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            long_wait_0:
                            wait             65532          
                            sub              R2, 65532, R2  
                            nop                             
                            jge              R2, 65532, @long_wait_0
                            wait             R2             
                            jmp              @continue_after_long_wait_0
            dynamic_sync_0:
                            jlt              R5, 1, @after_dynamic_sync_0
                            jlt              R5, 4, @one_two_three_0
                            jge              R5, 65532, @long_wait_sync_0
                            wait             R5             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R5, 4, R5      
                            nop                             
                            wait             R5             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R5, 65532, R5  
                            nop                             
                            jge              R5, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
                """

        readout_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              
            main:
                            move             1, R0          
                            move             0, R1          
                            move             0, R2          
                            move             20001, R3      
                            move             4, R4          
            loop_0:
                            move             40, R5         
                            add              R4, 40, R6     
                            nop                             
                            sub              R5, R6, R7     
                            nop                             
                            jlt              R7, 2147483648, @other_max_duration_0
                            move             R6, R7         
            after_other_max_duration_0:
                            move             0, R8          
                            nop                             
                            sub              R7, R8, R9     
                            nop                             
                            jlt              R9, 2147483648, @dynamic_sync_0
                            jge              R9, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            play             0, 1, 4        
                            acquire_weighed  0, R2, R1, R0, 1000
                            add              R2, 1, R2      
                            add              R4, 9, R4      
                            loop             R3, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:
                            jlt              R9, 1, @after_dynamic_sync_0
                            jlt              R9, 4, @one_two_three_0
                            jge              R9, 65532, @long_wait_sync_0
                            wait             R9             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R9, 4, R9      
                            nop                             
                            wait             R9             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R9, 65532, R9  
                            nop                             
                            jge              R9, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            other_max_duration_0:
                            move             R5, R7         
                            jmp              @after_other_max_duration_0
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)
        assert is_q1asm_equal(sequences["drive"], drive_str)


    def test_dynamic_sync_variable_expression_difference(self, dynamic_sync_variable_expression_difference: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_sync_variable_expression_difference)

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
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

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
                            nop                             
                            sub              R1, 50, R2     
                            nop                             
                            wait             R2             
                            move             0, R3          
                            nop                             
                            add              R2, 40, R4     
                            nop                             
                            sub              R3, R4, R5     
                            nop                             
                            jlt              R5, 2147483648, @dynamic_sync_0
                            jge              R5, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            move             50, R6         
                            nop                             
                            sub              R6, R1, R7     
                            nop                             
                            wait             R7             
                            move             0, R3          
                            nop                             
                            add              R7, 0, R4      
                            nop                             
                            sub              R3, R4, R5     
                            nop                             
                            jlt              R5, 2147483648, @dynamic_sync_1
                            jge              R5, 4294967293, @negative_one_two_three_1
            after_dynamic_sync_1:
                            wait             2004           
                            add              R1, 10, R1     
                            loop             R0, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:
                            jlt              R5, 1, @after_dynamic_sync_0
                            jlt              R5, 4, @one_two_three_0
                            jge              R5, 65532, @long_wait_sync_0
                            wait             R5             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R5, 4, R5      
                            nop                             
                            wait             R5             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R5, 65532, R5  
                            nop                             
                            jge              R5, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            dynamic_sync_1:
                            jlt              R5, 1, @after_dynamic_sync_1
                            jlt              R5, 4, @one_two_three_1
                            jge              R5, 65532, @long_wait_sync_1
                            wait             R5             
                            jmp              @after_dynamic_sync_1
            one_two_three_1:
                            add              R5, 4, R5      
                            nop                             
                            wait             R5             
                            jmp              @after_dynamic_sync_1
            negative_one_two_three_1:
                            wait             4              
                            jmp              @after_dynamic_sync_1
            long_wait_sync_1:
                            wait             65532          
                            sub              R5, 65532, R5  
                            nop                             
                            jge              R5, 65532, @long_wait_sync_1
                            jmp              @dynamic_sync_1
                """

        readout_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              
            main:
                            move             1, R0          
                            move             0, R1          
                            move             0, R2          
                            move             11, R3         
                            move             100, R4        
            loop_0:
                            nop                             
                            sub              R4, 50, R5     
                            nop                             
                            move             40, R6         
                            add              R5, 40, R7     
                            nop                             
                            sub              R6, R7, R8     
                            nop                             
                            jlt              R8, 2147483648, @other_max_duration_0
                            move             R7, R8         
            after_other_max_duration_0:
                            move             0, R9          
                            nop                             
                            sub              R8, R9, R10    
                            nop                             
                            jlt              R10, 2147483648, @dynamic_sync_0
                            jge              R10, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            move             50, R11        
                            nop                             
                            sub              R11, R4, R5    
                            nop                             
                            move             0, R6          
                            add              R5, 0, R7      
                            nop                             
                            sub              R6, R7, R8     
                            nop                             
                            jlt              R8, 2147483648, @other_max_duration_1
                            move             R7, R8         
            after_other_max_duration_1:
                            move             0, R12         
                            nop                             
                            sub              R8, R12, R10   
                            nop                             
                            jlt              R10, 2147483648, @dynamic_sync_1
                            jge              R10, 4294967293, @negative_one_two_three_1
            after_dynamic_sync_1:
                            play             0, 1, 4        
                            acquire_weighed  0, R2, R1, R0, 2000
                            add              R2, 1, R2      
                            add              R4, 10, R4     
                            loop             R3, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:
                            jlt              R10, 1, @after_dynamic_sync_0
                            jlt              R10, 4, @one_two_three_0
                            jge              R10, 65532, @long_wait_sync_0
                            wait             R10            
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R10, 4, R10    
                            nop                             
                            wait             R10            
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R10, 65532, R10
                            nop                             
                            jge              R10, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            other_max_duration_0:
                            move             R6, R8         
                            jmp              @after_other_max_duration_0
            dynamic_sync_1:
                            jlt              R10, 1, @after_dynamic_sync_1
                            jlt              R10, 4, @one_two_three_1
                            jge              R10, 65532, @long_wait_sync_1
                            wait             R10            
                            jmp              @after_dynamic_sync_1
            one_two_three_1:
                            add              R10, 4, R10    
                            nop                             
                            wait             R10            
                            jmp              @after_dynamic_sync_1
            negative_one_two_three_1:
                            wait             4              
                            jmp              @after_dynamic_sync_1
            long_wait_sync_1:
                            wait             65532          
                            sub              R10, 65532, R10
                            nop                             
                            jge              R10, 65532, @long_wait_sync_1
                            jmp              @dynamic_sync_1
            other_max_duration_1:
                            move             R6, R8         
                            jmp              @after_other_max_duration_1
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)
        assert is_q1asm_equal(sequences["drive"], drive_str)


    def test_dynamic_sync_variable_expression_sum(self, dynamic_sync_variable_expression_sum: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_sync_variable_expression_sum)

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
        assert len(sequences["readout"]._weights._weights) == 2
        assert sequences["readout"]._program._compiled

        drive_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              
            main:
                            move             4991, R0       
                            move             100, R1        
            loop_0:
                            play             0, 1, 40       
                            nop                             
                            add              R1, 500, R2    
                            nop                             
                            wait             R2             
                            move             0, R3          
                            nop                             
                            add              R2, 40, R4     
                            nop                             
                            sub              R3, R4, R5     
                            nop                             
                            jlt              R5, 2147483648, @dynamic_sync_0
                            jge              R5, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            nop                             
                            add              R1, 20000, R6  
                            nop                             
                            nop                             
                            move             R6, R7         
                            nop                             
                            jge              R6, 65532, @long_wait_0
                            wait             R6             
            continue_after_long_wait_0:
                            move             0, R3          
                            nop                             
                            add              R6, 0, R4      
                            nop                             
                            sub              R3, R4, R5     
                            nop                             
                            jlt              R5, 2147483648, @dynamic_sync_1
                            jge              R5, 4294967293, @negative_one_two_three_1
            after_dynamic_sync_1:
                            wait             2004           
                            add              R1, 10, R1     
                            loop             R0, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            long_wait_0:
                            wait             65532          
                            sub              R7, 65532, R7  
                            nop                             
                            jge              R7, 65532, @long_wait_0
                            wait             R7             
                            jmp              @continue_after_long_wait_0
            dynamic_sync_0:
                            jlt              R5, 1, @after_dynamic_sync_0
                            jlt              R5, 4, @one_two_three_0
                            jge              R5, 65532, @long_wait_sync_0
                            wait             R5             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R5, 4, R5      
                            nop                             
                            wait             R5             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R5, 65532, R5  
                            nop                             
                            jge              R5, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            dynamic_sync_1:
                            jlt              R5, 1, @after_dynamic_sync_1
                            jlt              R5, 4, @one_two_three_1
                            jge              R5, 65532, @long_wait_sync_1
                            wait             R5             
                            jmp              @after_dynamic_sync_1
            one_two_three_1:
                            add              R5, 4, R5      
                            nop                             
                            wait             R5             
                            jmp              @after_dynamic_sync_1
            negative_one_two_three_1:
                            wait             4              
                            jmp              @after_dynamic_sync_1
            long_wait_sync_1:
                            wait             65532          
                            sub              R5, 65532, R5  
                            nop                             
                            jge              R5, 65532, @long_wait_sync_1
                            jmp              @dynamic_sync_1
                """

        readout_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              
            main:
                            move             1, R0          
                            move             0, R1          
                            move             0, R2          
                            move             4991, R3       
                            move             100, R4        
            loop_0:
                            nop                             
                            add              R4, 500, R5    
                            nop                             
                            move             40, R6         
                            add              R5, 40, R7     
                            nop                             
                            sub              R6, R7, R8     
                            nop                             
                            jlt              R8, 2147483648, @other_max_duration_0
                            move             R7, R8         
            after_other_max_duration_0:
                            move             0, R9          
                            nop                             
                            sub              R8, R9, R10    
                            nop                             
                            jlt              R10, 2147483648, @dynamic_sync_0
                            jge              R10, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            nop                             
                            add              R4, 20000, R5  
                            nop                             
                            move             0, R6          
                            add              R5, 0, R7      
                            nop                             
                            sub              R6, R7, R8     
                            nop                             
                            jlt              R8, 2147483648, @other_max_duration_1
                            move             R7, R8         
            after_other_max_duration_1:
                            move             0, R11         
                            nop                             
                            sub              R8, R11, R10   
                            nop                             
                            jlt              R10, 2147483648, @dynamic_sync_1
                            jge              R10, 4294967293, @negative_one_two_three_1
            after_dynamic_sync_1:
                            play             0, 1, 4        
                            acquire_weighed  0, R2, R1, R0, 2000
                            add              R2, 1, R2      
                            add              R4, 10, R4     
                            loop             R3, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:
                            jlt              R10, 1, @after_dynamic_sync_0
                            jlt              R10, 4, @one_two_three_0
                            jge              R10, 65532, @long_wait_sync_0
                            wait             R10            
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R10, 4, R10    
                            nop                             
                            wait             R10            
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R10, 65532, R10
                            nop                             
                            jge              R10, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            other_max_duration_0:
                            move             R6, R8         
                            jmp              @after_other_max_duration_0
            dynamic_sync_1:
                            jlt              R10, 1, @after_dynamic_sync_1
                            jlt              R10, 4, @one_two_three_1
                            jge              R10, 65532, @long_wait_sync_1
                            wait             R10            
                            jmp              @after_dynamic_sync_1
            one_two_three_1:
                            add              R10, 4, R10    
                            nop                             
                            wait             R10            
                            jmp              @after_dynamic_sync_1
            negative_one_two_three_1:
                            wait             4              
                            jmp              @after_dynamic_sync_1
            long_wait_sync_1:
                            wait             65532          
                            sub              R10, 65532, R10
                            nop                             
                            jge              R10, 65532, @long_wait_sync_1
                            jmp              @dynamic_sync_1
            other_max_duration_1:
                            move             R6, R8         
                            jmp              @after_other_max_duration_1
                """

        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)

    def test_delay_with_dynamic_time(self, dynamic_sync: QProgram):
        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=dynamic_sync, delays={"drive": 20})

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
                            wait             20             
                            play             0, 1, 40       
                            wait             R1             
                            move             0, R2          
                            add              R1, 40, R3     
                            nop                             
                            sub              R2, R3, R4     
                            nop                             
                            jlt              R4, 2147483648, @dynamic_sync_0
                            jge              R4, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            nop                             
                            sub              R1, 30, R5     
                            nop                             
                            wait             R5             
                            move             2024, R2       
                            nop                             
                            add              R5, 0, R3      
                            nop                             
                            sub              R2, R3, R4     
                            nop                             
                            jlt              R4, 2147483648, @dynamic_sync_1
                            jge              R4, 4294967293, @negative_one_two_three_1
            after_dynamic_sync_1:
                            add              R1, 10, R1     
                            loop             R0, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:
                            jlt              R4, 1, @after_dynamic_sync_0
                            jlt              R4, 4, @one_two_three_0
                            jge              R4, 65532, @long_wait_sync_0
                            wait             R4             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R4, 4, R4      
                            nop                             
                            wait             R4             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R4, 65532, R4  
                            nop                             
                            jge              R4, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            dynamic_sync_1:
                            jlt              R4, 1, @after_dynamic_sync_1
                            jlt              R4, 4, @one_two_three_1
                            jge              R4, 65532, @long_wait_sync_1
                            wait             R4             
                            jmp              @after_dynamic_sync_1
            one_two_three_1:
                            add              R4, 4, R4      
                            nop                             
                            wait             R4             
                            jmp              @after_dynamic_sync_1
            negative_one_two_three_1:
                            wait             4              
                            jmp              @after_dynamic_sync_1
            long_wait_sync_1:
                            wait             65532          
                            sub              R4, 65532, R4  
                            nop                             
                            jge              R4, 65532, @long_wait_sync_1
                            jmp              @dynamic_sync_1
        """

        readout_str = """
            setup:
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              
            main:
                            move             1, R0          
                            move             0, R1          
                            move             0, R2          
                            move             11, R3         
                            move             100, R4        
            loop_0:
                            move             40, R5         
                            add              R4, 40, R6     
                            nop                             
                            sub              R5, R6, R7     
                            nop                             
                            jlt              R7, 2147483648, @other_max_duration_0
                            move             R6, R7         
            after_other_max_duration_0:
                            move             0, R8          
                            nop                             
                            sub              R7, R8, R9     
                            nop                             
                            jlt              R9, 2147483648, @dynamic_sync_0
                            jge              R9, 4294967293, @negative_one_two_three_0
            after_dynamic_sync_0:
                            nop                             
                            sub              R4, 30, R10    
                            nop                             
                            play             0, 1, 4        
                            acquire_weighed  0, R2, R1, R0, 2000
                            add              R2, 1, R2      
                            wait             20             
                            move             0, R5          
                            add              R10, 0, R6     
                            nop                             
                            sub              R5, R6, R7     
                            nop                             
                            jlt              R7, 2147483648, @other_max_duration_1
                            move             R6, R7         
            after_other_max_duration_1:
                            move             2024, R11      
                            nop                             
                            sub              R7, R11, R9    
                            nop                             
                            jlt              R9, 2147483648, @dynamic_sync_1
                            jge              R9, 4294967293, @negative_one_two_three_1
            after_dynamic_sync_1:
                            add              R4, 10, R4     
                            loop             R3, @loop_0    
                            set_mrk          0              
                            upd_param        4              
                            stop                            
            dynamic_sync_0:
                            jlt              R9, 1, @after_dynamic_sync_0
                            jlt              R9, 4, @one_two_three_0
                            jge              R9, 65532, @long_wait_sync_0
                            wait             R9             
                            jmp              @after_dynamic_sync_0
            one_two_three_0:
                            add              R9, 4, R9      
                            nop                             
                            wait             R9             
                            jmp              @after_dynamic_sync_0
            negative_one_two_three_0:
                            wait             4              
                            jmp              @after_dynamic_sync_0
            long_wait_sync_0:
                            wait             65532          
                            sub              R9, 65532, R9  
                            nop                             
                            jge              R9, 65532, @long_wait_sync_0
                            jmp              @dynamic_sync_0
            other_max_duration_0:
                            move             R5, R7         
                            jmp              @after_other_max_duration_0
            dynamic_sync_1:
                            jlt              R9, 1, @after_dynamic_sync_1
                            jlt              R9, 4, @one_two_three_1
                            jge              R9, 65532, @long_wait_sync_1
                            wait             R9             
                            jmp              @after_dynamic_sync_1
            one_two_three_1:
                            add              R9, 4, R9      
                            nop                             
                            wait             R9             
                            jmp              @after_dynamic_sync_1
            negative_one_two_three_1:
                            wait             4              
                            jmp              @after_dynamic_sync_1
            long_wait_sync_1:
                            wait             65532          
                            sub              R9, 65532, R9  
                            nop                             
                            jge              R9, 65532, @long_wait_sync_1
                            jmp              @dynamic_sync_1
            other_max_duration_1:
                            move             R5, R7         
                            jmp              @after_other_max_duration_1
        """
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)


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

    def test_32_acquisiton_raise_error(self, error_acquisition_index: QProgram):
        "Check that having acquisitions in 31+ nested level raises a Value error"
        compiler = QbloxCompiler()
        with pytest.raises(ValueError, match="Acquisition index 32 exceeds maximum of 31."):
            _ = compiler.compile(error_acquisition_index)


    def test_acquire_single_bin_different_nested_level(self, single_bin_different_depth_qp: QProgram):
        "Check that having single binned acquisitions at different nested level resets the bin index counter to 0"
        compiler = QbloxCompiler()
        sequences,_ = compiler.compile(single_bin_different_depth_qp)
        readout_str = """ 
        setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              
        main:
                move             100, R0        
        avg_0:
                play             0, 1, 4        
                acquire_weighed  0, 0, 0, 1, 10 
                play             0, 1, 4        
                acquire_weighed  0, 1, 0, 1, 10 
                loop             R0, @avg_0     
                play             0, 1, 4        
                acquire_weighed  1, 0, 0, 1, 10 
                play             0, 1, 4        
                acquire_weighed  1, 1, 0, 1, 10 
                set_mrk          0              
                upd_param        4              
                stop
        """
        assert is_q1asm_equal(sequences["readout"], readout_str)


    def test_bus_mapping_and_acquire(self, bus_mappping_acquire):
        """Test bus mapping and ascquisition together"""
        compiler = QbloxCompiler()
        sequences = compiler.compile(bus_mappping_acquire)
        acquisition_dict = sequences.sequences["readout"]._acquisitions.to_dict()
        readout_str = """setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              
        main:
                move             10, R0         
        avg_0:
                play             0, 1, 4        
                acquire_weighed  0, 0, 0, 1, 10 
                play             0, 1, 4        
                acquire_weighed  0, 1, 0, 1, 10 
                wait             100            
                loop             R0, @avg_0     
                play             0, 1, 4        
                acquire_weighed  1, 0, 0, 1, 10 
                set_mrk          0              
                upd_param        4              
                stop"""

        assert is_q1asm_equal(sequences.sequences["readout"], readout_str)
        assert acquisition_dict == {'Acquisition 0': {'num_bins': 2, 'index': 0}, 'Acquisition 1': {'num_bins': 1, 'index': 1}}


    def test_cryoscope(self, cryoscope_qprogram):
        compiler = QbloxCompiler()
        sequences = compiler.compile(cryoscope_qprogram)
        drive_str = """setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              
                main:
                                set_awg_gain     32767, 32767   
                                set_awg_gain     32767, 32767   
                                move             2000, R0       
                avg_0:
                                move             21, R1         
                                move             9830, R2       
                                nop                             
                                not              R2, R2         
                                nop                             
                                add              R2, 1, R2      
                loop_0:
                                move             80, R3         
                                move             80, R4         
                loop_1:
                                play             0, 1, 40       
                                wait             30             
                                wait             R4             
                                move             4, R5          
                                add              R4, 0, R6      
                                nop                             
                                sub              R5, R6, R7     
                                nop                             
                                jlt              R7, 2147483648, @dynamic_sync_0
                                jge              R7, 4294967293, @negative_one_two_three_0
                after_dynamic_sync_0:
                                wait             289            
                                play             0, 1, 40       
                                wait             1419           
                                wait             65532          
                                wait             65532          
                                wait             65532          
                                wait             3404           
                                play             0, 1, 40       
                                wait             30             
                                wait             R4             
                                move             4, R5          
                                add              R4, 0, R6      
                                nop                             
                                sub              R5, R6, R7     
                                nop                             
                                jlt              R7, 2147483648, @dynamic_sync_1
                                jge              R7, 4294967293, @negative_one_two_three_1
                after_dynamic_sync_1:
                                wait             289            
                                play             0, 1, 40       
                                wait             1419           
                                wait             65532          
                                wait             65532          
                                wait             65532          
                                wait             3404           
                                add              R4, 1, R4      
                                loop             R3, @loop_1    
                                add              R2, 983, R2    
                                loop             R1, @loop_0    
                                loop             R0, @avg_0     
                                set_mrk          0              
                                upd_param        4              
                                stop                            
                dynamic_sync_0:
                                jlt              R7, 1, @after_dynamic_sync_0
                                jlt              R7, 4, @one_two_three_0
                                jge              R7, 65532, @long_wait_sync_0
                                wait             R7             
                                jmp              @after_dynamic_sync_0
                one_two_three_0:
                                add              R7, 4, R7      
                                nop                             
                                wait             R7             
                                jmp              @after_dynamic_sync_0
                negative_one_two_three_0:
                                wait             4              
                                jmp              @after_dynamic_sync_0
                long_wait_sync_0:
                                wait             65532          
                                sub              R7, 65532, R7  
                                nop                             
                                jge              R7, 65532, @long_wait_sync_0
                                jmp              @dynamic_sync_0
                dynamic_sync_1:
                                jlt              R7, 1, @after_dynamic_sync_1
                                jlt              R7, 4, @one_two_three_1
                                jge              R7, 65532, @long_wait_sync_1
                                wait             R7             
                                jmp              @after_dynamic_sync_1
                one_two_three_1:
                                add              R7, 4, R7      
                                nop                             
                                wait             R7             
                                jmp              @after_dynamic_sync_1
                negative_one_two_three_1:
                                wait             4              
                                jmp              @after_dynamic_sync_1
                long_wait_sync_1:
                                wait             65532          
                                sub              R7, 65532, R7  
                                nop                             
                                jge              R7, 65532, @long_wait_sync_1
                                jmp              @dynamic_sync_1"""

        readout_str="""setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              
                main:
                                set_awg_gain     32767, 32767   
                                set_awg_gain     32767, 32767   
                                move             2000, R0       
                avg_0:
                                move             0, R1          
                                move             0, R2          
                                move             21, R3         
                                move             9830, R4       
                                nop                             
                                not              R4, R4         
                                nop                             
                                add              R4, 1, R4      
                loop_0:
                                move             80, R5         
                                move             80, R6         
                loop_1:
                                upd_param        4              
                                wait             66             
                                move             4, R7          
                                add              R6, 0, R8      
                                nop                             
                                sub              R7, R8, R9     
                                nop                             
                                jlt              R9, 2147483648, @other_max_duration_0
                                move             R8, R9         
                after_other_max_duration_0:
                                move             0, R10         
                                nop                             
                                sub              R9, R10, R11   
                                nop                             
                                jlt              R11, 2147483648, @dynamic_sync_0
                                jge              R11, 4294967293, @negative_one_two_three_0
                after_dynamic_sync_0:
                                wait             359            
                                play             0, 0, 4        
                                acquire_weighed  0, R2, R1, R1, 1385
                                add              R2, 1, R2      
                                wait             65532          
                                wait             65532          
                                wait             65532          
                                wait             3474           
                                move             4, R7          
                                add              R6, 0, R8      
                                nop                             
                                sub              R7, R8, R9     
                                nop                             
                                jlt              R9, 2147483648, @other_max_duration_1
                                move             R8, R9         
                after_other_max_duration_1:
                                move             0, R12         
                                nop                             
                                sub              R9, R12, R11   
                                nop                             
                                jlt              R11, 2147483648, @dynamic_sync_1
                                jge              R11, 4294967293, @negative_one_two_three_1
                after_dynamic_sync_1:
                                wait             359            
                                play             0, 0, 4        
                                acquire_weighed  0, R2, R1, R1, 1385
                                add              R2, 1, R2      
                                wait             65532          
                                wait             65532          
                                wait             65532          
                                wait             3404           
                                add              R6, 1, R6      
                                loop             R5, @loop_1    
                                add              R4, 983, R4    
                                loop             R3, @loop_0    
                                loop             R0, @avg_0     
                                set_mrk          0              
                                upd_param        4              
                                stop                            
                dynamic_sync_0:
                                jlt              R11, 1, @after_dynamic_sync_0
                                jlt              R11, 4, @one_two_three_0
                                jge              R11, 65532, @long_wait_sync_0
                                wait             R11            
                                jmp              @after_dynamic_sync_0
                one_two_three_0:
                                add              R11, 4, R11    
                                nop                             
                                wait             R11            
                                jmp              @after_dynamic_sync_0
                negative_one_two_three_0:
                                wait             4              
                                jmp              @after_dynamic_sync_0
                long_wait_sync_0:
                                wait             65532          
                                sub              R11, 65532, R11
                                nop                             
                                jge              R11, 65532, @long_wait_sync_0
                                jmp              @dynamic_sync_0
                other_max_duration_0:
                                move             R7, R9         
                                jmp              @after_other_max_duration_0
                dynamic_sync_1:
                                jlt              R11, 1, @after_dynamic_sync_1
                                jlt              R11, 4, @one_two_three_1
                                jge              R11, 65532, @long_wait_sync_1
                                wait             R11            
                                jmp              @after_dynamic_sync_1
                one_two_three_1:
                                add              R11, 4, R11    
                                nop                             
                                wait             R11            
                                jmp              @after_dynamic_sync_1
                negative_one_two_three_1:
                                wait             4              
                                jmp              @after_dynamic_sync_1
                long_wait_sync_1:
                                wait             65532          
                                sub              R11, 65532, R11
                                nop                             
                                jge              R11, 65532, @long_wait_sync_1
                                jmp              @dynamic_sync_1
                other_max_duration_1:
                                move             R7, R9         
                                jmp              @after_other_max_duration_1"""

        flux_str="""setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              
                main:
                                move             2000, R0       
                avg_0:
                                move             21, R1         
                                move             9830, R2       
                                nop                             
                                not              R2, R2         
                                nop                             
                                add              R2, 1, R2      
                loop_0:
                                move             80, R3         
                                move             80, R4         
                loop_1:
                                set_awg_gain     R2, R2         
                                set_awg_gain     R2, R2         
                                upd_param        4              
                                wait             66             
                                play             0, 1, 4        
                                move             0, R5          
                                add              R4, 0, R6      
                                nop                             
                                sub              R5, R6, R7     
                                nop                             
                                jlt              R7, 2147483648, @other_max_duration_0
                                move             R6, R7         
                after_other_max_duration_0:
                                move             4, R8          
                                nop                             
                                sub              R7, R8, R9     
                                nop                             
                                jlt              R9, 2147483648, @dynamic_sync_0
                                jge              R9, 4294967293, @negative_one_two_three_0
                after_dynamic_sync_0:
                                play             2, 1, 4        
                                wait             1744           
                                wait             65532          
                                wait             65532          
                                wait             65532          
                                wait             3474           
                                play             0, 1, 4        
                                move             0, R5          
                                add              R4, 0, R6      
                                nop                             
                                sub              R5, R6, R7     
                                nop                             
                                jlt              R7, 2147483648, @other_max_duration_1
                                move             R6, R7         
                after_other_max_duration_1:
                                move             4, R10         
                                nop                             
                                sub              R7, R10, R9    
                                nop                             
                                jlt              R9, 2147483648, @dynamic_sync_1
                                jge              R9, 4294967293, @negative_one_two_three_1
                after_dynamic_sync_1:
                                play             2, 1, 4        
                                wait             1744           
                                wait             65532          
                                wait             65532          
                                wait             65532          
                                wait             3404           
                                add              R4, 1, R4      
                                loop             R3, @loop_1    
                                add              R2, 983, R2    
                                loop             R1, @loop_0    
                                loop             R0, @avg_0     
                                set_mrk          0              
                                upd_param        4              
                                stop                            
                dynamic_sync_0:
                                jlt              R9, 1, @after_dynamic_sync_0
                                jlt              R9, 4, @one_two_three_0
                                jge              R9, 65532, @long_wait_sync_0
                                wait             R9             
                                jmp              @after_dynamic_sync_0
                one_two_three_0:
                                add              R9, 4, R9      
                                nop                             
                                wait             R9             
                                jmp              @after_dynamic_sync_0
                negative_one_two_three_0:
                                wait             4              
                                jmp              @after_dynamic_sync_0
                long_wait_sync_0:
                                wait             65532          
                                sub              R9, 65532, R9  
                                nop                             
                                jge              R9, 65532, @long_wait_sync_0
                                jmp              @dynamic_sync_0
                other_max_duration_0:
                                move             R5, R7         
                                jmp              @after_other_max_duration_0
                dynamic_sync_1:
                                jlt              R9, 1, @after_dynamic_sync_1
                                jlt              R9, 4, @one_two_three_1
                                jge              R9, 65532, @long_wait_sync_1
                                wait             R9             
                                jmp              @after_dynamic_sync_1
                one_two_three_1:
                                add              R9, 4, R9      
                                nop                             
                                wait             R9             
                                jmp              @after_dynamic_sync_1
                negative_one_two_three_1:
                                wait             4              
                                jmp              @after_dynamic_sync_1
                long_wait_sync_1:
                                wait             65532          
                                sub              R9, 65532, R9  
                                nop                             
                                jge              R9, 65532, @long_wait_sync_1
                                jmp              @dynamic_sync_1
                other_max_duration_1:
                                move             R5, R7         
                                jmp              @after_other_max_duration_1
                                
                                """

        assert is_q1asm_equal(sequences.sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences.sequences["readout"], readout_str)
        assert is_q1asm_equal(sequences.sequences["flux"], flux_str)


    def test_dynamic_wait_three_buses_dynamic_static(self, dynamic_wait_three_buses_dynamic_static):
        compiler = QbloxCompiler()
        sequences = compiler.compile(dynamic_wait_three_buses_dynamic_static)
        flux_str = """setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

main:
                move             11, R0         
                move             100, R1        
loop_0:
                move             0, R2          
                add              R1, 0, R3      
                nop                             
                sub              R2, R3, R4     
                nop                             
                jlt              R4, 2147483648, @other_max_duration_0
                move             R3, R4         
after_other_max_duration_0:


                move             0, R5          
                nop                             
                sub              R4, R5, R6     
                nop                             
                jlt              R6, 2147483648, @dynamic_sync_0
                jge              R6, 4294967293, @negative_one_two_three_0
after_dynamic_sync_0:


                wait             40             
                move             0, R2          
                add              R1, 0, R3      
                nop                             
                sub              R2, R3, R4     
                nop                             
                jlt              R4, 2147483648, @other_max_duration_1
                move             R3, R4         
after_other_max_duration_1:


                move             0, R7          
                nop                             
                sub              R4, R7, R6     
                nop                             
                jlt              R6, 2147483648, @dynamic_sync_1
                jge              R6, 4294967293, @negative_one_two_three_1
after_dynamic_sync_1:


                play             0, 1, 40       
                add              R1, 10, R1     
                loop             R0, @loop_0    
                set_mrk          0              
                upd_param        4              
                stop                            
dynamic_sync_0:


                jlt              R6, 1, @after_dynamic_sync_0
                jlt              R6, 4, @one_two_three_0
                jge              R6, 65532, @long_wait_sync_0
                wait             R6             
                jmp              @after_dynamic_sync_0
one_two_three_0:


                add              R6, 4, R6      
                nop                             
                wait             R6             
                jmp              @after_dynamic_sync_0
negative_one_two_three_0:


                wait             4              
                jmp              @after_dynamic_sync_0
long_wait_sync_0:


                wait             65532          
                sub              R6, 65532, R6  
                nop                             
                jge              R6, 65532, @long_wait_sync_0
                jmp              @dynamic_sync_0
other_max_duration_0:


                move             R2, R4         
                jmp              @after_other_max_duration_0
dynamic_sync_1:


                jlt              R6, 1, @after_dynamic_sync_1
                jlt              R6, 4, @one_two_three_1
                jge              R6, 65532, @long_wait_sync_1
                wait             R6             
                jmp              @after_dynamic_sync_1
one_two_three_1:


                add              R6, 4, R6      
                nop                             
                wait             R6             
                jmp              @after_dynamic_sync_1
negative_one_two_three_1:


                wait             4              
                jmp              @after_dynamic_sync_1
long_wait_sync_1:


                wait             65532          
                sub              R6, 65532, R6  
                nop                             
                jge              R6, 65532, @long_wait_sync_1
                jmp              @dynamic_sync_1
other_max_duration_1:


                move             R2, R4         
                jmp              @after_other_max_duration_1"""
        
        assert is_q1asm_equal(sequences.sequences["flux"], flux_str)

    def test_dynamic_wait_three_buses_static_static(self, dynamic_wait_three_buses_static_static):
        compiler = QbloxCompiler()
        sequences = compiler.compile(dynamic_wait_three_buses_static_static)
        flux_str = """setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

main:
                move             11, R0         
                move             100, R1        
loop_0:
                move             0, R2          
                add              R1, 0, R3      
                nop                             
                sub              R2, R3, R4     
                nop                             
                jlt              R4, 2147483648, @other_max_duration_0
                move             R3, R4         
after_other_max_duration_0:


                move             0, R5          
                nop                             
                sub              R4, R5, R6     
                nop                             
                jlt              R6, 2147483648, @dynamic_sync_0
                jge              R6, 4294967293, @negative_one_two_three_0
after_dynamic_sync_0:


                wait             50             
                play             0, 1, 40       
                add              R1, 10, R1     
                loop             R0, @loop_0    
                set_mrk          0              
                upd_param        4              
                stop                            
dynamic_sync_0:


                jlt              R6, 1, @after_dynamic_sync_0
                jlt              R6, 4, @one_two_three_0
                jge              R6, 65532, @long_wait_sync_0
                wait             R6             
                jmp              @after_dynamic_sync_0
one_two_three_0:


                add              R6, 4, R6      
                nop                             
                wait             R6             
                jmp              @after_dynamic_sync_0
negative_one_two_three_0:


                wait             4              
                jmp              @after_dynamic_sync_0
long_wait_sync_0:


                wait             65532          
                sub              R6, 65532, R6  
                nop                             
                jge              R6, 65532, @long_wait_sync_0
                jmp              @dynamic_sync_0
other_max_duration_0:


                move             R2, R4         
                jmp              @after_other_max_duration_0"""
        
        assert is_q1asm_equal(sequences.sequences["flux"], flux_str)

    def test_measure_reset_calibration_and_mapping(self, measure_reset_calibrated_bus_mapping: QProgram, calibration_reset: Calibration):
        compiler = QbloxCompiler()

        bus_mapping = {"drive_bus": "drive_q0_bus", "readout_bus": "readout_q0_bus"}


        sequences, _ = compiler.compile(qprogram=measure_reset_calibrated_bus_mapping, bus_mapping=bus_mapping, calibration=calibration_reset)

        assert len(sequences) == 2
        assert "drive_q0_bus" in sequences
        assert "readout_q0_bus" in sequences

        drive_str = """
            setup:
                            set_latch_en     1, 4           
                            wait_sync        4              
                            set_mrk          0              
                            upd_param        4              

            main:
                            latch_rst        4              
                            wait             2400          
                            set_cond         1, 1, 0, 100   
                            play             0, 1, 100      
                            set_cond         0, 0, 0, 4     
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
                play             0, 1, 4        
                acquire_weighed  0, 0, 0, 1, 2000
                set_mrk          0              
                upd_param        4              
                stop                            
        """
        print(sequences["readout_q0_bus"]._program)
        assert is_q1asm_equal(sequences["drive_q0_bus"], drive_str)
        assert is_q1asm_equal(sequences["readout_q0_bus"], readout_str)

    def test_crosstalk_compensation(self, crosstalk_qprogram: QProgram):

        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=crosstalk_qprogram, crosstalk=crosstalk)

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)
            
        flux1_str = """
        setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

        main:
                move             10, R0         
                move             0, R1          
                move             0, R2          
        loop_0:
                set_awg_offs     R1, R1         
                upd_param        4              
                wait             6              
                set_awg_gain     819, 819       
                set_awg_gain     819, 819       
                play             0, 1, 50       
                wait             54             
                add              R1, 327, R1    
                add              R2, 163, R2    
                loop             R0, @loop_0    
                set_mrk          0              
                upd_param        4              
                stop
        """
        flux2_str = """
        setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

        main:
                move             10, R0         
                move             0, R1          
                move             0, R2          
        loop_0:
                set_awg_offs     R2, R2         
                upd_param        4              
                wait             6              
                set_awg_gain     1638, 1638     
                set_awg_gain     1638, 1638     
                play             0, 1, 50       
                wait             54             
                add              R1, 327, R1    
                add              R2, 163, R2    
                loop             R0, @loop_0    
                nop                             
                set_mrk          0              
                upd_param        4              
                stop
        """
        drive_str = """
        setup:
                wait_sync        4              
                set_mrk          0              
                upd_param        4              

        main:
                move             10, R0         
                move             0, R1          
                move             0, R2          
        loop_0:
                wait             10             
                play             0, 0, 50       
                wait             54             
                add              R1, 327, R1    
                add              R2, 163, R2    
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
                move             0, R0          
                move             0, R1          
                move             10, R2         
                move             0, R3          
                move             0, R4          
        loop_0:
                wait             60             
                play             0, 0, 4        
                acquire_weighed  0, R1, R0, R0, 50
                add              R1, 1, R1      
                add              R3, 327, R3    
                add              R4, 163, R4    
                loop             R2, @loop_0    
                set_mrk          0              
                upd_param        4              
                stop
        """

        assert is_q1asm_equal(sequences["flux1"], flux1_str)
        assert is_q1asm_equal(sequences["flux2"], flux2_str)
        assert is_q1asm_equal(sequences["drive"], drive_str)
        assert is_q1asm_equal(sequences["readout"], readout_str)
        
    def test_crosstalk_compensation_through_calibration(self, crosstalk_qprogram: QProgram, calibration_crosstalk: Calibration):

        compiler = QbloxCompiler()
        sequences, _ = compiler.compile(qprogram=crosstalk_qprogram, calibration=calibration_crosstalk)

        for bus in sequences:
            assert isinstance(sequences[bus], QPy.Sequence)
