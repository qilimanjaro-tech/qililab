""" Data to use alongside the test suite. """
import copy
from multiprocessing.pool import RUN

import numpy as np
from qibo.gates import RX, RY, I, M, X, Y
from qibo.models.circuit import Circuit

from qililab.constants import (
    CONNECTION,
    EXPERIMENT,
    INSTRUMENTCONTROLLER,
    INSTRUMENTREFERENCE,
    LOOP,
    NODE,
    PLATFORM,
    PULSE,
    PULSEBUSSCHEDULE,
    PULSEEVENT,
    PULSESCHEDULES,
    PULSESHAPE,
    RUNCARD,
    SCHEMA,
)
from qililab.instruments.awg_settings.typings import AWGSequencerTypes, AWGTypes
from qililab.typings.enums import (
    AcquireTriggerMode,
    Category,
    ConnectionName,
    InstrumentControllerName,
    InstrumentControllerSubCategory,
    InstrumentName,
    IntegrationMode,
    Line,
    NodeName,
    Parameter,
    PulseShapeName,
    ReferenceClock,
    ResetMethod,
    SystemControlName,
)


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    platform = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "galadriel",
        PLATFORM.DEVICE_ID: 9,
        RUNCARD.ALIAS: None,
        RUNCARD.CATEGORY: RUNCARD.PLATFORM,
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 0,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "operations": [
            {
                RUNCARD.NAME: "Rxy",
                "pulse": {RUNCARD.NAME: "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                RUNCARD.NAME: "R180",
                "pulse": {RUNCARD.NAME: "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                RUNCARD.NAME: "X",
                "pulse": {RUNCARD.NAME: "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                RUNCARD.NAME: "Measure",
                "pulse": {RUNCARD.NAME: "Square", "amplitude": 1.0, "duration": 6000, "parameters": {}},
            },
        ],
        "gates": {
            0: [
                {
                    RUNCARD.NAME: "M",
                    "amplitude": 1,
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
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 50,
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
                    "duration": 20,
                    EXPERIMENT.SHAPE: {
                        RUNCARD.NAME: "drag",
                        "num_sigmas": 4,
                        "drag_coefficient": 0,
                    },
                },
                {
                    RUNCARD.NAME: "Drag",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 50,
                    EXPERIMENT.SHAPE: {
                        RUNCARD.NAME: "drag",
                        "num_sigmas": 4,
                        "drag_coefficient": 1.0,
                    },
                },
            ],
            1: [
                {
                    RUNCARD.NAME: "M",
                    "amplitude": 1,
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
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 50,
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
                    "duration": 20,
                    EXPERIMENT.SHAPE: {
                        RUNCARD.NAME: "drag",
                        "num_sigmas": 4,
                        "drag_coefficient": 0,
                    },
                },
                {
                    RUNCARD.NAME: "Drag",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 50,
                    EXPERIMENT.SHAPE: {
                        RUNCARD.NAME: "drag",
                        "num_sigmas": 4,
                        "drag_coefficient": 1.0,
                    },
                },
            ],
            (0, 1): [
                {
                    RUNCARD.NAME: "M",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 2000,
                    EXPERIMENT.SHAPE: {RUNCARD.NAME: "rectangular"},
                }
            ],
            (1, 0): [
                {
                    RUNCARD.NAME: "M",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 2000,
                    EXPERIMENT.SHAPE: {RUNCARD.NAME: "rectangular"},
                }
            ],
        },
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
        Parameter.NUM_SEQUENCERS.value: 2,
        AWGTypes.OUT_OFFSETS.value: [0, 0.5, 0.7, 0.8],
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 0,
                "output_i": 0,
                "output_q": 1,
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
            },
            {
                AWGSequencerTypes.IDENTIFIER.value: 1,
                AWGSequencerTypes.CHIP_PORT_ID.value: 10,
                "output_i": 0,
                "output_q": 1,
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
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
        Parameter.NUM_SEQUENCERS.value: 2,
        Parameter.ACQUISITION_DELAY_TIME.value: 100,
        AWGTypes.OUT_OFFSETS.value: [0.123, 1.23],
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 1,
                "qubit": 0,
                "output_i": 0,
                "output_q": 1,
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_123,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: True,
                Parameter.WEIGHTS_I.value: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                Parameter.WEIGHTS_Q.value: [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
                Parameter.WEIGHED_ACQ_ENABLED.value: True,
                Parameter.THRESHOLD.value: 0.5,
            },
            {
                AWGSequencerTypes.IDENTIFIER.value: 1,
                AWGSequencerTypes.CHIP_PORT_ID.value: 1,
                "qubit": 1,
                "output_i": 0,
                "output_q": 1,
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 200_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_000,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: False,
                Parameter.WEIGHTS_I.value: [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
                Parameter.WEIGHTS_Q.value: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                Parameter.WEIGHED_ACQ_ENABLED.value: False,
                Parameter.THRESHOLD.value: 0.5,
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
        Parameter.RF_ON.value: True,
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
        Parameter.RF_ON.value: True,
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
        RUNCARD.ALIAS: None,
        RUNCARD.CATEGORY: Category.CHIP.value,
        NODE.NODES: [
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 10, NODE.LINE: Line.FLUX.value, NODE.NODES: [3]},
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 0, NODE.LINE: Line.DRIVE.value, NODE.NODES: [3]},
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 1, NODE.LINE: Line.FEEDLINE_INPUT.value, NODE.NODES: [2]},
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 11, NODE.LINE: Line.FEEDLINE_OUTPUT.value, NODE.NODES: [2]},
            {
                RUNCARD.NAME: NodeName.RESONATOR.value,
                RUNCARD.ID: 2,
                RUNCARD.ALIAS: NodeName.RESONATOR.value,
                NODE.FREQUENCY: 7.34730e09,
                NODE.NODES: [1, 11, 3],
            },
            {
                RUNCARD.NAME: NodeName.QUBIT.value,
                RUNCARD.ID: 3,
                RUNCARD.ALIAS: NodeName.QUBIT.value,
                NODE.QUBIT_INDEX: 0,
                NODE.FREQUENCY: 3.451e09,
                NODE.NODES: [0, 2, 10],
            },
        ],
    }

    buses = [
        {
            RUNCARD.ID: 0,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.ALIAS: "drive_line_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 0,
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            },
            NodeName.PORT.value: 0,
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ID: 1,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.ALIAS: "feedline_input_output_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 1,
                RUNCARD.NAME: SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QRM.value, "rs_1"],
            },
            NodeName.PORT.value: 1,
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ID: 2,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.ALIAS: "flux_line_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 0,
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            },
            NodeName.PORT.value: 10,
            RUNCARD.DISTORTIONS: [],
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
        RUNCARD.NAME: NodeName.RESONATOR,
        RUNCARD.CATEGORY: NodeName.RESONATOR.value,
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
        PLATFORM.DEVICE_ID: 9,
        RUNCARD.CATEGORY: RUNCARD.PLATFORM,
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "operations": [
            {
                RUNCARD.NAME: "Rxy",
                "pulse": {RUNCARD.NAME: "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                RUNCARD.NAME: "R180",
                "pulse": {RUNCARD.NAME: "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                RUNCARD.NAME: "X",
                "pulse": {RUNCARD.NAME: "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
        ],
        "gates": {
            0: [
                {
                    RUNCARD.NAME: "M",
                    "amplitude": 1,
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
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 50,
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
                    "duration": 20,
                    EXPERIMENT.SHAPE: {
                        RUNCARD.NAME: "drag",
                        "num_sigmas": 4,
                        "drag_coefficient": 0,
                    },
                },
            ]
        },
    }

    chip = {
        RUNCARD.ID: 0,
        RUNCARD.CATEGORY: Category.CHIP.value,
        NODE.NODES: [
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 0, NODE.LINE: Line.DRIVE.value, NODE.NODES: [1]},
            {
                RUNCARD.NAME: NodeName.QUBIT.value,
                RUNCARD.ID: 1,
                NODE.QUBIT_INDEX: 0,
                NODE.FREQUENCY: 3.451e09,
                NODE.NODES: [0],
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
                RUNCARD.CATEGORY: Category.BUS.value,
                RUNCARD.ALIAS: "simulated_bus",
                Category.SYSTEM_CONTROL.value: {
                    RUNCARD.ID: 0,
                    RUNCARD.NAME: SystemControlName.SIMULATED_SYSTEM_CONTROL,
                    RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
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


experiment_params: list[list[str | Circuit | list[Circuit]]] = []
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
            LOOP.VALUES: (np.arange(start=15, stop=90, step=1)).tolist(),
            LOOP.CHANNEL_ID: None,
            LOOP.LOOP: {
                RUNCARD.ALIAS: "rs_1",
                LOOP.PARAMETER: NODE.FREQUENCY,
                LOOP.VALUES: (np.arange(start=7342000000, stop=7352000000, step=100000)).tolist(),
                LOOP.LOOP: None,
                LOOP.CHANNEL_ID: None,
            },
        },
    ],
    EXPERIMENT.RESULTS: [
        {
            RUNCARD.NAME: "qblox",
            "integration_lengths": [8000],
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
            "integration_lengths": [8000],
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
            LOOP.PARAMETER: NODE.FREQUENCY,
            LOOP.VALUES: (np.arange(start=7342000000, stop=7352000000, step=100000)).tolist(),
            LOOP.LOOP: None,
            LOOP.CHANNEL_ID: None,
        }
    ],
    EXPERIMENT.RESULTS: [
        {
            RUNCARD.NAME: "qblox",
            "integration_lengths": [8000],
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
            "integration_lengths": [8000],
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
            LOOP.PARAMETER: NODE.FREQUENCY,
            LOOP.VALUES: np.arange(start=7342000000, stop=7352000000, step=100000),
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
                LOOP.VALUES: np.arange(start=0.1, stop=1, step=0.3),
                LOOP.CHANNEL_ID: 0,
                LOOP.LOOP: {
                    RUNCARD.ALIAS: "attenuator",
                    LOOP.PARAMETER: Parameter.ATTENUATION.value,
                    LOOP.VALUES: np.arange(start=15, stop=90, step=1),
                    LOOP.LOOP: {
                        RUNCARD.ALIAS: "rs_1",
                        LOOP.PARAMETER: NODE.FREQUENCY,
                        LOOP.VALUES: np.arange(start=7342000000, stop=7352000000, step=100000),
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


class SauronVNA:
    """Test data of the sauron platform."""

    name = "sauron_vna"

    platform = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: "sauron_vna",
        PLATFORM.DEVICE_ID: 9,
        RUNCARD.ALIAS: None,
        RUNCARD.CATEGORY: RUNCARD.PLATFORM,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "gates": {},
        "operations": [],
    }

    keysight_e5080b_controller = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentControllerName.KEYSIGHT_E5080B,
        RUNCARD.ALIAS: InstrumentControllerName.KEYSIGHT_E5080B.value,
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        Parameter.TIMEOUT.value: 10000,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.254",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.VNA.value: InstrumentName.KEYSIGHT_E5080B.value,
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    keysight_e5080b = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentName.KEYSIGHT_E5080B,
        RUNCARD.ALIAS: InstrumentName.KEYSIGHT_E5080B.value,
        RUNCARD.CATEGORY: Category.VNA.value,
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.POWER.value: -60.0,
    }

    agilent_e5071b_controller = {
        RUNCARD.ID: 1,
        RUNCARD.NAME: InstrumentControllerName.AGILENT_E5071B,
        RUNCARD.ALIAS: InstrumentControllerName.AGILENT_E5071B.value,
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        Parameter.TIMEOUT.value: 10000,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.254",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.VNA.value: InstrumentName.AGILENT_E5071B.value,
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            }
        ],
    }

    agilent_e5071b = {
        RUNCARD.ID: 0,
        RUNCARD.NAME: InstrumentName.AGILENT_E5071B,
        RUNCARD.ALIAS: InstrumentName.AGILENT_E5071B.value,
        RUNCARD.CATEGORY: Category.VNA.value,
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.POWER.value: -60.0,
    }

    instruments = [keysight_e5080b, agilent_e5071b]
    instrument_controllers = [keysight_e5080b_controller, agilent_e5071b_controller]

    chip = {
        RUNCARD.ID: 0,
        RUNCARD.ALIAS: None,
        RUNCARD.CATEGORY: Category.CHIP.value,
        NODE.NODES: [
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 0, NODE.LINE: Line.DRIVE.value, NODE.NODES: [3]},
            {RUNCARD.NAME: NodeName.PORT.value, RUNCARD.ID: 1, NODE.LINE: Line.FEEDLINE_INPUT.value, NODE.NODES: [2]},
            {
                RUNCARD.NAME: NodeName.RESONATOR.value,
                RUNCARD.ID: 2,
                RUNCARD.ALIAS: NodeName.RESONATOR.value,
                NODE.FREQUENCY: 8.0726e09,
                NODE.NODES: [1, 3],
            },
            {
                RUNCARD.NAME: NodeName.QUBIT.value,
                RUNCARD.ID: 3,
                RUNCARD.ALIAS: NodeName.QUBIT.value,
                NODE.QUBIT_INDEX: 0,
                NODE.FREQUENCY: 6.5328e09,
                NODE.NODES: [0, 2],
            },
        ],
    }

    buses = [
        {
            RUNCARD.ID: 0,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.ALIAS: "keysight_e5080b_readout_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 0,
                RUNCARD.NAME: SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.INSTRUMENTS: [InstrumentName.KEYSIGHT_E5080B.value],
            },
            NodeName.PORT.value: 1,
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ID: 1,
            RUNCARD.CATEGORY: Category.BUS.value,
            RUNCARD.ALIAS: "agilent_e5071b_readout_bus",
            Category.SYSTEM_CONTROL.value: {
                RUNCARD.ID: 1,
                RUNCARD.NAME: SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.CATEGORY: Category.SYSTEM_CONTROL.value,
                RUNCARD.INSTRUMENTS: [InstrumentName.AGILENT_E5071B.value],
            },
            NodeName.PORT.value: 0,
            RUNCARD.DISTORTIONS: [],
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


class MockedSettingsFactory:
    """Class that loads a specific class given an object's name."""

    handlers: dict[str, type[Galadriel] | type[FluxQubitSimulator]] = {
        "galadriel": Galadriel,
        "flux_qubit": FluxQubitSimulator,
    }

    @classmethod
    def register(cls, handler_cls: type[Galadriel] | type[FluxQubitSimulator]):
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
