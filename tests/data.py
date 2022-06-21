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

    qblox_qcm_0 = {
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
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    qblox_qrm_0 = {
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
        "sampling_rate": 1000000000,
        "integration_length": 2000,
        "integration_mode": "ssb",
        "sequence_timeout": 1,
        "acquisition_timeout": 1,
        "acquisition_name": "single",
        "delay_time": 100,
        "frequency": 20000000,
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    rohde_schwarz_0 = {
        "id_": 0,
        "name": "rohde_schwarz",
        "category": "signal_generator",
        "ip": "192.168.0.10",
        "firmware": "4.30.046.295",
        "frequency": 3644000000.0,
        "power": 15,
    }

    rohde_schwarz_1 = {
        "id_": 1,
        "name": "rohde_schwarz",
        "category": "signal_generator",
        "ip": "192.168.0.7",
        "firmware": "4.30.046.295",
        "frequency": 7307720000.0,
        "power": 15,
    }

    attenuator = {
        "id_": 0,
        "name": "mini_circuits",
        "category": "attenuator",
        "firmware": None,
        "attenuation": 30,
        "ip": "192.168.0.222",
    }

    keithley_2600 = {
        "id_": 0,
        "name": "keithley_2600",
        "category": "dc_source",
        "firmware": None,
        "ip": "192.168.1.111",
    }

    instruments = [
        qblox_qcm_0,
        qblox_qrm_0,
        rohde_schwarz_0,
        rohde_schwarz_1,
        attenuator,
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
                    "awg": {"id_": 0, "category": "awg"},
                    "signal_generator": {"id_": 0, "category": "signal_generator"},
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
                    "awg": {"id_": 1, "category": "awg"},
                    "signal_generator": {"id_": 1, "category": "signal_generator"},
                },
                "attenuator": {"id_": 0, "category": "attenuator"},
                "port": 1,
            },
        ],
    }

    runcard = {
        "settings": platform,
        "schema": schema,
    }

    qubit_0 = {
        "id_": 0,
        "name": "qubit",
        "category": "qubit",
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    qubit_1 = {
        "id_": 1,
        "name": "qubit",
        "category": "qubit",
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    resonator_0 = {
        "id_": 0,
        "name": "resonator",
        "category": "resonator",
        "qubits": [
            {
                "id_": 0,
                "category": "qubit",
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
        "id_": 1,
        "name": "resonator",
        "category": "resonator",
        "qubits": [
            {
                "id_": 1,
                "category": "qubit",
                "pi_pulse_amplitude": 1,
                "pi_pulse_duration": 100,
                "pi_pulse_frequency": 100000000.0,
                "qubit_frequency": 3544000000.0,
                "min_voltage": 950,
                "max_voltage": 1775,
            }
        ],
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


results_two_loops = {
    "software_average": 1,
    "num_sequences": 1,
    "shape": [75, 100],
    "loop": {
        "instrument": "attenuator",
        "id_": 1,
        "parameter": "attenuation",
        "start": 15,
        "stop": 90,
        "num": None,
        "step": 1,
        "loop": {
            "instrument": "signal_generator",
            "id_": 1,
            "parameter": "frequency",
            "start": 7342000000,
            "stop": 7352000000,
            "num": None,
            "step": 100000,
            "loop": None,
        },
    },
    "results": [
        {
            "name": "qblox",
            "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
            "threshold": [0.48046875],
            "avg_cnt": [1024],
        },
        {
            "name": "qblox",
            "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
            "threshold": [0.4599609375],
            "avg_cnt": [1024],
        },
    ],
}

results_one_loops = {
    "software_average": 1,
    "num_sequences": 1,
    "shape": [100],
    "loop": {
        "instrument": "signal_generator",
        "id_": 1,
        "parameter": "frequency",
        "start": 7342000000,
        "stop": 7352000000,
        "num": None,
        "step": 100000,
        "loop": None,
    },
    "results": [
        {
            "name": "qblox",
            "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
            "threshold": [0.48046875],
            "avg_cnt": [1024],
        },
        {
            "name": "qblox",
            "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
            "threshold": [0.4599609375],
            "avg_cnt": [1024],
        },
    ],
}

experiment = {
    "platform": Platform0.runcard,
    "settings": {"hardware_average": 1024, "software_average": 1, "repetition_duration": 200000},
    "sequences": [
        {
            "pulses": [
                {
                    "name": "ReadoutPulse",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 2000,
                    "qubit_ids": [0],
                    "pulse_shape": {"name": "rectangular"},
                    "start_time": 40,
                }
            ],
            "time": {"[0]": 2040},
            "delay_between_pulses": 0,
            "delay_before_readout": 40,
        }
    ],
    "loop": {
        "instrument": "awg",
        "id_": 1,
        "parameter": "gain",
        "start": 0.1,
        "stop": 1,
        "num": None,
        "step": 0.3,
        "loop": {
            "instrument": "attenuator",
            "id_": 1,
            "parameter": "attenuation",
            "start": 15,
            "stop": 90,
            "num": None,
            "step": 1,
            "loop": {
                "instrument": "signal_generator",
                "id_": 1,
                "parameter": "frequency",
                "start": 7342000000,
                "stop": 7352000000,
                "num": None,
                "step": 100000,
                "loop": None,
            },
        },
    },
    "name": "punchout",
}


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
