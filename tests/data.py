""" Data to use alongside the test suite. """
import copy
from typing import Dict, List, Type

from qibo.gates import RX, RY, I, M, X, Y
from qibo.models.circuit import Circuit

from qililab.constants import (
    CONNECTION,
    EXPERIMENT,
    INSTRUMENTCONTROLLER,
    INSTRUMENTREFERENCE,
    LOOP,
    PLATFORM,
    PULSE,
    PULSEBUSSCHEDULE,
    PULSEEVENT,
    PULSESCHEDULES,
    RUNCARD,
    SCHEMA,
)
from qililab.instruments.awg_settings.typings import (
    AWGChannelMappingTypes,
    AWGIQChannelTypes,
    AWGSequencerPathTypes,
    AWGSequencerTypes,
    AWGTypes,
)
from qililab.typings.enums import (
    AcquireTriggerMode,
    BusCategory,
    BusName,
    BusSubCategory,
    Category,
    ConnectionName,
    InstrumentControllerName,
    InstrumentControllerSubCategory,
    InstrumentName,
    IntegrationMode,
    Node,
    NodeName,
    Parameter,
    PulseName,
    PulseShapeName,
    ReferenceClock,
    SystemControlCategory,
    SystemControlName,
    SystemControlSubCategory,
)


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    platform = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "galadriel",
        RUNCARD.CATEGORY: RUNCARD.PLATFORM,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.MASTER_AMPLITUDE_GATE: 1,
        PLATFORM.MASTER_DURATION_GATE: 100,
        "gates": [
            {
                RUNCARD.NAME: "M",
                "amplitude": PLATFORM.MASTER_AMPLITUDE_GATE,
                "phase": 0,
                "duration": 2000,
                EXPERIMENT.SHAPE: {RUNCARD.NAME: "rectangular"},
            },
            {
                RUNCARD.NAME: "I",
                "amplitude": 0,
                "phase": 0,
                "duration": 0,
                EXPERIMENT.SHAPE: {RUNCARD.NAME: "rectangular"},
            },
            {
                RUNCARD.NAME: "X",
                "amplitude": PLATFORM.MASTER_AMPLITUDE_GATE,
                "phase": 0,
                "duration": PLATFORM.MASTER_DURATION_GATE,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": 0,
                },
            },
            {
                RUNCARD.NAME: "Y",
                "amplitude": PLATFORM.MASTER_AMPLITUDE_GATE,
                "phase": 1.5707963267948966,
                "duration": PLATFORM.MASTER_DURATION_GATE,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": 0,
                },
            },
        ],
    }

    pulsar_controller_qcm_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentControllerName.QBLOX_PULSAR,
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
        RUNCARD.NAME: InstrumentName.QBLOX_QCM,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QCM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 0,
                AWGSequencerTypes.PATH0.value: {
                    AWGSequencerPathTypes.OUTPUT_CHANNEL.value: 0,
                },
                AWGSequencerTypes.PATH1.value: {
                    AWGSequencerPathTypes.OUTPUT_CHANNEL.value: 1,
                },
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_PATH0.value: 1,
                Parameter.GAIN_PATH1.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_PATH0.value: 0,
                Parameter.OFFSET_PATH1.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SYNC_ENABLED.value: True,
            }
        ],
        AWGTypes.AWG_IQ_CHANNELS.value: [
            {
                AWGIQChannelTypes.IDENTIFIER.value: 0,
                AWGIQChannelTypes.I_CHANNEL.value: {
                    AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: 0,
                    AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: 0,
                },
                AWGIQChannelTypes.Q_CHANNEL.value: {
                    AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: 0,
                    AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: 1,
                },
            },
        ],
    }

    pulsar_controller_qrm_0 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentControllerName.QBLOX_PULSAR,
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
        RUNCARD.NAME: InstrumentName.QBLOX_QRM,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QRM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        Parameter.ACQUISITION_DELAY_TIME.value: 100,
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 1,
                AWGSequencerTypes.PATH0.value: {
                    AWGSequencerPathTypes.OUTPUT_CHANNEL.value: 0,
                },
                AWGSequencerTypes.PATH1.value: {
                    AWGSequencerPathTypes.OUTPUT_CHANNEL.value: 1,
                },
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_PATH0.value: 1,
                Parameter.GAIN_PATH1.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_PATH0.value: 0,
                Parameter.OFFSET_PATH1.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SYNC_ENABLED.value: True,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_000,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: False,
            }
        ],
        AWGTypes.AWG_IQ_CHANNELS.value: [
            {
                AWGIQChannelTypes.IDENTIFIER.value: 0,
                AWGIQChannelTypes.I_CHANNEL.value: {
                    AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: 0,
                    AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: 0,
                },
                AWGIQChannelTypes.Q_CHANNEL.value: {
                    AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: 0,
                    AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: 1,
                },
            },
        ],
    }

    rohde_schwarz_controller_0 = {
        RUNCARD.ID: 2,
        RUNCARD.NAME: InstrumentControllerName.ROHDE_SCHWARZ,
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
        RUNCARD.NAME: InstrumentName.ROHDE_SCHWARZ,
        RUNCARD.ALIAS: "rs_0",
        RUNCARD.CATEGORY: Category.SIGNAL_GENERATOR.value,
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
    }

    rohde_schwarz_controller_1 = {
        RUNCARD.ID: 3,
        RUNCARD.NAME: InstrumentControllerName.ROHDE_SCHWARZ,
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
        RUNCARD.NAME: InstrumentName.ROHDE_SCHWARZ,
        RUNCARD.ALIAS: "rs_1",
        RUNCARD.CATEGORY: Category.SIGNAL_GENERATOR.value,
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 3.351e09,
    }

    attenuator_controller_0 = {
        RUNCARD.ID: 4,
        RUNCARD.NAME: InstrumentControllerName.MINI_CIRCUITS,
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
        RUNCARD.NAME: InstrumentName.MINI_CIRCUITS,
        RUNCARD.ALIAS: "attenuator",
        RUNCARD.CATEGORY: Category.ATTENUATOR.value,
        Parameter.ATTENUATION.value: 30,
        RUNCARD.FIRMWARE: None,
    }

    keithley_2600_controller_0 = {
        RUNCARD.ID: 5,
        RUNCARD.NAME: InstrumentControllerName.KEITHLEY2600,
        RUNCARD.ALIAS: "keithley_2600_controller_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.112",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.DC_SOURCE.value: InstrumentName.KEITHLEY2600.value,
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    keithley_2600 = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentName.KEITHLEY2600,
        RUNCARD.ALIAS: InstrumentControllerName.KEITHLEY2600.value,
        RUNCARD.CATEGORY: Category.DC_SOURCE.value,
        RUNCARD.FIRMWARE: None,
        Parameter.MAX_CURRENT.value: 0.1,
        Parameter.MAX_VOLTAGE.value: 20.0,
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
        RUNCARD.ID: 0,
        RUNCARD.CATEGORY: Category.CHIP.value,
        Node.NODES.value: [
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 0, Node.NODES.value: [3]},
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 1, Node.NODES.value: [2]},
            {
                RUNCARD.NAME: NodeName.RESONATOR.value,
                RUNCARD.ID: 2,
                RUNCARD.ALIAS: NodeName.PORT.value,
                Node.FREQUENCY.value: 7.34730e09,
                Node.NODES.value: [1, 3],
            },
            {
                RUNCARD.NAME: NodeName.QUBIT.value,
                RUNCARD.ID: 3,
                RUNCARD.ALIAS: NodeName.QUBIT.value,
                Node.QUBIT_INDEX.value: 0,
                Node.FREQUENCY.value: 3.451e09,
                Node.NODES.value: [0, 2],
            },
        ],
    }

    buses = [
        {
            RUNCARD.ID: 0,
            RUNCARD.NAME: BusName.TIME_DOMAIN_CONTROL_BUS,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.BUS_CATEGORY: BusCategory.TIME_DOMAIN.value,
            RUNCARD.BUS_SUBCATEGORY: BusSubCategory.CONTROL.value,
            RUNCARD.ALIAS: "drive_line_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 0,
                RUNCARD.NAME: SystemControlName.TIME_DOMAIN_CONTROL_SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.SYSTEM_CONTROL_CATEGORY: SystemControlCategory.TIME_DOMAIN.value,
                RUNCARD.SYSTEM_CONTROL_SUBCATEGORY: SystemControlSubCategory.CONTROL.value,
                Category.AWG.value: InstrumentName.QBLOX_QCM.value,
                Category.SIGNAL_GENERATOR.value: "rs_0",
            },
            NodeName.PORT.value: 0,
        },
        {
            RUNCARD.ID: 1,
            RUNCARD.NAME: BusName.TIME_DOMAIN_READOUT_BUS,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.BUS_CATEGORY: BusCategory.TIME_DOMAIN.value,
            RUNCARD.BUS_SUBCATEGORY: BusSubCategory.TIME_DOMAIN_READOUT.value,
            RUNCARD.ALIAS: "feedline_input_output_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 1,
                RUNCARD.NAME: SystemControlName.TIME_DOMAIN_READOUT_SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.SYSTEM_CONTROL_CATEGORY: SystemControlCategory.TIME_DOMAIN.value,
                RUNCARD.SYSTEM_CONTROL_SUBCATEGORY: SystemControlSubCategory.TIME_DOMAIN_READOUT.value,
                Category.AWG.value: InstrumentName.QBLOX_QRM.value,
                Category.SIGNAL_GENERATOR.value: "rs_1",
            },
            NodeName.PORT.value: 1,
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
        RUNCARD.NAME: NodeName.QUBIT,
        RUNCARD.CATEGORY: NodeName.QUBIT.value,
        RUNCARD.ALIAS: NodeName.QUBIT.value,
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    resonator_0 = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: NodeName.PORT,
        RUNCARD.CATEGORY: NodeName.PORT.value,
        "qubits": [
            {
                RUNCARD.ID: 0,
                RUNCARD.CATEGORY: NodeName.QUBIT.value,
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
        RUNCARD.CATEGORY: RUNCARD.PLATFORM,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.MASTER_AMPLITUDE_GATE: 1,
        PLATFORM.MASTER_DURATION_GATE: 10,
        "gates": [
            {
                RUNCARD.NAME: "M",
                "amplitude": 1,
                "phase": 0,
                "duration": 2000,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: "rectangular",
                },
            },
            {
                RUNCARD.NAME: "I",
                "amplitude": 0,
                "phase": 0,
                "duration": 0,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: "rectangular",
                },
            },
            {
                RUNCARD.NAME: "X",
                "amplitude": 1,
                "phase": 0,
                "duration": 10,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": 0,
                },
            },
            {
                RUNCARD.NAME: "Y",
                "amplitude": 1,
                "phase": 1.5707963267948966,
                "duration": 10,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: "drag",
                    "num_sigmas": 4,
                    "drag_coefficient": 0,
                },
            },
        ],
    }

    chip = {
        RUNCARD.ID: 0,
        RUNCARD.CATEGORY: Category.CHIP.value,
        Node.NODES.value: [
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 0, Node.NODES.value: [1]},
            {
                RUNCARD.NAME: NodeName.QUBIT.value,
                RUNCARD.ID: 1,
                Node.QUBIT_INDEX.value: 0,
                Node.FREQUENCY.value: 3.451e09,
                Node.NODES.value: [0],
            },
        ],
    }

    schema = {
        SCHEMA.INSTRUMENTS: [],
        SCHEMA.INSTRUMENT_CONTROLLERS: [],
        SCHEMA.CHIP: chip,
        SCHEMA.BUSES: [
            {
                RUNCARD.ID: 0,
                RUNCARD.NAME: BusName.SIMULATED_BUS,
                RUNCARD.CATEGORY: Category.BUS.value,
                RUNCARD.BUS_CATEGORY: BusCategory.SIMULATED.value,
                RUNCARD.BUS_SUBCATEGORY: BusCategory.SIMULATED.value,
                RUNCARD.ALIAS: "simulated_bus",
                Category.SYSTEM_CONTROL.value: {
                    RUNCARD.ID: 0,
                    RUNCARD.NAME: SystemControlName.SIMULATED_SYSTEM_CONTROL,
                    RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                    RUNCARD.SYSTEM_CONTROL_CATEGORY: SystemControlCategory.SIMULATED.value,
                    RUNCARD.SYSTEM_CONTROL_SUBCATEGORY: SystemControlSubCategory.SIMULATED.value,
                    RUNCARD.ALIAS: "simulated_system_control",
                    NodeName.QUBIT.value: "csfq4jj",
                    "qubit_params": {"n_cut": 10, "phi_x": 6.28318530718, "phi_z": -0.25132741228},
                    "drive": "zport",
                    "drive_params": {"dimension": 10},
                    "resolution": 1,
                    "store_states": False,
                },
                NodeName.PORT.value: 0,
            }
        ],
    }

    runcard = {
        RUNCARD.SETTINGS: platform,
        RUNCARD.SCHEMA: schema,
    }


experiment_params: List[List[str | Circuit | List[Circuit]]] = []
for platform in [Galadriel]:
    circuit = Circuit(1)
    circuit.add(I(0))
    circuit.add(X(0))
    circuit.add(Y(0))
    circuit.add(RX(0, 23))
    circuit.add(RY(0, 15))
    if platform == Galadriel:
        circuit.add(M(0))
    experiment_params.extend([[platform.runcard, circuit], [platform.runcard, [circuit, circuit]]])  # type: ignore

# Circuit used for simulator
simulated_experiment_circuit: Circuit = Circuit(1)
simulated_experiment_circuit.add(I(0))
simulated_experiment_circuit.add(X(0))
simulated_experiment_circuit.add(Y(0))
simulated_experiment_circuit.add(RX(0, 23))
simulated_experiment_circuit.add(RY(0, 15))

results_two_loops = {
    EXPERIMENT.SOFTWARE_AVERAGE: 1,
    EXPERIMENT.NUM_SCHEDULES: 1,
    EXPERIMENT.SHAPE: [75, 100],
    EXPERIMENT.LOOPS: [
        {
            RUNCARD.ALIAS: "attenuator",
            LOOP.PARAMETER: Parameter.ATTENUATION.value,
            LOOP.OPTIONS: {
                LOOP.START: 15,
                LOOP.STOP: 90,
                LOOP.NUM: None,
                LOOP.STEP: 1,
                LOOP.LOGARITHMIC: False,
                LOOP.CHANNEL_ID: None,
                LOOP.VALUES: None,
            },
            LOOP.LOOP: {
                RUNCARD.ALIAS: "rs_1",
                LOOP.PARAMETER: Node.FREQUENCY.value,
                LOOP.OPTIONS: {
                    LOOP.START: 7342000000,
                    LOOP.STOP: 7352000000,
                    LOOP.NUM: None,
                    LOOP.STEP: 100000,
                    LOOP.LOGARITHMIC: False,
                    LOOP.CHANNEL_ID: None,
                    LOOP.VALUES: None,
                },
                LOOP.LOOP: None,
            },
        },
    ],
    EXPERIMENT.RESULTS: [
        {
            RUNCARD.NAME: "qblox",
            "pulse_length": 8000,
            "qblox_raw_results": [
                {
                    "scope": {
                        "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                        "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
                    },
                    "bins": {
                        "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                        "threshold": [0.48046875],
                        "avg_cnt": [1024],
                    },
                }
            ],
        },
        {
            RUNCARD.NAME: "qblox",
            "pulse_length": 8000,
            "qblox_raw_results": [
                {
                    "scope": {
                        "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                        "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
                    },
                    "bins": {
                        "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
                        "threshold": [0.4599609375],
                        "avg_cnt": [1024],
                    },
                }
            ],
        },
    ],
}

results_one_loops = {
    EXPERIMENT.SOFTWARE_AVERAGE: 1,
    EXPERIMENT.NUM_SCHEDULES: 1,
    EXPERIMENT.SHAPE: [100],
    EXPERIMENT.LOOPS: [
        {
            RUNCARD.ALIAS: "rs_1",
            LOOP.PARAMETER: Node.FREQUENCY.value,
            LOOP.OPTIONS: {
                LOOP.START: 7342000000,
                LOOP.STOP: 7352000000,
                LOOP.NUM: None,
                LOOP.STEP: 100000,
                LOOP.LOGARITHMIC: False,
                LOOP.CHANNEL_ID: None,
                LOOP.VALUES: None,
            },
            LOOP.LOOP: None,
        }
    ],
    EXPERIMENT.RESULTS: [
        {
            RUNCARD.NAME: "qblox",
            "pulse_length": 8000,
            "qblox_raw_results": [
                {
                    "scope": {
                        "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                        "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
                    },
                    "bins": {
                        "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                        "threshold": [0.48046875],
                        "avg_cnt": [1024],
                    },
                }
            ],
        },
        {
            RUNCARD.NAME: "qblox",
            "pulse_length": 8000,
            "qblox_raw_results": [
                {
                    "scope": {
                        "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                        "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
                    },
                    "bins": {
                        "integration": {"path0": [-0.14089025097703958], "path1": [-0.3594594414081583]},
                        "threshold": [0.4599609375],
                        "avg_cnt": [1024],
                    },
                }
            ],
        },
    ],
}

results_one_loops_empty = {
    EXPERIMENT.SOFTWARE_AVERAGE: 1,
    EXPERIMENT.NUM_SCHEDULES: 1,
    EXPERIMENT.SHAPE: [100],
    EXPERIMENT.LOOPS: [
        {
            RUNCARD.ALIAS: "rs_1",
            LOOP.PARAMETER: Node.FREQUENCY.value,
            LOOP.OPTIONS: {
                LOOP.START: 7342000000,
                LOOP.STOP: 7352000000,
                LOOP.NUM: None,
                LOOP.STEP: 100000,
                LOOP.LOGARITHMIC: False,
                LOOP.CHANNEL_ID: None,
                LOOP.VALUES: None,
            },
            LOOP.LOOP: None,
        }
    ],
    EXPERIMENT.RESULTS: [],
}

experiment = {
    RUNCARD.PLATFORM: Galadriel.runcard,
    EXPERIMENT.OPTIONS: {
        EXPERIMENT.LOOPS: [
            {
                RUNCARD.ALIAS: "qblox_qrm",
                LOOP.PARAMETER: Parameter.GAIN.value,
                LOOP.OPTIONS: {
                    LOOP.START: 0.1,
                    LOOP.STOP: 1,
                    LOOP.NUM: None,
                    LOOP.STEP: 0.3,
                    LOOP.LOGARITHMIC: False,
                    LOOP.CHANNEL_ID: 0,
                    LOOP.VALUES: None,
                },
                LOOP.LOOP: {
                    RUNCARD.ALIAS: "attenuator",
                    LOOP.PARAMETER: Parameter.ATTENUATION.value,
                    LOOP.OPTIONS: {
                        LOOP.START: 15,
                        LOOP.STOP: 90,
                        LOOP.NUM: None,
                        LOOP.STEP: 1,
                        LOOP.LOGARITHMIC: False,
                        LOOP.CHANNEL_ID: None,
                        LOOP.VALUES: None,
                    },
                    LOOP.LOOP: {
                        RUNCARD.ALIAS: "rs_1",
                        LOOP.PARAMETER: Node.FREQUENCY.value,
                        LOOP.OPTIONS: {
                            LOOP.START: 7342000000,
                            LOOP.STOP: 7352000000,
                            LOOP.NUM: None,
                            LOOP.STEP: 100000,
                            LOOP.LOGARITHMIC: False,
                            LOOP.CHANNEL_ID: None,
                            LOOP.VALUES: None,
                        },
                        LOOP.LOOP: None,
                    },
                },
            }
        ],
        RUNCARD.NAME: "punchout",
        RUNCARD.SETTINGS: {
            EXPERIMENT.HARDWARE_AVERAGE: 1024,
            EXPERIMENT.SOFTWARE_AVERAGE: 1,
            EXPERIMENT.REPETITION_DURATION: 200000,
        },
    },
    EXPERIMENT.PULSE_SCHEDULES: [
        {
            PULSESCHEDULES.ELEMENTS: [
                {
                    PULSEBUSSCHEDULE.TIMELINE: [
                        {
                            PULSEEVENT.PULSE: {
                                PULSE.NAME: PulseName.READOUT_PULSE.value,
                                PULSE.AMPLITUDE: 1,
                                PULSE.FREQUENCY: 1e9,
                                PULSE.PHASE: 0,
                                PULSE.DURATION: 2000,
                                PULSE.PULSE_SHAPE: {RUNCARD.NAME: PulseShapeName.RECTANGULAR.value},
                            },
                            PULSEEVENT.START_TIME: 40,
                        }
                    ],
                    PULSEBUSSCHEDULE.PORT: 1,
                }
            ],
        }
    ],
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
        mocked_platform = cls.handlers[platform_name]
        return copy.deepcopy(mocked_platform.runcard)
