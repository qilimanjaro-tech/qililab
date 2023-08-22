""" Data to use alongside the test suite. """
# pylint: disable=too-many-lines
import copy
from typing import Any

import numpy as np
from qblox_instruments.types import PulsarType
from qibo.gates import I, M, X, Y
from qibo.models.circuit import Circuit

from qililab.constants import (
    CONNECTION,
    EXPERIMENT,
    INSTRUMENTCONTROLLER,
    LOOP,
    PLATFORM,
    PULSE,
    PULSEBUSSCHEDULE,
    PULSEEVENT,
    PULSESCHEDULES,
    RUNCARD,
)
from qililab.instruments.awg_settings.typings import AWGTypes
from qililab.typings.enums import (
    AcquireTriggerMode,
    ConnectionName,
    InstrumentControllerName,
    InstrumentName,
    IntegrationMode,
    Parameter,
    PulseShapeName,
    ReferenceClock,
    ResetMethod,
    SystemControlName,
)

class NewGaladriel:
    """Test data of the new galadriel platform."""

    name = "galadriel"

    gates_settings: dict[str, Any] = {
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 0,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "operations": [],
        "gates": {},
    }
    device_id = 0
    chip: dict[str, Any] = {
        "nodes": [],
    }
    instrument_controllers: dict[str, Any] = {}
    buses: dict[str, Any] = {}
    pulsar_qrm: dict[str, Any]  = {
        "alias": "pulsar_qrm",
        "type": "Pulsar",
        "dummy_type": PulsarType.PULSAR_QCM,
        "sequencers": {
            "q0_flux": {
                "path0": "0"
            },
            "q1_flux": {
                "path0": "1"
            },
            "q2_flux": {
                "path0": "2"
            },
            "q3_flux": {
                "path0": "3"
            },
            "q4_flux": {
                "path0": "0"
            },
        }
    }

    instruments: list[dict] = [pulsar_qrm]

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    device_id = 9

    gates_settings: dict[str, Any] = {
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 0,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "operations": [
            {
                "name": "Rxy",
                "pulse": {"name": "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                "name": "R180",
                "pulse": {"name": "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                "name": "X",
                "pulse": {"name": "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                "name": "Measure",
                "pulse": {"name": "Square", "amplitude": 1.0, "duration": 6000, "parameters": {}},
            },
        ],
        "gates": {
            "M(0)": [
                {
                    "bus": "feedline_input_output_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 2000,
                        "frequency": 0,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "I(0)": [
                {
                    "bus": "drive_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 100,
                        "frequency": 0,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "X(0)": [
                {
                    "bus": "drive_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 50,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "Y(0)": [
                {
                    "bus": "drive_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "RY(0)": [
                {
                    "bus": "drive_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "RX(0)": [
                {
                    "bus": "drive_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
        },
    }

    pulsar_controller_qcm_0: dict[str, Any] = {
        "name": InstrumentControllerName.QBLOX_PULSAR,
        "alias": "pulsar_controller_qcm_0",
        Parameter.REFERENCE_CLOCK.value: ReferenceClock.INTERNAL.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.3",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.QBLOX_QCM.value,
                "slot_id": 0,
            }
        ],
    }

    qblox_qcm_0: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QCM,
        "alias": InstrumentName.QBLOX_QCM.value,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 2,
        AWGTypes.OUT_OFFSETS.value: [0, 0.5, 0.7, 0.8],
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                "identifier": 0,
                "chip_port_id": "drive_q0",
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
                "identifier": 1,
                "chip_port_id": "flux_q0",
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

    pulsar_controller_qrm_0: dict[str, Any] = {
        "name": InstrumentControllerName.QBLOX_PULSAR,
        "alias": "pulsar_controller_qrm_0",
        Parameter.REFERENCE_CLOCK.value: ReferenceClock.EXTERNAL.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.4",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.QBLOX_QRM.value,
                "slot_id": 0,
            }
        ],
    }

    qblox_qrm_0: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QRM,
        "alias": InstrumentName.QBLOX_QRM.value,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 2,
        Parameter.ACQUISITION_DELAY_TIME.value: 100,
        AWGTypes.OUT_OFFSETS.value: [0.123, 1.23],
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                "identifier": 0,
                "chip_port_id": "feedline_input",
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
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
            {
                "identifier": 1,
                "chip_port_id": "feedline_input",
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
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
        ],
    }

    rohde_schwarz_controller_0: dict[str, Any] = {
        "name": InstrumentControllerName.ROHDE_SCHWARZ,
        "alias": "rohde_schwarz_controller_0",
        Parameter.REFERENCE_CLOCK.value: "EXT",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.10",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rs_0",
                "slot_id": 0,
            }
        ],
    }

    rohde_schwarz_0: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ,
        "alias": "rs_0",
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    rohde_schwarz_controller_1: dict[str, Any] = {
        "name": InstrumentControllerName.ROHDE_SCHWARZ,
        "alias": "rohde_schwarz_controller_1",
        Parameter.REFERENCE_CLOCK.value: "EXT",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.7",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rs_1",
                "slot_id": 0,
            }
        ],
    }

    rohde_schwarz_1: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ,
        "alias": "rs_1",
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 3.351e09,
        Parameter.RF_ON.value: True,
    }

    attenuator_controller_0: dict[str, Any] = {
        "name": InstrumentControllerName.MINI_CIRCUITS,
        "alias": "attenuator_controller_0",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.222",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "attenuator",
                "slot_id": 0,
            }
        ],
    }

    attenuator: dict[str, Any] = {
        "name": InstrumentName.MINI_CIRCUITS,
        "alias": "attenuator",
        Parameter.ATTENUATION.value: 30,
        RUNCARD.FIRMWARE: None,
    }

    keithley_2600_controller_0: dict[str, Any] = {
        "name": InstrumentControllerName.KEITHLEY2600,
        "alias": "keithley_2600_controller_0",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.112",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.KEITHLEY2600.value,
                "slot_id": 0,
            }
        ],
    }

    keithley_2600: dict[str, Any] = {
        "name": InstrumentName.KEITHLEY2600,
        "alias": InstrumentControllerName.KEITHLEY2600.value,
        RUNCARD.FIRMWARE: None,
        Parameter.MAX_CURRENT.value: 0.1,
        Parameter.MAX_VOLTAGE.value: 20.0,
    }

    instruments: list[dict] = [qblox_qcm_0, qblox_qrm_0, rohde_schwarz_0, rohde_schwarz_1, attenuator, keithley_2600]
    instrument_controllers: list[dict] = [
        pulsar_controller_qcm_0,
        pulsar_controller_qrm_0,
        rohde_schwarz_controller_0,
        rohde_schwarz_controller_1,
        attenuator_controller_0,
        keithley_2600_controller_0,
    ]

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "flux_q0", "line": "flux", "nodes": ["q0"]},
            {"name": "port", "alias": "drive_q0", "line": "drive", "nodes": ["q0"]},
            {"name": "port", "alias": "feedline_input", "line": "feedline_input", "nodes": ["resonator_q0"]},
            {"name": "port", "alias": "feedline_output", "line": "feedline_output", "nodes": ["resonator_q0"]},
            {
                "name": "resonator",
                "alias": "resonator_q0",
                "frequency": 7.34730e09,
                "nodes": ["feedline_input", "feedline_output", "q0"],
            },
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 3.451e09,
                "nodes": ["flux_q0", "drive_q0", "resonator_q0"],
            },
        ],
    }

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "drive_line_q0_bus",
            "system_control": {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            },
            "port": "drive_q0",
            RUNCARD.DISTORTIONS: [],
            RUNCARD.DELAY: 0,
        },
        {
            "alias": "feedline_input_output_bus",
            "system_control": {
                "name": SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QRM.value, "rs_1"],
            },
            "port": "feedline_input",
            RUNCARD.DISTORTIONS: [],
            RUNCARD.DELAY: 0,
        },
        {
            RUNCARD.ALIAS: "flux_line_q0_bus",
            "system_control": {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            },
            "port": "flux_q0",
            RUNCARD.DISTORTIONS: [],
            RUNCARD.DELAY: 0,
        },
    ]

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }

    qubit_0: dict[str, Any] = {
        "name": "qubit",
        "alias": "qubit",
        "pi_pulse_amplitude": 1,
        "pi_pulse_duration": 100,
        "pi_pulse_frequency": 100000000.0,
        "qubit_frequency": 3544000000.0,
        "min_voltage": 950,
        "max_voltage": 1775,
    }

    resonator_0: dict[str, Any] = {
        "name": "resonator",
        "qubits": [
            {
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

    device_id = 9

    gates_settings: dict[str, Any] = {
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "operations": [
            {
                "name": "Rxy",
                "pulse": {"name": "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                "name": "R180",
                "pulse": {"name": "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
            {
                "name": "X",
                "pulse": {"name": "Gaussian", "amplitude": 1.0, "duration": 40, "parameters": {"sigma": 2}},
            },
        ],
        "gates": {
            "M(0)": [
                {
                    "bus": "simulated_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 2000,
                        "frequency": 0,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "I(0)": [
                {
                    "bus": "simulated_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 100,
                        "frequency": 0,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "X(0)": [
                {
                    "bus": "simulated_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 50,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "Y(0)": [
                {
                    "bus": "simulated_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "RY(0)": [
                {
                    "bus": "simulated_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "RX(0)": [
                {
                    "bus": "simulated_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "frequency": 0,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
        },
    }

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "drive_q0", "line": "drive", "nodes": ["q0"]},
            {"name": "qubit", "alias": "q0", "qubit_index": 0, "frequency": 3.451e09, "nodes": ["drive_q0"]},
        ],
    }

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.INSTRUMENTS: [],
        RUNCARD.INSTRUMENT_CONTROLLERS: [],
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: [
            {
                "alias": "simulated_bus",
                "system_control": {
                    "name": SystemControlName.SIMULATED_SYSTEM_CONTROL,
                    "qubit": "csfq4jj",
                    "qubit_params": {"n_cut": 10, "phi_x": 6.28318530718, "phi_z": -0.25132741228},
                    "drive": "zport",
                    "drive_params": {"dimension": 10},
                    "resolution": 1,
                    "store_states": False,
                },
                RUNCARD.DISTORTIONS: [],
                "port": "drive_q0",
            }
        ],
    }


experiment_params: list[list[str | Circuit | list[Circuit]]] = []
for platform in [Galadriel]:
    circuit = Circuit(1)
    circuit.add(I(0))
    circuit.add(X(0))
    circuit.add(Y(0))
    # FIXME: https://www.notion.so/qilimanjaro/Adapt-test-data-runcard-circuit-to-current-implementation-d875fecbe5834272a4a43e9b3f602685?pvs=4
    # circuit.add(RX(0, 23))
    # circuit.add(RY(0, 15))
    if platform == Galadriel:
        circuit.add(M(0))
    experiment_params.extend([[platform.runcard, circuit], [platform.runcard, [circuit, circuit]]])  # type: ignore

# Circuit used for simulator
simulated_experiment_circuit: Circuit = Circuit(1)
simulated_experiment_circuit.add(I(0))
simulated_experiment_circuit.add(X(0))
simulated_experiment_circuit.add(Y(0))
# simulated_experiment_circuit.add(RX(0, 23))
# simulated_experiment_circuit.add(RY(0, 15))

results_two_loops: dict[str, Any] = {
    EXPERIMENT.SOFTWARE_AVERAGE: 1,
    EXPERIMENT.NUM_SCHEDULES: 1,
    EXPERIMENT.SHAPE: [75, 100],
    EXPERIMENT.LOOPS: [
        {
            "alias": "attenuator",
            LOOP.PARAMETER: Parameter.ATTENUATION.value,
            LOOP.VALUES: (np.arange(start=15, stop=90, step=1)).tolist(),
            LOOP.CHANNEL_ID: None,
            LOOP.LOOP: {
                "alias": "rs_1",
                LOOP.PARAMETER: "frequency",
                LOOP.VALUES: (np.arange(start=7342000000, stop=7352000000, step=100000)).tolist(),
                LOOP.LOOP: None,
                LOOP.CHANNEL_ID: None,
            },
        },
    ],
    EXPERIMENT.RESULTS: [
        {
            "name": "qblox",
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
            "name": "qblox",
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

results_one_loops: dict[str, Any] = {
    EXPERIMENT.SOFTWARE_AVERAGE: 1,
    EXPERIMENT.NUM_SCHEDULES: 1,
    EXPERIMENT.SHAPE: [100],
    EXPERIMENT.LOOPS: [
        {
            "alias": "rs_1",
            LOOP.PARAMETER: "frequency",
            LOOP.VALUES: (np.arange(start=7342000000, stop=7352000000, step=100000)).tolist(),
            LOOP.LOOP: None,
            LOOP.CHANNEL_ID: None,
        }
    ],
    EXPERIMENT.RESULTS: [
        {
            "name": "qblox",
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
            "name": "qblox",
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

results_one_loops_empty: dict[str, Any] = {
    EXPERIMENT.SOFTWARE_AVERAGE: 1,
    EXPERIMENT.NUM_SCHEDULES: 1,
    EXPERIMENT.SHAPE: [100],
    EXPERIMENT.LOOPS: [
        {
            "alias": "rs_1",
            LOOP.PARAMETER: "frequency",
            LOOP.VALUES: np.arange(start=7342000000, stop=7352000000, step=100000),
            LOOP.LOOP: None,
        }
    ],
    EXPERIMENT.RESULTS: [],
}

experiment: dict[str, Any] = {
    RUNCARD.PLATFORM: Galadriel.runcard,
    EXPERIMENT.OPTIONS: {
        EXPERIMENT.LOOPS: [
            {
                "alias": "qblox_qrm",
                LOOP.PARAMETER: Parameter.GAIN.value,
                LOOP.VALUES: np.arange(start=0.1, stop=1, step=0.3),
                LOOP.CHANNEL_ID: 0,
                LOOP.LOOP: {
                    "alias": "attenuator",
                    LOOP.PARAMETER: Parameter.ATTENUATION.value,
                    LOOP.VALUES: np.arange(start=15, stop=90, step=1),
                    LOOP.LOOP: {
                        "alias": "rs_1",
                        LOOP.PARAMETER: "frequency",
                        LOOP.VALUES: np.arange(start=7342000000, stop=7352000000, step=100000),
                        LOOP.LOOP: None,
                    },
                },
            }
        ],
        RUNCARD.NAME: "punchout",
        RUNCARD.GATES_SETTINGS: {
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
                                PULSE.PULSE_SHAPE: {"name": PulseShapeName.RECTANGULAR.value},
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

    device_id = 9

    gates_settings: dict[str, Any] = {
        PLATFORM.DELAY_BETWEEN_PULSES: 0,
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BEFORE_READOUT: 40,
        PLATFORM.TIMINGS_CALCULATION_METHOD: "as_soon_as_possible",
        PLATFORM.RESET_METHOD: ResetMethod.PASSIVE.value,
        PLATFORM.PASSIVE_RESET_DURATION: 100,
        "gates": {},
        "operations": [],
    }

    keysight_e5080b_controller: dict[str, Any] = {
        "name": InstrumentControllerName.KEYSIGHT_E5080B,
        "alias": InstrumentControllerName.KEYSIGHT_E5080B.value,
        Parameter.TIMEOUT.value: 10000,
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.254",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.KEYSIGHT_E5080B.value,
                "slot_id": 0,
            }
        ],
    }

    keysight_e5080b: dict[str, Any] = {
        "name": InstrumentName.KEYSIGHT_E5080B,
        "alias": InstrumentName.KEYSIGHT_E5080B.value,
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.POWER.value: -60.0,
    }

    agilent_e5071b_controller: dict[str, Any] = {
        "name": InstrumentControllerName.AGILENT_E5071B,
        "alias": InstrumentControllerName.AGILENT_E5071B.value,
        Parameter.TIMEOUT.value: 10000,
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.254",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.AGILENT_E5071B.value,
                "slot_id": 0,
            }
        ],
    }

    agilent_e5071b: dict[str, Any] = {
        "name": InstrumentName.AGILENT_E5071B,
        "alias": InstrumentName.AGILENT_E5071B.value,
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.POWER.value: -60.0,
    }

    instruments: list[dict] = [keysight_e5080b, agilent_e5071b]
    instrument_controllers: list[dict] = [keysight_e5080b_controller, agilent_e5071b_controller]

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "drive_q0", "line": "drive", "nodes": ["q0"]},
            {"name": "port", "alias": "feedline_input", "line": "feedline_input", "nodes": ["resonator_q0"]},
            {"name": "resonator", "alias": "resonator_q0", "frequency": 8.0726e09, "nodes": ["feedline_input", "q0"]},
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 6.5328e09,
                "nodes": ["drive_q0", "resonator_q0"],
            },
        ],
    }

    buses: list[dict[str, Any]] = [
        {
            "alias": "keysight_e5080b_readout_bus",
            "system_control": {
                "name": SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [InstrumentName.KEYSIGHT_E5080B.value],
            },
            "port": "drive_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            "alias": "agilent_e5071b_readout_bus",
            "system_control": {
                "name": SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [InstrumentName.AGILENT_E5071B.value],
            },
            "port": "feedline_input",
            RUNCARD.DISTORTIONS: [],
        },
    ]

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
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
