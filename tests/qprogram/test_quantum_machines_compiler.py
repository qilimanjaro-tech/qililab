from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from qililab import Arbitrary, Calibration, Domain, IQPair, QProgram, QuantumMachinesCompiler, Square
from qililab.qprogram.blocks import ForLoop, Loop


@pytest.fixture(name="calibration")
def fixture_calibration() -> Calibration:
    calibration = Calibration()
    calibration.add_waveform(bus="drive_q0", name="Xpi", waveform=Square(1.0, 100))
    calibration.add_waveform(bus="drive_q1", name="Xpi", waveform=Square(1.0, 150))
    calibration.add_waveform(bus="drive_q2", name="Xpi", waveform=Square(1.0, 200))

    return calibration


@pytest.fixture(name="play_operation")
def fixture_play_operation() -> QProgram:
    ones_zeros_pair = IQPair(I=Square(amplitude=1.0, duration=100), Q=Square(amplitude=0.0, duration=100))
    qp = QProgram()
    qp.play(bus="drive", waveform=ones_zeros_pair)
    qp.play(bus="flux", waveform=ones_zeros_pair)

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


@pytest.fixture(name="play_operations_share_waveforms")
def fixture_play_operations_share_waveforms() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.play(bus="drive", waveform=drag_wf)
    qp.play(bus="drive", waveform=IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5))

    return qp


@pytest.fixture(name="set_gain_and_play_operation")
def fixture_set_gain_and_play_operation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.set_gain(bus="drive", gain=0.5)
    qp.play(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="play_named_operation")
def fixture_play_named_operation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.play(bus="drive", waveform="Xpi")
    qp.play(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="set_frequency_operation")
def fixture_set_frequency_operation() -> QProgram:
    qp = QProgram()
    qp.set_frequency(bus="drive", frequency=100e6)

    return qp


@pytest.fixture(name="set_offset_operation")
def fixture_set_offset_operation() -> QProgram:
    qp = QProgram()
    qp.set_offset(bus="drive", offset_path0=0.1, offset_path1=0.2)

    return qp


@pytest.fixture(name="set_dc_offset_operation")
def fixture_set_dc_offset_operation() -> QProgram:
    qp = QProgram()
    qp.set_offset(bus="drive", offset_path0=0.1)

    return qp


@pytest.fixture(name="set_phase_operation")
def fixture_set_phase_operation() -> QProgram:
    qp = QProgram()
    qp.set_phase(bus="drive", phase=np.pi / 2)

    return qp


@pytest.fixture(name="reset_phase_operation")
def fixture_reset_phase_operation() -> QProgram:
    qp = QProgram()
    qp.reset_phase(bus="drive")

    return qp


@pytest.fixture(name="wait_operation")
def fixture_wait_operation() -> QProgram:
    qp = QProgram()
    qp.wait(bus="drive", duration=100)

    return qp


@pytest.fixture(name="sync_operation")
def fixture_sync_operation() -> QProgram:
    qp = QProgram()
    qp.sync(buses=["drive", "readout"])

    return qp


@pytest.fixture(name="sync_operation_no_parameters")
def fixture_sync_operation_no_parameters() -> QProgram:
    qp = QProgram()
    qp.wait(bus="drive", duration=100)
    qp.wait(bus="readout", duration=200)
    qp.sync()

    return qp


@pytest.fixture(name="measure_operation")
def fixture_measure_operation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    qp.measure(bus="readout", waveform=drag_wf, weights=weights)

    return qp


@pytest.fixture(name="measure_operation_save_raw_adc")
def fixture_measure_operation_save_raw_adc() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    qp.quantum_machines.measure(bus="readout", waveform=drag_wf, weights=weights, save_adc=True)

    return qp


@pytest.fixture(name="measure_operation_no_demodulation")
def fixture_measure_operation_no_demodulation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    qp.quantum_machines.measure(bus="readout", waveform=drag_wf, weights=weights, demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_same_pulse")
def fixture_measure_operation_with_same_pulse() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    weights2 = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))

    qp = QProgram()
    qp.quantum_machines.measure(bus="readout", waveform=drag_wf, weights=weights, demodulation=False)
    qp.quantum_machines.measure(bus="readout", waveform=drag_wf, weights=weights2, demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_average")
def fixture_measure_operation_with_average() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    with qp.average(shots=1000):
        qp.measure(bus="readout", waveform=drag_wf, weights=weights)

    return qp


@pytest.fixture(name="measure_operation_with_inner_loop_average")
def fixture_measure_operation_with_inner_loop_averagee() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
        qp.set_gain(bus="readout", gain=gain)
        with qp.average(shots=1000):
            qp.measure(bus="readout", waveform=drag_wf, weights=weights)

    return qp


@pytest.fixture(name="measure_operation_in_for_loop")
def fixture_measure_operation_in_for_loop() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
        qp.set_gain(bus="readout", gain=gain)
        qp.measure(bus="readout", waveform=drag_wf, weights=weights)

    return qp


@pytest.fixture(name="measure_operation_in_loop")
def fixture_measure_operation_in_loop() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.loop(variable=gain, values=np.arange(start=0, stop=1.05, step=0.1)):
        qp.set_gain(bus="readout", gain=gain)
        qp.measure(bus="readout", waveform=drag_wf, weights=weights)

    return qp


@pytest.fixture(name="measure_operation_in_parallel")
def fixture_measure_operation_in_parallel() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weights = IQPair(I=Square(1.0, duration=200), Q=Square(1.0, duration=200))
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    with qp.parallel(
        loops=[
            Loop(variable=gain, values=np.arange(start=0, stop=1.05, step=0.1)),
            Loop(variable=frequency, values=np.arange(start=100, stop=205, step=10)),
        ]
    ):
        qp.set_frequency(bus="readout", frequency=frequency)
        qp.set_gain(bus="readout", gain=gain)
        qp.measure(bus="readout", waveform=drag_wf, weights=weights)

    return qp


@pytest.fixture(name="for_loop")
def fixture_for_loop() -> QProgram:
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    phase = qp.variable(label="phase", domain=Domain.Phase)
    time = qp.variable(label="time", domain=Domain.Time)
    scalar = qp.variable(label="int_scalar", domain=Domain.Scalar, type=int)

    with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
        qp.set_gain(bus="drive", gain=gain)

    with qp.for_loop(variable=frequency, start=100, stop=200, step=10):
        qp.set_frequency(bus="drive", frequency=frequency)

    with qp.for_loop(variable=phase, start=0, stop=np.pi / 2, step=np.pi / 18):
        qp.set_phase(bus="drive", phase=phase)

    with qp.for_loop(variable=time, start=100, stop=200, step=10):
        qp.wait(bus="drive", duration=time)

    with qp.for_loop(variable=scalar, start=0, stop=10, step=1):
        qp.wait(bus="drive", duration=100)

    return qp


@pytest.fixture(name="for_loop_with_negative_step")
def fixture_for_loop_with_negative_step() -> QProgram:
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    phase = qp.variable(label="phase", domain=Domain.Phase)
    time = qp.variable(label="time", domain=Domain.Time)
    scalar = qp.variable(label="int_scalar", domain=Domain.Scalar, type=int)

    with qp.for_loop(variable=gain, start=1.0, stop=0.0, step=-0.1):
        qp.set_gain(bus="drive", gain=gain)

    with qp.for_loop(variable=frequency, start=200, stop=100, step=-10):
        qp.set_frequency(bus="drive", frequency=frequency)

    with qp.for_loop(variable=phase, start=np.pi / 2, stop=0, step=-np.pi / 18):
        qp.set_phase(bus="drive", phase=phase)

    with qp.for_loop(variable=time, start=200, stop=100, step=-10):
        qp.wait(bus="drive", duration=time)

    with qp.for_loop(variable=scalar, start=10, stop=0, step=-1):
        qp.wait(bus="drive", duration=100)

    return qp


@pytest.fixture(name="loop")
def fixture_loop() -> QProgram:
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    phase = qp.variable(label="phase", domain=Domain.Phase)
    time = qp.variable(label="time", domain=Domain.Time)
    scalar = qp.variable(label="int_scalar", domain=Domain.Scalar, type=int)

    with qp.loop(variable=gain, values=np.arange(start=0, stop=1.05, step=0.1)):
        qp.set_gain(bus="drive", gain=gain)

    with qp.loop(variable=frequency, values=np.arange(start=100, stop=205, step=10)):
        qp.set_frequency(bus="drive", frequency=frequency)

    with qp.loop(variable=phase, values=np.arange(start=0, stop=95, step=10)):
        qp.set_phase(bus="drive", phase=phase)

    with qp.loop(variable=time, values=np.arange(start=100, stop=205, step=10)):
        qp.wait(bus="drive", duration=time)

    with qp.loop(variable=scalar, values=np.arange(start=0, stop=10, step=1)):
        qp.wait(bus="drive", duration=100)

    return qp


@pytest.fixture(name="parallel")
def fixture_parallel() -> QProgram:
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    frequency = qp.variable(label="frequency", domain=Domain.Frequency)
    phase = qp.variable(label="phase", domain=Domain.Phase)
    time = qp.variable(label="time", domain=Domain.Time)
    scalar = qp.variable(label="int_scalar", domain=Domain.Scalar, type=int)

    with qp.parallel(
        loops=[
            ForLoop(variable=gain, start=0, stop=1.0, step=0.1),
            Loop(variable=frequency, values=np.arange(start=100, stop=205, step=10)),
            ForLoop(variable=phase, start=0, stop=90, step=10),
            Loop(variable=time, values=np.arange(start=100, stop=205, step=10)),
            ForLoop(variable=scalar, start=0, stop=10, step=1),
        ]
    ):
        qp.set_gain(bus="drive", gain=gain)
        qp.set_frequency(bus="drive", frequency=frequency)
        qp.set_phase(bus="drive", phase=phase)
        qp.wait(bus="drive", duration=time)

    return qp


@pytest.fixture(name="infinite_loop")
def fixture_infinite_loop() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    with qp.infinite_loop():
        qp.play(bus="drive", waveform=drag_wf)

    return qp


class TestQuantumMachinesCompiler:
    def test_play_operation(self, play_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, _ = compiler.compile(play_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        play = statements[0].play
        assert play.qe.name == "drive"
        assert play.named_pulse.name in configuration["pulses"]

    def test_play_operation_qdac(self, play_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(play_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_block_handlers(self, measurement_blocked_operation: QProgram):
        drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
        readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
        weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qp_no_block = QProgram()
        qp_no_block.play(bus="drive", waveform=drag_wf)
        qp_no_block.measure(bus="readout", waveform=readout_pair, weights=weights_pair)

        compiler = QuantumMachinesCompiler()
        qua_program, configuration, _ = compiler.compile(qprogram=measurement_blocked_operation)

        qua_program_no_block, _, _ = compiler.compile(qprogram=qp_no_block)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 4

        play = statements[0].play
        assert play.qe.name == "drive"
        assert play.named_pulse.name in configuration["pulses"]

        measure = statements[1].measure
        assert measure.qe.name == "readout"
        assert measure.pulse.name in configuration["pulses"]

        assert qua_program._program == qua_program_no_block._program

    def test_play_operations_share_waveforms(self, play_operations_share_waveforms: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, _ = compiler.compile(play_operations_share_waveforms)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        play1 = statements[0].play
        assert play1.qe.name == "drive"
        assert play1.named_pulse.name in configuration["pulses"]

        play2 = statements[0].play
        assert play2.qe.name == "drive"
        assert play2.named_pulse.name in configuration["pulses"]

        assert play1.named_pulse.name == play2.named_pulse.name

    def test_set_gain_and_play_operation(self, set_gain_and_play_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, _ = compiler.compile(set_gain_and_play_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        play = statements[0].play
        assert play.qe.name == "drive"
        assert play.named_pulse.name in configuration["pulses"]
        assert float(play.amp.v0.literal.value) == 1

    def test_set_gain_and_play_operation_qdac(self, set_gain_and_play_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(set_gain_and_play_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_play_named_operation_and_bus_mapping(self, play_named_operation: QProgram, calibration: Calibration):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(
            play_named_operation, bus_mapping={"drive": "drive_q0"}, calibration=calibration
        )

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        play1 = statements[0].play
        assert play1.qe.name == "drive_q0"

        play2 = statements[1].play
        assert play2.qe.name == "drive_q0"

    def test_play_named_operation_raises_error_if_operations_not_in_calibration(self, play_named_operation: QProgram):
        calibration = Calibration()
        compiler = QuantumMachinesCompiler()
        with pytest.raises(RuntimeError):
            _, _, _ = compiler.compile(play_named_operation, bus_mapping={"drive": "drive_q0"}, calibration=calibration)

    def test_set_frequency_operation(self, set_frequency_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(set_frequency_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        update_frequency = statements[0].update_frequency
        assert update_frequency.qe.name == "drive"
        assert update_frequency.keep_phase is False
        assert float(update_frequency.value.literal.value) == 100e6

    def test_set_frequency_operation_qdac(self, set_frequency_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(set_frequency_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_set_offset_operation(self, set_offset_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(set_offset_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        set_dc_offset = statements[0].set_dc_offset
        assert set_dc_offset.qe.name == "drive"

    def test_set_offset_operation_qdac(self, set_offset_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(set_offset_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_set_dc_offset_operation(self, set_dc_offset_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(set_dc_offset_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        set_dc_offset = statements[0].set_dc_offset
        assert set_dc_offset.qe.name == "drive"

    def test_set_dc_offset_operation_qdac(self, set_dc_offset_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(set_dc_offset_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_set_phase_operation(self, set_phase_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(set_phase_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        rotation = statements[0].z_rotation
        assert rotation.qe.name == "drive"
        assert float(rotation.value.literal.value) == 90 / 360.0

    def test_set_phase_operation_qdac(self, set_phase_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(set_phase_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_reset_phase_operation(self, reset_phase_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(reset_phase_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        reset_frame = statements[0].reset_frame
        assert reset_frame.qe.name == "drive"

    def test_reset_phase_operation_qdac(self, reset_phase_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(reset_phase_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_wait_operation(self, wait_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(wait_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        wait = statements[0].wait
        assert len(wait.qe) == 1
        assert wait.qe[0].name == "drive"
        assert int(wait.time.literal.value) == 100 / 4

    def test_wait_operation_qdac(self, wait_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"
        qua_program, _, _ = compiler.compile(wait_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_sync_operation(self, sync_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(sync_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        align = statements[0].align
        assert len(align.qe) == 2
        assert align.qe[0].name == "drive"
        assert align.qe[1].name == "readout"

    def test_sync_operation_qdac_raises_error(self, sync_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "drive"

        with pytest.raises(ValueError, match="QDACII buses not allowed inside sync function"):
            compiler.compile(sync_operation, qm_buses=[mock_qm_bus])

    def test_sync_operation_no_parameters(self, sync_operation_no_parameters: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(sync_operation_no_parameters)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        align = statements[2].align
        assert len(align.qe) == 0

    def test_measure_operation(self, measure_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "readout"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output2 == "out2"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output2 == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 4

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_qdac(self, measure_operation: QProgram):
        compiler = QuantumMachinesCompiler()

        mock_qm_bus = MagicMock()
        mock_qm_bus.alias = "readout"
        qua_program, _, _ = compiler.compile(measure_operation, qm_buses=[mock_qm_bus])

        statements = qua_program._program.script.body.statements
        assert len(statements) == 0

    def test_measure_operation_save_raw_adc(self, measure_operation_save_raw_adc: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_save_raw_adc)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "readout"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output2 == "out2"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output2 == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 4

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 4
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles
        assert "adc1_0" in measurements[0].result_handles
        assert "adc2_0" in measurements[0].result_handles

    def test_measure_operation_no_demodulation(self, measure_operation_no_demodulation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_no_demodulation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "readout"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.dual_bare_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_bare_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_bare_integration.element_output2 == "out2"
        assert measure.measure_processes[0].analog.dual_bare_integration.element_output2 == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 4

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_same_pulse_updates_it_correctly(self, measure_operation_with_same_pulse: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, _ = compiler.compile(measure_operation_with_same_pulse)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 6

        measure_0 = statements[0].measure
        assert measure_0.qe.name == "readout"
        assert measure_0.pulse.name in configuration["pulses"]

        measure_1 = statements[3].measure
        assert measure_1.qe.name == "readout"
        assert measure_1.pulse.name in configuration["pulses"]

        assert measure_0.pulse.name == measure_1.pulse.name

        assert len(configuration["pulses"][measure_0.pulse.name]["integration_weights"]) == 8

    def test_measure_operation_with_average(self, measure_operation_with_average: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, measurements = compiler.compile(measure_operation_with_average)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_inner_loop_average(self, measure_operation_with_inner_loop_average: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, measurements = compiler.compile(measure_operation_with_inner_loop_average)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_in_for_loop(self, measure_operation_in_for_loop: QProgram):
        compiler = QuantumMachinesCompiler()
        _, _, measurements = compiler.compile(measure_operation_in_for_loop)

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_in_loop(self, measure_operation_in_loop: QProgram):
        compiler = QuantumMachinesCompiler()
        _, _, measurements = compiler.compile(measure_operation_in_loop)

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_in_parallel(self, measure_operation_in_parallel: QProgram):
        compiler = QuantumMachinesCompiler()
        _, _, measurements = compiler.compile(measure_operation_in_parallel)

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_threshold(self, measure_operation: QProgram):
        """Test measurement result contains the provided thresholds."""
        compiler = QuantumMachinesCompiler()
        thresholds = {"readout": 1.0}
        _, _, measurements = compiler.compile(measure_operation, thresholds=thresholds)

        assert len(measurements) == 1
        assert measurements[0].threshold == 1.0

    def test_measure_operation_with_threshold_rotations(self, measure_operation: QProgram):
        """Test compilation of measurement applying the rotations provided in the `threshold_rotations` map"""
        compiler = QuantumMachinesCompiler()
        rotation_angle = np.pi
        threshold_rotations = {"readout": rotation_angle}
        qua_program, configuration, measurements = compiler.compile(
            measure_operation, threshold_rotations=threshold_rotations
        )

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "readout"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output2 == "out2"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output2 == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 4

        A, B, C, D = configuration["integration_weights"].values()
        np.testing.assert_allclose(A["cosine"], [(np.cos(rotation_angle), 200)], atol=1e-15)
        np.testing.assert_allclose(A["sine"], [(np.sin(rotation_angle), 200)], atol=1e-15)

        np.testing.assert_allclose(B["cosine"], [(-np.sin(rotation_angle), 200)], atol=1e-15)
        np.testing.assert_allclose(B["sine"], [(np.cos(rotation_angle), 200)], atol=1e-15)

        np.testing.assert_allclose(C["cosine"], [(np.sin(rotation_angle), 200)], atol=1e-15)
        np.testing.assert_allclose(C["sine"], [(-np.cos(rotation_angle), 200)], atol=1e-15)

        np.testing.assert_allclose(D["cosine"], [(np.cos(rotation_angle), 200)], atol=1e-15)
        np.testing.assert_allclose(D["sine"], [(np.sin(rotation_angle), 200)], atol=1e-15)

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_for_loop(self, for_loop: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(for_loop)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 5

        # Voltage
        assert float(statements[0].for_.init.statements[0].assign.expression.literal.value) == 0
        assert float(statements[0].for_.condition.binary_operation.right.literal.value) == 1.05
        assert (
            float(statements[0].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == 0.1
        )

        # Frequency
        assert float(statements[1].for_.init.statements[0].assign.expression.literal.value) == 100
        assert float(statements[1].for_.condition.binary_operation.right.literal.value) == 205
        assert (
            float(statements[1].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == 10
        )

        # Phase
        assert float(statements[2].for_.init.statements[0].assign.expression.literal.value) == 0 / 360.0
        assert float(statements[2].for_.condition.binary_operation.right.literal.value) == 95 / 360.0
        assert (
            float(statements[2].for_.update.statements[0].assign.expression.binary_operation.right.literal.value)
            == 10 / 360.0
        )

        # Time
        assert float(statements[3].for_.init.statements[0].assign.expression.literal.value) == 100
        assert float(statements[3].for_.condition.binary_operation.right.literal.value) == 200
        assert (
            float(statements[3].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == 10
        )

    def test_for_loop_with_negative_step(self, for_loop_with_negative_step: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(for_loop_with_negative_step)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 5

        # Voltage
        assert float(statements[0].for_.init.statements[0].assign.expression.literal.value) == 1.0
        assert float(statements[0].for_.condition.binary_operation.right.literal.value) == -0.05
        assert (
            float(statements[0].for_.update.statements[0].assign.expression.binary_operation.right.literal.value)
            == -0.1
        )

        # Frequency
        assert float(statements[1].for_.init.statements[0].assign.expression.literal.value) == 200
        assert float(statements[1].for_.condition.binary_operation.right.literal.value) == 95
        assert (
            float(statements[1].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == -10
        )

        # Phase
        assert float(statements[2].for_.init.statements[0].assign.expression.literal.value) == 90 / 360.0
        assert float(statements[2].for_.condition.binary_operation.right.literal.value) == -5 / 360.0
        assert (
            float(statements[2].for_.update.statements[0].assign.expression.binary_operation.right.literal.value)
            == -10 / 360.0
        )

        # Time
        assert float(statements[3].for_.init.statements[0].assign.expression.literal.value) == 200
        assert float(statements[3].for_.condition.binary_operation.right.literal.value) == 100
        assert (
            float(statements[3].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == -10
        )

    def test_loop(self, loop: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(loop)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 5
        assert len(statements[0].for_each.iterator) == 1
        assert len(statements[1].for_each.iterator) == 1
        assert len(statements[2].for_each.iterator) == 1
        assert len(statements[3].for_each.iterator) == 1
        assert len(statements[4].for_each.iterator) == 1

    def test_parallel(self, parallel: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(parallel)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1
        assert len(statements[0].for_each.iterator) == 5

    def test_infinite_loop(self, infinite_loop: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(infinite_loop)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1
        assert bool(statements[0].for_.condition.literal.value) is True

    def test_hash_arbitrary_waveforms(self):
        compiler = QuantumMachinesCompiler()
        waveform0 = Arbitrary(np.ones(3000))
        waveform1 = Arbitrary(np.ones(3004))
        assert compiler._QuantumMachinesCompiler__hash_waveform(
            waveform0
        ) != compiler._QuantumMachinesCompiler__hash_waveform(waveform1)

    @pytest.mark.parametrize(
        "start,stop,step,expected_result",
        [(0, 10, 1, 11), (10, 0, -1, 11), (1, 2.05, 0.1, 11)],
    )
    def test_calculate_iterations(self, start, stop, step, expected_result):
        result = QuantumMachinesCompiler._calculate_iterations(start, stop, step)
        assert result == expected_result

    def test_calculate_iterations_with_zero_step_throws_error(self):
        with pytest.raises(ValueError, match="Step value cannot be zero"):
            QuantumMachinesCompiler._calculate_iterations(100, 200, 0)
