""" Data to use alongside the test suite. """
import copy
from typing import Dict, List

from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, U2, I, M, X, Y

from qililab.constants import DEFAULT_PLATFORM_NAME, YAML


class Platform0:
    """Test data of the platform_0 platform."""

    name = "platform_0"

    platform = {
        YAML.ID: 0,
        YAML.NAME: "platform_0",
        YAML.CATEGORY: "platform",
        YAML.SETTINGS: {
            "readout_duration": 2000,
            "readout_amplitude": 0.4,
            "readout_phase": 0,
            "delay_between_pulses": 0,
            "delay_before_readout": 40,
            "gate_duration": 100,
            "num_sigmas": 4,
            "drag_coefficient": 0,
        },
    }

    qubit_0: dict = {
        YAML.ID: 0,
        YAML.NAME: "qubit",
        YAML.CATEGORY: "qubit",
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    qubit_1 = {
        YAML.ID: 1,
        YAML.NAME: "qubit",
        YAML.CATEGORY: "qubit",
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    qblox_qcm_0 = {
        YAML.ID: 0,
        YAML.NAME: "qblox_qcm",
        YAML.CATEGORY: "awg",
        "ip": "192.168.0.3",
        "firmware": "0.7.0",
        "reference_clock": "internal",
        "sequencer": 0,
        "sync_enabled": True,
        "gain": 1,
        "frequency": 100000000,
    }

    qblox_qrm_0 = {
        YAML.ID: 1,
        YAML.NAME: "qblox_qrm",
        YAML.CATEGORY: "awg",
        "ip": "192.168.0.4",
        "firmware": "0.7.0",
        "reference_clock": "external",
        "sequencer": 0,
        "sync_enabled": True,
        "gain": 0.5,
        "acquire_trigger_mode": "sequencer",
        "scope_acquisition_averaging": False,
        "start_integrate": 130,
        "sampling_rate": 1000000000,
        "integration_length": 2000,
        "integration_mode": "ssb",
        "sequence_timeout": 1,
        "acquisition_timeout": 1,
        "acquisition_name": "single",
        "delay_time": 100,
        "frequency": 20000000,
    }

    resonator_0 = {
        YAML.ID: 0,
        YAML.NAME: "resonator",
        YAML.CATEGORY: "resonator",
        "qubits": [
            {
                YAML.ID: 0,
                YAML.CATEGORY: "qubit",
                "pi_pulse_amplitude": 1,
                "pi_pulse_duration": 100,
                "pi_pulse_frequency": 100000000.0,
                "qubit_frequency": 3544000000.0,
                "min_voltage": 950,
                "max_voltage": 1775,
            }
        ],
    }

    resonator_1 = {
        YAML.ID: 1,
        YAML.NAME: "resonator",
        YAML.CATEGORY: "resonator",
        "qubits": [
            {
                YAML.ID: 1,
                YAML.CATEGORY: "qubit",
                "pi_pulse_amplitude": 1,
                "pi_pulse_duration": 100,
                "pi_pulse_frequency": 100000000.0,
                "qubit_frequency": 3544000000.0,
                "min_voltage": 950,
                "max_voltage": 1775,
            }
        ],
    }

    rohde_schwarz_0 = {
        YAML.ID: 0,
        YAML.NAME: "rohde_schwarz",
        YAML.CATEGORY: "signal_generator",
        "ip": "192.168.0.10",
        "firmware": "4.30.046.295",
        "frequency": 3644000000.0,
        "power": 15,
    }

    rohde_schwarz_1 = {
        YAML.ID: 1,
        YAML.NAME: "rohde_schwarz",  # unique name
        YAML.CATEGORY: "signal_generator",  # general name
        "ip": "192.168.0.7",
        "firmware": "4.30.046.295",
        "frequency": 7307720000.0,
        "power": 15,
    }

    mixer_0 = {
        YAML.ID: 0,
        YAML.CATEGORY: "mixer",  # general name
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    mixer_1 = {
        YAML.ID: 1,
        YAML.CATEGORY: "mixer",  # general name
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    mixer_2 = {
        YAML.ID: 2,
        YAML.CATEGORY: "mixer",  # general name
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    attenuator = {
        YAML.ID: 1,
        YAML.NAME: "mini_circuits",
        YAML.CATEGORY: "step_attenuator",
        "attenuation": 30,
        "ip": "192.168.0.222",
        "firmware": None,
    }

    schema = {
        YAML.ELEMENTS: [
            {
                YAML.ID: 0,
                YAML.CATEGORY: "bus",
                YAML.SUBCATEGORY: "control",
                "system_control": {
                    YAML.ID: 0,
                    YAML.CATEGORY: "system_control",
                    YAML.SUBCATEGORY: "mixer_based_system_control",
                    "awg": qblox_qcm_0,
                    "signal_generator": rohde_schwarz_0,
                    "mixer_up": mixer_0,
                },
                "target": qubit_0,
            },
            {
                YAML.ID: 0,
                YAML.CATEGORY: "bus",
                YAML.SUBCATEGORY: "readout",
                "system_control": {
                    YAML.ID: 1,
                    YAML.CATEGORY: "system_control",
                    YAML.SUBCATEGORY: "mixer_based_system_control",
                    "awg": qblox_qrm_0,
                    "signal_generator": rohde_schwarz_1,
                    "mixer_up": mixer_1,
                    "mixer_down": mixer_2,
                },
                "attenuator": attenuator,
                "target": resonator_0,
            },
        ],
    }

    runcard = {
        YAML.PLATFORM: platform,
        YAML.SCHEMA: schema,
    }


class FluxQubit:
    """Test data of the flux_qubit platform."""

    name = "flux_qubit"

    platform = {
        YAML.ID: 0,
        YAML.NAME: "flux_qubit",
        YAML.CATEGORY: "platform",
        YAML.SETTINGS: {
            "readout_duration": 2000,
            "readout_amplitude": 0.4,
            "readout_phase": 0,
            "delay_between_pulses": 0,
            "delay_before_readout": 40,
            "gate_duration": 100,
            "num_sigmas": 4,
            "drag_coefficient": 0,
        },
    }

    schema = {
        YAML.ELEMENTS: [
            {
                YAML.ID: 0,
                YAML.CATEGORY: "bus",
                YAML.SUBCATEGORY: "control",
                "system_control": {
                    YAML.ID: 0,
                    YAML.CATEGORY: "system_control",
                    YAML.SUBCATEGORY: "simulated_system_control",
                    "qubit": "csfq4jj",
                    "frequency": 2085540698,
                    "driving_hamiltonian": "zport",
                    "resolution": 0.01,
                    "nsteps": 100000000,
                    "store_states": False,
                    "dimension": 10,
                },
                "target": {
                    YAML.ID: 0,
                    YAML.NAME: "qubit",
                    YAML.CATEGORY: "qubit",
                    "pi_pulse_amplitude": 1,
                    "pi_pulse_duration": 100,
                    "pi_pulse_frequency": 100000000.0,
                    "qubit_frequency": 3544000000.0,
                    "min_voltage": 950,
                    "max_voltage": 1775,
                },
            }
        ]
    }

    runcard = {
        YAML.PLATFORM: platform,
        YAML.SCHEMA: schema,
    }


experiment_params: List[List[str | Circuit | List[Circuit]]] = []
for p_name in [DEFAULT_PLATFORM_NAME, "flux_qubit"]:
    circuit = Circuit(1)
    circuit.add(I(0))
    circuit.add(X(0))
    circuit.add(Y(0))
    circuit.add(RX(0, 23))
    circuit.add(RY(0, 15))
    circuit.add(U2(0, 14, 25))
    if p_name == DEFAULT_PLATFORM_NAME:
        circuit.add(M(0))
    experiment_params.extend([[p_name, circuit], [p_name, [circuit, circuit]]])


class MockedSettingsFactory:
    """Class that loads a specific class given an object's name."""

    handlers: Dict[str, type] = {"platform_0": Platform0, "flux_qubit": FluxQubit}

    @classmethod
    def register(cls, handler_cls: type):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name] = handler_cls  # type: ignore
        return handler_cls

    @classmethod
    def get(cls, platform_name: str, filename: str):
        """Return class attribute."""
        platform = cls.handlers[platform_name]
        return copy.deepcopy(getattr(platform, filename))
