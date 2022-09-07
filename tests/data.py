""" Data to use alongside the test suite. """
import copy
from typing import Dict, List, Type

from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, U2, I, M, X, Y

from qililab.constants import (
    CONNECTION,
    INSTRUMENTCONTROLLER,
    INSTRUMENTREFERENCE,
    PLATFORM,
    RUNCARD,
    SCHEMA,
)
from qililab.typings.enums import (
    Category,
    ConnectionName,
    InstrumentControllerName,
    InstrumentControllerSubCategory,
    InstrumentName,
    Parameter,
    ReferenceClock,
)


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    platform = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "galadriel",
        RUNCARD.CATEGORY: "platform",
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.MASTER_AMPLITUDE_GATE: 1,
        PLATFORM.MASTER_DURATION_GATE: 100,
        PLATFORM.MASTER_DRAG_COEFFICIENT: 0,
        "gates": [
            {
                "name": "M",
                "amplitude": PLATFORM.MASTER_AMPLITUDE_GATE,
                "phase": 0,
                "duration": 2000,
                "shape": {"name": "rectangular"},
            },
            {
                "name": "I",
                "amplitude": 0,
                "phase": 0,
                "duration": 0,
                "shape": {"name": "rectangular"},
            },
            {
                "name": "X",
                "amplitude": PLATFORM.MASTER_AMPLITUDE_GATE,
                "phase": 0,
                "duration": PLATFORM.MASTER_DURATION_GATE,
                "shape": {
                    "name": "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": PLATFORM.MASTER_DRAG_COEFFICIENT,
                },
            },
            {
                "name": "Y",
                "amplitude": PLATFORM.MASTER_AMPLITUDE_GATE,
                "phase": 1.5707963267948966,
                "duration": PLATFORM.MASTER_DURATION_GATE,
                "shape": {
                    "name": "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": PLATFORM.MASTER_DRAG_COEFFICIENT,
                },
            },
        ],
    }

    pulsar_controller_qcm_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentControllerName.QBLOX_PULSAR.value,
        RUNCARD.ALIAS: "pulsar_controller_qcm_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        Parameter.REFERENCE_CLOCK.value: ReferenceClock.INTERNAL.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.3",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.AWG.value: InstrumentName.QBLOX_QCM.value,
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    qblox_qcm_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentName.QBLOX_QCM.value,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QCM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        "firmware": "0.7.0",
        "sync_enabled": True,
        "frequency": 100000000,
        "num_bins": 100,
        "num_sequencers": 1,
        "gain": [1],
        "epsilon": [0],
        "delta": [0],
        "offset_i": [0],
        "offset_q": [0],
    }

    pulsar_controller_qrm_0 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentControllerName.QBLOX_PULSAR.value,
        RUNCARD.ALIAS: "pulsar_controller_qrm_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        Parameter.REFERENCE_CLOCK.value: ReferenceClock.EXTERNAL.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.4",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.AWG.value: InstrumentName.QBLOX_QRM.value,
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    qblox_qrm_0 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentName.QBLOX_QRM.value,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QRM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        "firmware": "0.7.0",
        "sync_enabled": True,
        "scope_acquire_trigger_mode": "sequencer",
        "scope_hardware_averaging": True,
        "sampling_rate": 1000000000,
        "integration": True,
        "integration_length": 2000,
        "integration_mode": "ssb",
        "sequence_timeout": 1,
        "num_bins": 100,
        "acquisition_timeout": 1,
        "acquisition_delay_time": 100,
        "frequency": 20000000,
        "num_sequencers": 2,
        "gain": [0.5, 0.5],
        "epsilon": [0, 0],
        "delta": [0, 0],
        "offset_i": [0, 0],
        "offset_q": [0, 0],
    }

    rohde_schwarz_controller_0 = {
        RUNCARD.ID: 2,
        RUNCARD.NAME: InstrumentControllerName.ROHDE_SCHWARZ.value,
        RUNCARD.ALIAS: "rohde_schwarz_controller_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.10",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.SIGNAL_GENERATOR.value: "rs_0",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    rohde_schwarz_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentName.ROHDE_SCHWARZ.value,
        RUNCARD.ALIAS: "rs_0",
        RUNCARD.CATEGORY: Category.SIGNAL_GENERATOR.value,
        "firmware": "4.30.046.295",
        "power": 15,
    }

    rohde_schwarz_controller_1 = {
        RUNCARD.ID: 3,
        RUNCARD.NAME: InstrumentControllerName.ROHDE_SCHWARZ.value,
        RUNCARD.ALIAS: "rohde_schwarz_controller_1",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.7",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.SIGNAL_GENERATOR.value: "rs_1",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    rohde_schwarz_1 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentName.ROHDE_SCHWARZ.value,
        RUNCARD.ALIAS: "rs_1",
        RUNCARD.CATEGORY: Category.SIGNAL_GENERATOR.value,
        "firmware": "4.30.046.295",
        "power": 15,
    }

    attenuator_controller_0 = {
        RUNCARD.ID: 4,
        RUNCARD.NAME: InstrumentControllerName.MINI_CIRCUITS.value,
        RUNCARD.ALIAS: "attenuator_controller_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.222",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.ATTENUATOR.value: "attenuator",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    attenuator = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentName.MINI_CIRCUITS.value,
        RUNCARD.ALIAS: "attenuator",
        RUNCARD.CATEGORY: Category.ATTENUATOR.value,
        "attenuation": 30,
        "firmware": None,
    }

    keithley_2600_controller_0 = {
        RUNCARD.ID: 5,
        RUNCARD.NAME: InstrumentControllerName.KEITHLEY2600.value,
        RUNCARD.ALIAS: "keithley_2600_controller_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.112",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.DC_SOURCE.value: "keithley_2600",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    keithley_2600 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentName.KEITHLEY2600.value,
        RUNCARD.ALIAS: "keithley_2600",
        RUNCARD.CATEGORY: Category.DC_SOURCE.value,
        "firmware": None,
        "max_current": 0.1,
        "max_voltage": 20.0,
    }

    instruments = [qblox_qcm_0, qblox_qrm_0, rohde_schwarz_0, rohde_schwarz_1, attenuator, keithley_2600]
    instrument_controllers = [
        pulsar_controller_qcm_0,
        pulsar_controller_qrm_0,
        rohde_schwarz_controller_0,
        rohde_schwarz_controller_1,
        attenuator_controller_0,
        keithley_2600_controller_0,
    ]

    chip = {
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "id_": 0, "nodes": [3]},
            {"name": "port", "id_": 1, "nodes": [2]},
            {"name": "resonator", "id_": 2, "alias": "resonator", "frequency": 7.34730e09, "nodes": [1, 3]},
            {"name": "qubit", "id_": 3, "alias": "qubit", "qubit_idx": 0, "frequency": 3.451e09, "nodes": [0, 2]},
        ],
    }

    buses = [
        {
            RUNCARD.ID: 0,
            RUNCARD.CATEGORY: "bus",
            RUNCARD.SUBCATEGORY: "control",
            "system_control": {
                RUNCARD.ID: 0,
                RUNCARD.CATEGORY: "system_control",
                RUNCARD.SUBCATEGORY: "mixer_based_system_control",
                Category.AWG.value: InstrumentName.QBLOX_QCM.value,
                Category.SIGNAL_GENERATOR.value: "rs_0",
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
                Category.AWG.value: InstrumentName.QBLOX_QRM.value,
                Category.SIGNAL_GENERATOR.value: "rs_1",
            },
            "attenuator": "attenuator",
            "port": 1,
        },
    ]

    schema = {
        SCHEMA.INSTRUMENTS: instruments,
        SCHEMA.CHIP: chip,
        SCHEMA.BUSES: buses,
        SCHEMA.INSTRUMENT_CONTROLLERS: instrument_controllers,
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


class FluxQubitSimulator:
    """Test data of the flux_qubit platform."""

    name = "flux_qubit"

    platform = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "flux_qubit",
        RUNCARD.CATEGORY: "platform",
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.MASTER_AMPLITUDE_GATE: 1,
        PLATFORM.MASTER_DURATION_GATE: 100,
        PLATFORM.MASTER_DRAG_COEFFICIENT: 0,
        "gates": [
            {
                "name": "M",
                "amplitude": 1,
                "phase": 0,
                "duration": 2000,
                "shape": {
                    "name": "rectangular",
                },
            },
            {
                "name": "I",
                "amplitude": 0,
                "phase": 0,
                "duration": 0,
                "shape": {
                    "name": "rectangular",
                },
            },
            {
                "name": "X",
                "amplitude": 1,
                "phase": 0,
                "duration": 100,
                "shape": {
                    "name": "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": PLATFORM.MASTER_DRAG_COEFFICIENT,
                },
            },
            {
                "name": "Y",
                "amplitude": 1,
                "phase": 1.5707963267948966,
                "duration": 100,
                "shape": {
                    "name": "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": PLATFORM.MASTER_DRAG_COEFFICIENT,
                },
            },
        ],
    }

    chip = {
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "id_": 0, "nodes": [1]},
            {"name": "qubit", "id_": 1, "qubit_idx": 0, "frequency": 3.451e09, "nodes": [0]},
        ],
    }

    chip = {
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "id_": 0, "nodes": [1]},
            {"name": "qubit", "id_": 1, "qubit_idx": 0, "frequency": 3.451e09, "nodes": [0]},
        ],
    }

    schema = {
        SCHEMA.INSTRUMENTS: [],
        SCHEMA.INSTRUMENT_CONTROLLERS: [],
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
for platform in (Galadriel, FluxQubitSimulator):
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
    "loops": [
        {
            "alias": "attenuator",
            "instrument": None,
            "id_": None,
            "parameter": "attenuation",
            "start": 15,
            "stop": 90,
            "num": None,
            "step": 1,
            "loop": {
                "alias": "rs_1",
                "instrument": None,
                "id_": None,
                "parameter": "frequency",
                "start": 7342000000,
                "stop": 7352000000,
                "num": None,
                "step": 100000,
                "loop": None,
            },
        }
    ],
    "results": [
        {
            "name": "qblox",
            "pulse_length": 8000,
            "bins": [
                {
                    "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                    "threshold": [0.48046875],
                    "avg_cnt": [1024],
                }
            ],
        },
        {
            "name": "qblox",
            "pulse_length": 8000,
            "bins": [
                {
                    "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
                    "threshold": [0.4599609375],
                    "avg_cnt": [1024],
                }
            ],
        },
    ],
}

results_one_loops = {
    "software_average": 1,
    "num_sequences": 1,
    "shape": [100],
    "loops": [
        {
            "alias": "rs_1",
            "instrument": None,
            "id_": None,
            "parameter": "frequency",
            "start": 7342000000,
            "stop": 7352000000,
            "num": None,
            "step": 100000,
            "loop": None,
        }
    ],
    "results": [
        {
            "name": "qblox",
            "pulse_length": 8000,
            "bins": [
                {
                    "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                    "threshold": [0.48046875],
                    "avg_cnt": [1024],
                }
            ],
        },
        {
            "name": "qblox",
            "pulse_length": 8000,
            "bins": [
                {
                    "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
                    "threshold": [0.4599609375],
                    "avg_cnt": [1024],
                }
            ],
        },
    ],
}

experiment = {
    "platform": Galadriel.runcard,
    "settings": {
        "hardware_average": 1024,
        "software_average": 1,
        "repetition_duration": 200000,
    },
    "sequences": [
        {
            "elements": [
                {
                    "pulses": [
                        {
                            "name": "readout_pulse",
                            "amplitude": 1,
                            "frequency": 1e9,
                            "phase": 0,
                            "duration": 2000,
                            "pulse_shape": {"name": "rectangular"},
                            "start_time": 40,
                        }
                    ],
                    "port": 1,
                }
            ],
            "time": {"[0]": 2040},
            "delay_between_pulses": 0,
            "delay_before_readout": 40,
        }
    ],
    "loops": [
        {
            "alias": "qblox_qrm",
            "parameter": "gain",
            "start": 0.1,
            "stop": 1,
            "num": None,
            "step": 0.3,
            "loop": {
                "alias": "attenuator",
                "parameter": "attenuation",
                "start": 15,
                "stop": 90,
                "num": None,
                "step": 1,
                "loop": {
                    "alias": "rs_1",
                    "parameter": "frequency",
                    "start": 7342000000,
                    "stop": 7352000000,
                    "num": None,
                    "step": 100000,
                    "loop": None,
                },
            },
        }
    ],
    "name": "punchout",
}


class MockedSettingsFactory:
    """Class that loads a specific class given an object's name."""

    handlers: Dict[str, Type[Galadriel] | Type[FluxQubitSimulator]] = {
        "galadriel": Galadriel,
        "flux_qubit": FluxQubitSimulator,
    }

    @classmethod
    def register(cls, handler_cls: Type[Galadriel] | Type[FluxQubitSimulator]):
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
