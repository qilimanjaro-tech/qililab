import numpy as np
import pytest

from qililab.qprogram import Domain, QProgram, QuantumMachinesCompiler
from qililab.qprogram.blocks import ForLoop, Loop
from qililab.waveforms import IQPair, Square


@pytest.fixture(name="play_operation")
def fixture_play_operation() -> QProgram:
    ones_zeros_pair = IQPair(I=Square(amplitude=1.0, duration=100), Q=Square(amplitude=0.0, duration=100))
    qp = QProgram()
    qp.play(bus="drive", waveform=ones_zeros_pair)

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


@pytest.fixture(name="set_frequency_operation")
def fixture_set_frequency_operation() -> QProgram:
    qp = QProgram()
    qp.set_frequency(bus="drive", frequency=100e6)

    return qp


@pytest.fixture(name="set_phase_operation")
def fixture_set_phase_operation() -> QProgram:
    qp = QProgram()
    qp.set_phase(bus="drive", phase=90)

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


@pytest.fixture(name="measure_operation_with_no_weights_no_adc")
def fixture_measure_operation_with_no_weights_no_adc() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="measure_operation_with_no_weights")
def fixture_measure_operation_with_no_weights() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, save_raw_adc=True)

    return qp


@pytest.fixture(name="measure_operation_with_one_weight")
def fixture_measure_operation_with_one_weight() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_wf = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=weight_wf)

    return qp


@pytest.fixture(name="measure_operation_with_two_weights")
def fixture_measure_operation_with_two_weights() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_I = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_Q = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_I, weight_Q))

    return qp


@pytest.fixture(name="measure_operation_with_four_weights")
def fixture_measure_operation_with_four_weights() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D))

    return qp


@pytest.fixture(name="measure_operation_with_one_weight_no_demodulation")
def fixture_measure_operation_with_one_weight_no_demodulation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_wf = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=weight_wf, demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_two_weights_no_demodulation")
def fixture_measure_operation_with_two_weights_no_demodulation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_I = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_Q = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_I, weight_Q), demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_four_weights_no_demodulation")
def fixture_measure_operation_with_four_weights_no_demodulation() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D), demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_same_pulse")
def fixture_measure_operation_with_same_pulse() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A

    weight_E = IQPair(I=Square(1.0, 200), Q=Square(1.0, 200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D), demodulation=False)
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_E, weight_B, weight_C, weight_E), demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_average")
def fixture_measure_operation_with_average() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    with qp.average(shots=1000):
        qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D))

    return qp


@pytest.fixture(name="measure_operation_in_for_loop")
def fixture_measure_operation_in_for_loop() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
        qp.set_gain(bus="drive", gain=gain)
        qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D))

    return qp


@pytest.fixture(name="measure_operation_in_loop")
def fixture_measure_operation_in_loop() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    with qp.loop(variable=gain, values=np.arange(start=0, stop=1.05, step=0.1)):
        qp.set_gain(bus="drive", gain=gain)
        qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D))

    return qp


@pytest.fixture(name="measure_operation_in_parallel")
def fixture_measure_operation_in_parallel() -> QProgram:
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    frequency = qp.variable(Domain.Frequency)
    with qp.parallel(
        loops=[
            Loop(variable=gain, values=np.arange(start=0, stop=1.05, step=0.1)),
            Loop(variable=frequency, values=np.arange(start=100, stop=205, step=10)),
        ]
    ):
        qp.set_frequency(bus="drive", frequency=frequency)
        qp.set_gain(bus="drive", gain=gain)
        qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D))

    return qp


@pytest.fixture(name="for_loop")
def fixture_for_loop() -> QProgram:
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    frequency = qp.variable(Domain.Frequency)
    phase = qp.variable(Domain.Phase)
    time = qp.variable(Domain.Time)

    with qp.for_loop(variable=gain, start=0, stop=1.0, step=0.1):
        qp.set_gain(bus="drive", gain=gain)

    with qp.for_loop(variable=frequency, start=100, stop=200, step=10):
        qp.set_frequency(bus="drive", frequency=frequency)

    with qp.for_loop(variable=phase, start=0, stop=90, step=10):
        qp.set_phase(bus="drive", phase=phase)

    with qp.for_loop(variable=time, start=100, stop=200, step=10):
        qp.wait(bus="drive", duration=time)

    return qp


@pytest.fixture(name="for_loop_with_negative_step")
def fixture_for_loop_with_negative_step() -> QProgram:
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    frequency = qp.variable(Domain.Frequency)
    phase = qp.variable(Domain.Phase)
    time = qp.variable(Domain.Time)

    with qp.for_loop(variable=gain, start=1.0, stop=0.0, step=-0.1):
        qp.set_gain(bus="drive", gain=gain)

    with qp.for_loop(variable=frequency, start=200, stop=100, step=-10):
        qp.set_frequency(bus="drive", frequency=frequency)

    with qp.for_loop(variable=phase, start=90, stop=0, step=-10):
        qp.set_phase(bus="drive", phase=phase)

    with qp.for_loop(variable=time, start=200, stop=100, step=-10):
        qp.wait(bus="drive", duration=time)

    return qp


@pytest.fixture(name="loop")
def fixture_loop() -> QProgram:
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    frequency = qp.variable(Domain.Frequency)
    phase = qp.variable(Domain.Phase)
    time = qp.variable(Domain.Time)

    with qp.loop(variable=gain, values=np.arange(start=0, stop=1.05, step=0.1)):
        qp.set_gain(bus="drive", gain=gain)

    with qp.loop(variable=frequency, values=np.arange(start=100, stop=205, step=10)):
        qp.set_frequency(bus="drive", frequency=frequency)

    with qp.loop(variable=phase, values=np.arange(start=0, stop=95, step=10)):
        qp.set_phase(bus="drive", phase=phase)

    with qp.loop(variable=time, values=np.arange(start=100, stop=205, step=10)):
        qp.wait(bus="drive", duration=time)

    return qp


@pytest.fixture(name="parallel")
def fixture_parallel() -> QProgram:
    qp = QProgram()
    gain = qp.variable(Domain.Voltage)
    frequency = qp.variable(Domain.Frequency)
    phase = qp.variable(Domain.Phase)
    time = qp.variable(Domain.Time)

    with qp.parallel(
        loops=[
            ForLoop(variable=gain, start=0, stop=1.0, step=0.1),
            Loop(variable=frequency, values=np.arange(start=100, stop=205, step=10)),
            ForLoop(variable=phase, start=0, stop=90, step=10),
            Loop(variable=time, values=np.arange(start=100, stop=205, step=10)),
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
        assert float(play.amp.v0.literal.value) == 0.5 * 2

    def test_set_frequency_operation(self, set_frequency_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(set_frequency_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        update_frequency = statements[0].update_frequency
        assert update_frequency.qe.name == "drive"
        assert update_frequency.keep_phase is False
        assert float(update_frequency.value.literal.value) == 100e6

    def test_set_phase_operation(self, set_phase_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(set_phase_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        rotation = statements[0].z_rotation
        assert rotation.qe.name == "drive"
        assert float(rotation.value.literal.value) == 90 / 360.0

    def test_reset_phase_operation(self, reset_phase_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(reset_phase_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        reset_frame = statements[0].reset_frame
        assert reset_frame.qe.name == "drive"

    def test_wait_operation(self, wait_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(wait_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        wait = statements[0].wait
        assert len(wait.qe) == 1
        assert wait.qe[0].name == "drive"
        assert int(wait.time.literal.value) == 100

    def test_sync_operation(self, sync_operation: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(sync_operation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        align = statements[0].align
        assert len(align.qe) == 2
        assert align.qe[0].name == "drive"
        assert align.qe[1].name == "readout"

    def test_sync_operation_no_parameters(self, sync_operation_no_parameters: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(sync_operation_no_parameters)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        align = statements[2].align
        assert len(align.qe) == 0

    def test_measure_operation_with_no_weights_no_adc(self, measure_operation_with_no_weights_no_adc: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_no_weights_no_adc)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 0

    def test_measure_operation_with_no_weights(self, measure_operation_with_no_weights: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_no_weights)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "adc1_0" in measurements[0].result_handles
        assert "adc2_0" in measurements[0].result_handles

    def test_measure_operation_with_one_weight(self, measure_operation_with_one_weight: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_one_weight)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 1
        assert measure.measure_processes[0].analog.demod_integration.element_output == "out1"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 1

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 1
        assert "I_0" in measurements[0].result_handles

    def test_measure_operation_with_two_weights(self, measure_operation_with_two_weights: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_two_weights)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.demod_integration.element_output == "out1"
        assert measure.measure_processes[1].analog.demod_integration.element_output == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 2

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_four_weights(self, measure_operation_with_four_weights: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_four_weights)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[0].analog.dual_demod_integration.element_output2 == "out2"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_demod_integration.element_output2 == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 3

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_one_weight_no_demodulation(
        self, measure_operation_with_one_weight_no_demodulation: QProgram
    ):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_one_weight_no_demodulation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 1
        assert measure.measure_processes[0].analog.bare_integration.element_output == "out1"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 1

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 1
        assert "I_0" in measurements[0].result_handles

    def test_measure_operation_with_two_weights_no_demodulation(
        self, measure_operation_with_two_weights_no_demodulation: QProgram
    ):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_two_weights_no_demodulation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.bare_integration.element_output == "out1"
        assert measure.measure_processes[1].analog.bare_integration.element_output == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 2

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_four_weights_no_demodulation(
        self, measure_operation_with_four_weights_no_demodulation: QProgram
    ):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_four_weights_no_demodulation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 3

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 2
        assert measure.measure_processes[0].analog.dual_bare_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_bare_integration.element_output1 == "out1"
        assert measure.measure_processes[1].analog.dual_bare_integration.element_output2 == "out2"
        assert measure.measure_processes[0].analog.dual_bare_integration.element_output2 == "out2"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 3

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_average(self, measure_operation_with_average: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, measurements = compiler.compile(measure_operation_with_average)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        assert len(measurements) == 1
        assert len(measurements[0].result_handles) == 2
        assert "I_0" in measurements[0].result_handles
        assert "Q_0" in measurements[0].result_handles

    def test_measure_operation_with_same_pulse_updates_it_correctly(self, measure_operation_with_same_pulse: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(measure_operation_with_same_pulse)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 6

        measure_0 = statements[0].measure
        assert measure_0.qe.name == "drive"
        assert measure_0.pulse.name in configuration["pulses"]

        measure_1 = statements[3].measure
        assert measure_1.qe.name == "drive"
        assert measure_1.pulse.name in configuration["pulses"]

        assert measure_0.pulse.name == measure_1.pulse.name

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

    def test_for_loop(self, for_loop: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(for_loop)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 4

        # Voltage
        assert float(statements[0].for_.init.statements[0].assign.expression.literal.value) == 0
        assert float(statements[0].for_.condition.binary_operation.right.literal.value) == 1.0
        assert (
            float(statements[0].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == 0.1
        )

        # Frequency
        assert float(statements[1].for_.init.statements[0].assign.expression.literal.value) == 100
        assert float(statements[1].for_.condition.binary_operation.right.literal.value) == 200
        assert (
            float(statements[1].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == 10
        )

        # Phase
        assert float(statements[2].for_.init.statements[0].assign.expression.literal.value) == 0 / 360.0
        assert float(statements[2].for_.condition.binary_operation.right.literal.value) == 90 / 360.0
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
        assert len(statements) == 4

        # Voltage
        assert float(statements[0].for_.init.statements[0].assign.expression.literal.value) == 1.0
        assert float(statements[0].for_.condition.binary_operation.right.literal.value) == 0
        assert (
            float(statements[0].for_.update.statements[0].assign.expression.binary_operation.right.literal.value)
            == -0.1
        )

        # Frequency
        assert float(statements[1].for_.init.statements[0].assign.expression.literal.value) == 200
        assert float(statements[1].for_.condition.binary_operation.right.literal.value) == 100
        assert (
            float(statements[1].for_.update.statements[0].assign.expression.binary_operation.right.literal.value) == -10
        )

        # Phase
        assert float(statements[2].for_.init.statements[0].assign.expression.literal.value) == 90 / 360.0
        assert float(statements[2].for_.condition.binary_operation.right.literal.value) == 0 / 360.0
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
        assert len(statements) == 4
        assert len(statements[0].for_each.iterator) == 1
        assert len(statements[1].for_each.iterator) == 1
        assert len(statements[2].for_each.iterator) == 1
        assert len(statements[3].for_each.iterator) == 1

    def test_parallel(self, parallel: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(parallel)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1
        assert len(statements[0].for_each.iterator) == 4

    def test_infinite_loop(self, infinite_loop: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, _, _ = compiler.compile(infinite_loop)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1
        assert bool(statements[0].for_.condition.literal.value) is True

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
