from dataclasses import asdict

import pytest
from qibo.gates import I, M, X, Y

from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.settings import RuncardSchema


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
            if not hasattr(gate_class, "settings"):
                gate_class.settings = {}
            gate_class.settings[qubit] = gate_class.HardwareGateSettings(**settings_dict)


class TestHardwareGates:
    @pytest.mark.parametrize("qubit", [0, 1])
    @pytest.mark.parametrize("qibo_gate", [I, X, Y, M])
    def test_gate_settings_method(self, qubit: int, qibo_gate: str):
        settings = HardwareGateFactory.gate_settings(qibo_gate(qubit))  # type: ignore
        assert isinstance(settings, HardwareGate.HardwareGateSettings)
