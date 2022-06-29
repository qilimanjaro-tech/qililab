""" Data to use alongside the test suite. """
import copy
from typing import Dict, List, Type

from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, U2, I, M, X, Y

from qililab.constants import PLATFORM, RUNCARD, SCHEMA


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    platform = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "galadriel",
        RUNCARD.CATEGORY: "platform",
        PLATFORM.TRANSLATION_SETTINGS: {
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
        RUNCARD.ID: 0,
        RUNCARD.NAME: "qblox_qcm",
        RUNCARD.CATEGORY: "awg",
        "ip": "192.168.0.3",
        "firmware": "0.7.0",
        "reference_clock": "internal",
        "sequencer": 0,
        "sync_enabled": True,
        "gain": 1,
        "frequency": 100000000,
        "num_bins": 100,
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    qblox_qrm_0 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: "qblox_qrm",
        RUNCARD.CATEGORY: "awg",
        "ip": "192.168.0.4",
        "firmware": "0.7.0",
        "reference_clock": "external",
        "sequencer": 0,
        "sync_enabled": True,
        "gain": 0.5,
        "acquire_trigger_mode": "sequencer",
        "hardware_averaging": True,
        "sampling_rate": 1000000000,
        "integration": True,
        "integration_length": 2000,
        "integration_mode": "ssb",
        "sequence_timeout": 1,
        "num_bins": 100,
        "acquisition_timeout": 1,
        "acquisition_delay_time": 100,
        "frequency": 20000000,
        "epsilon": 0,
        "delta": 0,
        "offset_i": 0,
        "offset_q": 0,
    }

    rohde_schwarz_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "rohde_schwarz",
        RUNCARD.CATEGORY: "signal_generator",
        "ip": "192.168.0.10",
        "firmware": "4.30.046.295",
        "power": 15,
    }

    rohde_schwarz_1 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: "rohde_schwarz",  # unique name
        RUNCARD.CATEGORY: "signal_generator",  # general name
        "ip": "192.168.0.7",
        "firmware": "4.30.046.295",
        "power": 15,
    }

    attenuator = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: "mini_circuits",
        RUNCARD.CATEGORY: "attenuator",
        "attenuation": 30,
        "ip": "192.168.0.222",
        "firmware": None,
    }

    keithley_2600 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: "keithley_2600",
        RUNCARD.CATEGORY: "dc_source",
        "ip": "192.168.1.112",
        "firmware": None,
        "max_current": 0.1,
        "max_voltage": 20.0,
    }

    instruments = [qblox_qcm_0, qblox_qrm_0, rohde_schwarz_0, rohde_schwarz_1, attenuator]

    chip = {
        "id_": 0,
        "category": "chip",
        "ports": [0, 1, 2, 3],  # ports used for control/readout
        "nodes": [
            {"name": "resonator", "port": 1, "frequency": 7.34730e09, "nodes": [1]},
            {"name": "qubit", "idx": 0, "port": 0, "frequency": 3.451e09, "nodes": [0]},
        ],
    }

    schema = {
        SCHEMA.INSTRUMENTS: instruments,
        SCHEMA.CHIP: chip,
        SCHEMA.BUSES: [
            {
                RUNCARD.ID: 0,
                RUNCARD.CATEGORY: "bus",
                RUNCARD.SUBCATEGORY: "control",
                "system_control": {
                    RUNCARD.ID: 0,
                    RUNCARD.CATEGORY: "system_control",
                    RUNCARD.SUBCATEGORY: "mixer_based_system_control",
                    "awg": qblox_qcm_0,
                    "signal_generator": rohde_schwarz_0,
                },
                "port": 0,
            },
            {
                RUNCARD.ID: 0,
                RUNCARD.CATEGORY: "bus",
                RUNCARD.SUBCATEGORY: "readout",
                "system_control": {
                    RUNCARD.ID: 1,
                    RUNCARD.CATEGORY: "system_control",
                    RUNCARD.SUBCATEGORY: "mixer_based_system_control",
                    "awg": qblox_qrm_0,
                    "signal_generator": rohde_schwarz_1,
                },
                "attenuator": attenuator,
                "port": 1,
            },
        ],
    }

    runcard = {
        RUNCARD.SETTINGS: platform,
        RUNCARD.SCHEMA: schema,
    }

    qubit_0: dict = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "qubit",
        RUNCARD.CATEGORY: "qubit",
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    resonator_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "resonator",
        RUNCARD.CATEGORY: "resonator",
        "qubits": [
            {
                RUNCARD.ID: 0,
                RUNCARD.CATEGORY: "qubit",
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
        RUNCARD.ID: 0,
        RUNCARD.NAME: "flux_qubit",
        RUNCARD.CATEGORY: "platform",
        PLATFORM.TRANSLATION_SETTINGS: {
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

    chip = {
        "id_": 0,
        "category": "chip",
        "ports": [0, 1],  # ports used for control/readout
        "nodes": [
            {"name": "qubit", "idx": 0, "port": 0, "frequency": 3.451e09, "nodes": [0]},
        ],
    }

    schema = {
        SCHEMA.INSTRUMENTS: [],
        SCHEMA.CHIP: chip,
        SCHEMA.BUSES: [
            {
                RUNCARD.ID: 0,
                RUNCARD.CATEGORY: "bus",
                RUNCARD.SUBCATEGORY: "control",
                "system_control": {
                    RUNCARD.ID: 0,
                    RUNCARD.CATEGORY: "system_control",
                    RUNCARD.SUBCATEGORY: "simulated_system_control",
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
        RUNCARD.SETTINGS: platform,
        RUNCARD.SCHEMA: schema,
    }


experiment_params: List[List[str | Circuit | List[Circuit]]] = []
for platform in (Galadriel, FluxQubit):
    circuit = Circuit(1)
    circuit.add(I(0))
    circuit.add(X(0))
    circuit.add(Y(0))
    circuit.add(RX(0, 23))
    circuit.add(RY(0, 15))
    circuit.add(U2(0, 14, 25))
    if platform == Galadriel:
        circuit.add(M(0))
    experiment_params.extend([[platform.runcard, circuit], [platform.runcard, [circuit, circuit]]])  # type: ignore


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
            "bins": {
                "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                "threshold": [0.48046875],
                "avg_cnt": [1024],
            },
        },
        {
            "name": "qblox",
            "bins": {
                "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
                "threshold": [0.4599609375],
                "avg_cnt": [1024],
            },
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
            "bins": {
                "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                "threshold": [0.48046875],
                "avg_cnt": [1024],
            },
        },
        {
            "name": "qblox",
            "bins": {
                "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
                "threshold": [0.4599609375],
                "avg_cnt": [1024],
            },
        },
    ],
}

experiment = {
    "platform": Galadriel.runcard,
    "settings": {"hardware_average": 1024, "software_average": 1, "repetition_duration": 200000},
    "sequences": [
        {
            "pulses": [
                {
                    "name": "ReadoutPulse",
                    "amplitude": 1,
                    "frequency": 1e9,
                    "phase": 0,
                    "duration": 2000,
                    "port": 1,
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

    handlers: Dict[str, Type[Galadriel] | Type[FluxQubit]] = {"galadriel": Galadriel, "flux_qubit": FluxQubit}

    @classmethod
    def register(cls, handler_cls: Type[Galadriel] | Type[FluxQubit]):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name] = handler_cls  # type: ignore
        return handler_cls

    @classmethod
    def get(cls, platform_name: str):
        """Return class attribute."""
        platform = cls.handlers[platform_name]
        return copy.deepcopy(platform.runcard)
