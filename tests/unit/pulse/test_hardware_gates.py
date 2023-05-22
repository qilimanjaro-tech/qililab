import re
from dataclasses import asdict

import pytest
from qibo.gates import CZ, RX, RY, U2, Gate, I, M, X, Y

from qililab.chip import Chip
from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.settings import RuncardSchema
from qililab.transpiler import Drag, Park


@pytest.fixture(name="platform_settings")
def fixture_platform_settings() -> RuncardSchema.PlatformSettings:
    """Fixture that returns an instance of a ``RuncardSchema.PlatformSettings`` class."""
    settings = {
        "id_": 0,
        "category": "platform",
        "name": "dummy",
        "device_id": 9,
        "minimum_clock_time": 4,
        "delay_between_pulses": 0,
        "delay_before_readout": 0,
        "master_amplitude_gate": 1,
        "master_duration_gate": 40,
        "reset_method": "passive",
        "passive_reset_duration": 100,
        "timings_calculation_method": "as_soon_as_possible",
        "operations": [],
        "gates": {
            0: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "X",
                    "amplitude": 0.8,
                    "phase": 0,
                    "duration": 45,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                },
                {
                    "name": "Y",
                    "amplitude": 0.3,
                    "phase": 90,
                    "duration": 40,
                    "shape": {"name": "gaussian", "num_sigmas": 4},
                },
                {
                    "name": "Drag",
                    "amplitude": 0.3,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {
                    "name": "Park",
                    "amplitude": 1.0,
                    "phase": None,
                    "duration": 40,
                    "shape": {
                        "name": "Park",
                        "amplitude": 1.0,
                        "phase": None,
                        "duration": 83,
                        "shape": {"name": "rectangular"},
                    },
                },
            ],
            1: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "X",
                    "amplitude": 0.8,
                    "phase": 0,
                    "duration": 45,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                },
                {
                    "name": "Y",
                    "amplitude": 0.3,
                    "phase": 90,
                    "duration": 40,
                    "shape": {"name": "gaussian", "num_sigmas": 4},
                },
                {
                    "name": "Drag",
                    "amplitude": 0.3,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {
                    "name": "Park",
                    "amplitude": 1.0,
                    "phase": None,
                    "duration": 40,
                    "shape": {
                        "name": "Park",
                        "amplitude": 1.0,
                        "phase": None,
                        "duration": 83,
                        "shape": {"name": "rectangular"},
                    },
                },
            ],
            (0, 1): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.0, "t_phi": 1},
                },
            ],
        },
    }
    return RuncardSchema.PlatformSettings(**settings)  # type: ignore  # pylint: disable=unexpected-keyword-arg


@pytest.fixture(autouse=True)
def initialize_hardware_gates(platform_settings: RuncardSchema.PlatformSettings):
    for qubit, gate_settings_list in platform_settings.gates.items():
        for gate_settings in gate_settings_list:
            settings_dict = asdict(gate_settings)
            gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
            if not gate_class.settings:
                gate_class.settings = {}
            gate_class.settings[qubit] = gate_class.HardwareGateSettings(**settings_dict)


class TestHardwareGates:
    @pytest.mark.parametrize("qubit", [0, 1])
    @pytest.mark.parametrize("gate_name", ["I", "X", "Y", "Drag", "M", "Park", "CZ"])
    def test_parameters_method(self, qubit: int, gate_name: str):
        gate = HardwareGateFactory.get(gate_name)
        # there's only one 2q gate so we treat it as an special case
        if gate_name == "CZ":
            settings = gate.parameters(qubits=(0, 1), master_amplitude_gate=1.0, master_duration_gate=40)
            assert isinstance(settings, HardwareGate.HardwareGateSettings)
        else:
            settings = gate.parameters(qubits=qubit, master_amplitude_gate=1.0, master_duration_gate=40)
            assert isinstance(settings, HardwareGate.HardwareGateSettings)

    @pytest.mark.parametrize("gate_name", ["I", "X", "Y", "Drag", "M", "Park", "CZ"])
    def test_parameters_method_raise_error_when_settings_for_qubit_not_set(self, gate_name: str):
        if gate_name == "CZ":
            qubits = (123, 520)
        else:
            qubit = 151

        gate = HardwareGateFactory.get(gate_name)
        with pytest.raises(
            ValueError,
            match=f"Please specify the parameters of the {gate.name.value} gate for qubit {re.escape(str(qubit))}.",
        ):
            if gate_name == "CZ":
                gate.parameters(qubits=qubits, master_amplitude_gate=1.0, master_duration_gate=40)
            else:
                gate.parameters(qubits=qubit, master_amplitude_gate=1.0, master_duration_gate=40)

    @pytest.mark.parametrize("qubit", [0, 1])
    @pytest.mark.parametrize("gate_name", ["RX", "RY"])
    def test_parameters_method_raise_error_when_settings_not_set(self, qubit: int, gate_name: str):
        gate = HardwareGateFactory.get(gate_name)
        with pytest.raises(ValueError, match=f"Please specify the parameters of the {gate.name.value} gate."):
            gate.parameters(qubits=qubit, master_amplitude_gate=1.0, master_duration_gate=40)

    @pytest.mark.parametrize("gate", [I(0), M(0), X(0), Y(0), RX(0, 90), RY(0, 90), Drag(0, 2, 1.4), Park(1), CZ(0, 1)])
    def test_translate_method(self, gate: Gate):
        gate_settings = HardwareGateFactory.gate_settings(gate=gate, master_amplitude_gate=1.0, master_duration_gate=40)
        assert isinstance(gate_settings, HardwareGate.HardwareGateSettings)
