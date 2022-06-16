""" Data to use alongside the test suite. """
import copy
from typing import Dict, List

from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, U2, I, M, X, Y

from qililab.constants import DEFAULT_PLATFORM_NAME


class Platform0:
    """Test data of the platform_0 platform."""

    name = "platform_0"

    platform = {
        "id_": 0,
        "name": "platform_0",
        "category": "platform",
        "translation_settings": {
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

    instruments = [
        {
            "id_": 0,
            "name": "qblox_qcm",
            "category": "awg",
            "ip": "192.168.0.3",
            "firmware": "0.7.0",
            "reference_clock": "internal",
            "sequencer": 0,
            "sync_enabled": True,
            "gain": 1,
            "frequency": 100000000,
        },
        {
            "id_": 1,
            "name": "qblox_qrm",
            "category": "awg",
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
        },
        {
            "id_": 0,
            "name": "rohde_schwarz",
            "category": "signal_generator",
            "ip": "192.168.0.10",
            "firmware": "4.30.046.295",
            "frequency": 3644000000.0,
            "power": 15,
        },
        {
            "id_": 1,
            "name": "rohde_schwarz",
            "category": "signal_generator",
            "ip": "192.168.0.7",
            "firmware": "4.30.046.295",
            "frequency": 7307720000.0,
            "power": 15,
        },
        {
            "id_": 1,
            "name": "mini_circuits",
            "category": "attenuator",
            "firmware": None,
            "attenuation": 30,
            "ip": "192.168.0.222",
        },
    ]

    schema = {
        "instruments": instruments,
        "buses": [
            {
                "id_": 0,
                "category": "bus",
                "subcategory": "control",
                "system_control": {
                    "id_": 0,
                    "category": "system_control",
                    "subcategory": "mixer_based_system_control",
                    "awg": {"id_": 0},
                    "signal_generator": {"id_": 0},
                },
                "port": 0,
            },
            {
                "id_": 0,
                "category": "bus",
                "subcategory": "readout",
                "system_control": {
                    "id_": 1,
                    "category": "system_control",
                    "subcategory": "mixer_based_system_control",
                    "awg": {"id_": 1},
                    "signal_generator": {"id_": 1},
                },
                "attenuator": {"id_": 0},
                "port": 1,
            },
        ],
    }

    runcard = {
        "settings": platform,
        "schema": schema,
    }


class FluxQubit:
    """Test data of the flux_qubit platform."""

    name = "flux_qubit"

    platform = {
        "id_": 0,
        "name": "flux_qubit",
        "category": "platform",
        "translation_settings": {
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
        "instruments": [],
        "buses": [
            {
                "id_": 0,
                "category": "bus",
                "subcategory": "control",
                "system_control": {
                    "id_": 0,
                    "category": "system_control",
                    "subcategory": "simulated_system_control",
                    "qubit": "csfq4jj",
                    "frequency": 2085540698,
                    "driving_hamiltonian": "zport",
                    "resolution": 0.01,
                    "nsteps": 100000000,
                    "store_states": False,
                    "dimension": 10,
                },
                "port": 0,
            }
        ],
    }

    runcard = {
        "settings": platform,
        "schema": schema,
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
