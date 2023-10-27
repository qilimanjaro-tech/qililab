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

        rotation = statements[0].reset_frame
        assert rotation.qe.name == "drive"
        assert float(rotation.value.literal.value) == 90 / 360.0
