import pytest

from qililab import Domain, DragPair, Gaussian, IQPair, QProgram, QuantumMachinesCompiler, Square
from qililab.qprogram.blocks import ForLoop


@pytest.fixture(name="runcard_configuration")
def fixture_runcard_configuration() -> dict:
    runcard_configuration = {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},  # I qubit_0
                    2: {"offset": 0.0},  # Q qubit_0
                    3: {"offset": 0.0},  # I qubit_1
                    4: {"offset": 0.0},  # Q qubit_1
                    5: {"offset": 0.0},  # flux qubit_0
                    6: {"offset": 0.0},  # flux qubit_1
                    7: {"offset": 0.0},  # I resonator
                    8: {"offset": 0.0},  # Q resonator
                },
                "digital_outputs": {
                    1: {},
                },
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            },
        },
        "elements": {
            "qubit_0": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 100e6,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 7.4e9,
            },
            "qubit_1": {
                "mixInputs": {
                    "I": ("con1", 3),
                    "Q": ("con1", 4),
                    "lo_frequency": 100e6,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 7.4e9,
            },
            "flux_0": {
                "singleInput": {
                    "port": ("con1", 5),
                },
            },
            "flux_1": {
                "singleInput": {
                    "port": ("con1", 6),
                },
            },
            "resonator": {
                "mixInputs": {
                    "I": ("con1", 7),
                    "Q": ("con1", 8),
                    "lo_frequency": 150e6,
                    "mixer": "mixer_resonator",
                },
                "intermediate_frequency": 6e9,
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": 120,
                "smearing": 0,
            },
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 100e6,
                    "lo_frequency": 7.4e9,
                    "correction": [1.0, 0.0, 0.0, 1.0],
                }
            ],
            "mixer_resonator": [
                {
                    "intermediate_frequency": 6e9,
                    "lo_frequency": 100e6,
                    "correction": [1.0, 0.0, 0.0, 1.0],
                }
            ],
        },
    }

    return runcard_configuration


@pytest.fixture(name="play_operation")
def fixture_play_operation() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.play(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="play_operations_share_waveforms")
def fixture_play_operations_share_waveforms() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.play(bus="drive", waveform=drag_wf)
    qp.play(bus="drive", waveform=DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5))

    return qp


@pytest.fixture(name="set_gain_and_play_operation")
def fixture_set_gain_and_play_operation() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
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


@pytest.fixture(name="measure_operation_with_no_weights")
def fixture_measure_operation_with_no_weights() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf)

    return qp


@pytest.fixture(name="measure_operation_with_no_raw_adc")
def fixture_measure_operation_with_no_raw_adc() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, save_raw_adc=False)

    return qp


@pytest.fixture(name="measure_operation_with_one_weight")
def fixture_measure_operation_with_one_weight() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_wf = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=weight_wf)

    return qp


@pytest.fixture(name="measure_operation_with_two_weights")
def fixture_measure_operation_with_two_weights() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_I = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_Q = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_I, weight_Q))

    return qp


@pytest.fixture(name="measure_operation_with_four_weights")
def fixture_measure_operation_with_four_weights() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D))

    return qp


@pytest.fixture(name="measure_operation_with_one_weight_no_demodulation")
def fixture_measure_operation_with_one_weight_no_demodulation() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_wf = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=weight_wf, demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_two_weights_no_demodulation")
def fixture_measure_operation_with_two_weights_no_demodulation() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_I = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_Q = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_I, weight_Q), demodulation=False)

    return qp


@pytest.fixture(name="measure_operation_with_four_weights_no_demodulation")
def fixture_measure_operation_with_four_weights_no_demodulation() -> QProgram:
    drag_wf = DragPair(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_A = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    weight_B = IQPair(I=Square(0.5, duration=200), Q=Square(0.5, duration=200))
    weight_C = IQPair(I=Square(0.0, duration=200), Q=Square(1.0, duration=200))
    weight_D = weight_A
    qp = QProgram()
    qp.measure(bus="drive", waveform=drag_wf, weights=(weight_A, weight_B, weight_C, weight_D), demodulation=False)

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
        assert float(update_frequency.value.literal.value) == 100e6 * 1e3

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

    def test_measure_operation_with_no_weights(self, measure_operation_with_no_weights: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(measure_operation_with_no_weights)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(result_handles) == 2
        assert "adc1" in result_handles
        assert "adc2" in result_handles

    def test_measure_operation_with_no_raw_adc(self, measure_operation_with_no_raw_adc: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(measure_operation_with_no_raw_adc)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 1

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(result_handles) == 0

    def test_measure_operation_with_one_weight(self, measure_operation_with_one_weight: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(measure_operation_with_one_weight)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 1
        assert measure.measure_processes[0].analog.demod_integration.element_output == "out1"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 1

        assert len(result_handles) == 3
        assert "adc1" in result_handles
        assert "adc2" in result_handles
        assert "I" in result_handles

    def test_measure_operation_with_two_weights(self, measure_operation_with_two_weights: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(measure_operation_with_two_weights)

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

        assert len(result_handles) == 4
        assert "adc1" in result_handles
        assert "adc2" in result_handles
        assert "I" in result_handles
        assert "Q" in result_handles

    def test_measure_operation_with_four_weights(self, measure_operation_with_four_weights: QProgram):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(measure_operation_with_four_weights)

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

        assert len(result_handles) == 4
        assert "adc1" in result_handles
        assert "adc2" in result_handles
        assert "I" in result_handles
        assert "Q" in result_handles

    def test_measure_operation_with_one_weight_no_demodulation(
        self, measure_operation_with_one_weight_no_demodulation: QProgram
    ):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(measure_operation_with_one_weight_no_demodulation)

        statements = qua_program._program.script.body.statements
        assert len(statements) == 2

        measure = statements[0].measure
        assert measure.qe.name == "drive"
        assert measure.pulse.name in configuration["pulses"]

        assert len(measure.measure_processes) == 1
        assert measure.measure_processes[0].analog.bare_integration.element_output == "out1"

        measurement_pulse = configuration["pulses"][measure.pulse.name]
        assert len(measurement_pulse["integration_weights"]) == 1

        assert len(result_handles) == 3
        assert "adc1" in result_handles
        assert "adc2" in result_handles
        assert "I" in result_handles

    def test_measure_operation_with_two_weights_no_demodulation(
        self, measure_operation_with_two_weights_no_demodulation: QProgram
    ):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(
            measure_operation_with_two_weights_no_demodulation
        )

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

        assert len(result_handles) == 4
        assert "adc1" in result_handles
        assert "adc2" in result_handles
        assert "I" in result_handles
        assert "Q" in result_handles

    def test_measure_operation_with_four_weights_no_demodulation(
        self, measure_operation_with_four_weights_no_demodulation: QProgram
    ):
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, result_handles = compiler.compile(
            measure_operation_with_four_weights_no_demodulation
        )

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

        assert len(result_handles) == 4
        assert "adc1" in result_handles
        assert "adc2" in result_handles
        assert "I" in result_handles
        assert "Q" in result_handles
