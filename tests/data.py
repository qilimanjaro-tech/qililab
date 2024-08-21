""" Data to use alongside the test suite. """

# pylint: disable=too-many-lines
import copy
from typing import Any

import numpy as np
from qibo.gates import Align, I, M, X, Y
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


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

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
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "M(1)": [
                {
                    "bus": "feedline_input_output_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 2000,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "M(2)": [
                {
                    "bus": "feedline_input_output_bus_1",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 2000,
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
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "Drag(0)": [
                {
                    "bus": "drive_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 50,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "Drag(1)": [
                {
                    "bus": "drive_line_q1_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 50,
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
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
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "X(1)": [
                {
                    "bus": "drive_line_q1_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 0,
                        "duration": 50,
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
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "Y(1)": [
                {
                    "bus": "drive_line_q1_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
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
                        "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
                    },
                }
            ],
            "CZ(0,1)": [
                {
                    "bus": "flux_line_q1_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "shape": {"name": "rectangular"},
                        "options": {"q0_phase_correction": 0.1, "q2_phase_correction": 0.2},
                    },
                }
            ],
            "CZ(0, 2)": [
                {
                    "bus": "flux_line_q0_bus",
                    "wait_time": 0,
                    "pulse": {
                        "amplitude": 1.0,
                        "phase": 1.5707963267948966,
                        "duration": 20,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
        },
    }

    flux_control_topology: list[dict[str, str]] = [
        {"flux": "phix_q0", "bus": "flux_line_q0_bus"},
        {"flux": "phiz_q0", "bus": "flux_line_q0_bus"},
        {"flux": "phix_q1", "bus": "drive_line_q0_bus"},
        {"flux": "phiz_q1", "bus": "drive_line_q0_bus"},
        {"flux": "phix_c0_1", "bus": "flux_line_q0_bus"},
        {"flux": "phiz_c0_1", "bus": "flux_line_q0_bus"},
    ]

    pulsar_controller_qcm_0: dict[str, Any] = {
        "name": InstrumentControllerName.QBLOX_PULSAR,
        "alias": "pulsar_controller_qcm_0",
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
        INSTRUMENTCONTROLLER.RESET: False,
        Parameter.REFERENCE_CLOCK.value: ReferenceClock.INTERNAL.value,
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
                "outputs": [0, 1],
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
                "outputs": [0, 1],
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

    qblox_qcm_rf_0: dict[str, Any] = {
        "name": InstrumentName.QCMRF,
        "alias": InstrumentName.QCMRF.value,
        "firmware": "0.7.0",
        "num_sequencers": 1,
        "out0_lo_freq": 3.7e9,
        "out0_lo_en": True,
        "out0_att": 10,
        "out0_offset_path0": 0.2,
        "out0_offset_path1": 0.07,
        "out1_lo_freq": 3.9e9,
        "out1_lo_en": True,
        "out1_att": 6,
        "out1_offset_path0": 0.1,
        "out1_offset_path1": 0.6,
        "awg_sequencers": [
            {
                "identifier": 0,
                "chip_port_id": "drive_q1",
                "outputs": [0],
                "num_bins": 1,
                "intermediate_frequency": 20000000,
                "gain_i": 0.001,
                "gain_q": 0.02,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_i": 0,
                "offset_q": 0,
                "hardware_modulation": True,
            },
        ],
    }

    qblox_qrm_rf_0: dict[str, Any] = {
        "name": InstrumentName.QRMRF,
        "alias": InstrumentName.QRMRF.value,
        "firmware": "0.7.0",
        "num_sequencers": 1,
        "out0_in0_lo_freq": 3e9,
        "out0_in0_lo_en": True,
        "out0_att": 34,
        "in0_att": 28,
        "out0_offset_path0": 0.123,
        "out0_offset_path1": 1.234,
        "acquisition_delay_time": 100,
        "awg_sequencers": [
            {
                "identifier": 0,
                "chip_port_id": "feedline_output_1",
                "qubit": 1,
                "outputs": [0],
                "weights_i": [1, 1, 1, 1],
                "weights_q": [1, 1, 1, 1],
                "weighed_acq_enabled": False,
                "threshold": 0.5,
                "threshold_rotation": 45.0,
                "num_bins": 1,
                "intermediate_frequency": 20000000,
                "gain_i": 0.001,
                "gain_q": 0.02,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_i": 0,
                "offset_q": 0,
                "hardware_modulation": True,
                "scope_acquire_trigger_mode": "sequencer",
                "scope_hardware_averaging": True,
                "sampling_rate": 1000000000,
                "integration_length": 8000,
                "integration_mode": "ssb",
                "sequence_timeout": 1,
                "acquisition_timeout": 1,
                "hardware_demodulation": True,
                "scope_store_enabled": True,
                "time_of_flight": 40,
            }
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
                "alias": f"{InstrumentName.QBLOX_QRM.value}_0",
                "slot_id": 0,
            }
        ],
        INSTRUMENTCONTROLLER.RESET: True,
    }

    qblox_qrm_0: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QRM,
        "alias": f"{InstrumentName.QBLOX_QRM.value}_0",
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 2,
        Parameter.ACQUISITION_DELAY_TIME.value: 100,
        AWGTypes.OUT_OFFSETS.value: [0.123, 1.23],
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                "identifier": 0,
                "chip_port_id": "feedline_input",
                "qubit": 0,
                "outputs": [0, 1],
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
                Parameter.TIME_OF_FLIGHT.value: 40,
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
                "outputs": [0, 1],
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
                Parameter.TIME_OF_FLIGHT.value: 40,
                Parameter.WEIGHTS_I.value: [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
                Parameter.WEIGHTS_Q.value: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                Parameter.WEIGHED_ACQ_ENABLED.value: False,
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
        ],
    }

    pulsar_controller_qrm_1: dict[str, Any] = {
        "name": InstrumentControllerName.QBLOX_PULSAR,
        "alias": "pulsar_controller_qrm_1",
        Parameter.REFERENCE_CLOCK.value: ReferenceClock.EXTERNAL.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.5",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": f"{InstrumentName.QBLOX_QRM.value}_1",
                "slot_id": 0,
            }
        ],
        INSTRUMENTCONTROLLER.RESET: True,
    }

    qblox_qrm_1: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QRM,
        "alias": f"{InstrumentName.QBLOX_QRM.value}_1",
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        Parameter.ACQUISITION_DELAY_TIME.value: 100,
        AWGTypes.OUT_OFFSETS.value: [0.123, 1.23],
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                "identifier": 0,
                "chip_port_id": "feedline_output_2",
                "qubit": 2,
                "outputs": [0],
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
                Parameter.TIME_OF_FLIGHT.value: 40,
                Parameter.WEIGHTS_I.value: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                Parameter.WEIGHTS_Q.value: [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
                Parameter.WEIGHED_ACQ_ENABLED.value: True,
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
        INSTRUMENTCONTROLLER.RESET: True,
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
        INSTRUMENTCONTROLLER.RESET: True,
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
        INSTRUMENTCONTROLLER.RESET: True,
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
        INSTRUMENTCONTROLLER.RESET: True,
    }

    keithley_2600: dict[str, Any] = {
        "name": InstrumentName.KEITHLEY2600,
        "alias": InstrumentControllerName.KEITHLEY2600.value,
        RUNCARD.FIRMWARE: None,
        Parameter.MAX_CURRENT.value: 0.1,
        Parameter.MAX_VOLTAGE.value: 20.0,
    }

    instruments: list[dict] = [
        qblox_qcm_0,
        qblox_qrm_0,
        qblox_qrm_1,
        qblox_qcm_rf_0,
        qblox_qrm_rf_0,
        rohde_schwarz_0,
        rohde_schwarz_1,
        attenuator,
        keithley_2600,
    ]
    instrument_controllers: list[dict] = [
        pulsar_controller_qcm_0,
        pulsar_controller_qrm_0,
        pulsar_controller_qrm_1,
        rohde_schwarz_controller_0,
        rohde_schwarz_controller_1,
        attenuator_controller_0,
        keithley_2600_controller_0,
    ]

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "flux_q0", "line": "flux", "nodes": ["q0"]},
            {"name": "port", "alias": "flux_q1", "line": "flux", "nodes": ["q1"]},
            {"name": "port", "alias": "flux_q2", "line": "flux", "nodes": ["q2"]},
            {"name": "port", "alias": "drive_q0", "line": "drive", "nodes": ["q0"]},
            {"name": "port", "alias": "drive_q1", "line": "drive", "nodes": ["q1"]},
            {
                "name": "port",
                "alias": "feedline_input",
                "line": "feedline_input",
                "nodes": ["resonator_q0", "resonator_q1"],
            },
            {"name": "port", "alias": "feedline_output", "line": "feedline_output", "nodes": ["resonator_q0"]},
            {"name": "port", "alias": "feedline_output_1", "line": "feedline_output", "nodes": ["resonator_q1"]},
            {"name": "port", "alias": "feedline_output_2", "line": "feedline_input", "nodes": ["resonator_q2"]},
            {
                "name": "resonator",
                "alias": "resonator_q0",
                "frequency": 7.34730e09,
                "nodes": ["feedline_input", "feedline_output", "q0"],
            },
            {
                "name": "resonator",
                "alias": "resonator_q1",
                "frequency": 7.34730e09,
                "nodes": ["feedline_input", "feedline_output_1", "q1"],
            },
            {
                "name": "resonator",
                "alias": "resonator_q2",
                "frequency": 7.34730e09,
                "nodes": ["feedline_input", "feedline_output_2", "q2"],
            },
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 3.451e09,
                "nodes": ["flux_q0", "drive_q0", "resonator_q0"],
            },
            {
                "name": "qubit",
                "alias": "q1",
                "qubit_index": 1,
                "frequency": 3.351e09,
                "nodes": ["drive_q1", "resonator_q1"],
            },
            {
                "name": "qubit",
                "alias": "q2",
                "qubit_index": 2,
                "frequency": 4.451e09,
                "nodes": ["drive_q2", "resonator_q2"],
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
            RUNCARD.DISTORTIONS: [{"name": "lfilter", "a": [1.0], "auto_norm": True, "b": [1.0], "norm_factor": 1.0}],
            RUNCARD.DELAY: 0,
        },
        {
            RUNCARD.ALIAS: "drive_line_q1_bus",
            "system_control": {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [InstrumentName.QCMRF.value],
            },
            "port": "drive_q1",
            RUNCARD.DISTORTIONS: [],
            RUNCARD.DELAY: 0,
        },
        {
            "alias": "feedline_input_output_bus",
            "system_control": {
                "name": SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_0", "rs_1"],
            },
            "port": "feedline_input",
            RUNCARD.DISTORTIONS: [],
            RUNCARD.DELAY: 0,
        },
        {
            "alias": "feedline_input_output_bus_2",
            "system_control": {
                "name": SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_1"],
            },
            "port": "feedline_output_2",
            RUNCARD.DISTORTIONS: [],
            RUNCARD.DELAY: 0,
        },
        {
            "alias": "feedline_input_output_bus_1",
            "system_control": {
                "name": SystemControlName.READOUT_SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: [f"{InstrumentName.QRMRF.value}"],
            },
            "port": "feedline_output_1",
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
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.FLUX_CONTROL_TOPOLOGY: flux_control_topology,
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


class GaladrielDeviceID:
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
        "operations": [],
        "gates": {},
    }

    instruments: list[dict] = []
    instrument_controllers: list[dict] = []

    chip: dict[str, Any] = {
        "nodes": [],
    }

    buses: list[dict[str, Any]] = []

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        "device_id": device_id,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


parametrized_experiment_params: list[list[str | Circuit | list[Circuit]]] = []
for platform in [Galadriel]:
    circuit = Circuit(1)
    circuit.add(I(0))
    circuit.add(Align(0, delay=0))  # Parametrized gate
    circuit.add(X(0))
    circuit.add(Y(0))
    if platform == Galadriel:
        circuit.add(M(0))
    parametrized_experiment_params.extend([[platform.runcard, circuit], [platform.runcard, [circuit, circuit]]])  # type: ignore


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
                        "threshold": [0],
                        "avg_cnt": [1],
                    },
                    "qubit": 0,
                    "measurement": 0,
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
                        "threshold": [0],
                        "avg_cnt": [1],
                    },
                    "qubit": 0,
                    "measurement": 0,
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
                        "threshold": [0],
                        "avg_cnt": [1],
                    },
                    "qubit": 1,
                    "measurement": 0,
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
                        "threshold": [0],
                        "avg_cnt": [1],
                    },
                    "qubit": 1,
                    "measurement": 0,
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
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class MockedSettingsFactory:
    """Class that loads a specific class given an object's name."""

    handlers: dict[str, type[Galadriel]] = {"galadriel": Galadriel}

    @classmethod
    def register(cls, handler_cls: type[Galadriel]):
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


class SauronYokogawa:
    """Test data of the sauron with yokogawa platform."""

    name = "sauron_yokogawa"

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

    yokogawa_gs200_current = {
        RUNCARD.NAME: InstrumentName.YOKOGAWA_GS200,
        RUNCARD.ALIAS: "yokogawa_current",
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.SOURCE_MODE.value: "current",
        Parameter.CURRENT.value: [0.5],
        Parameter.VOLTAGE.value: [0.0],
        Parameter.SPAN.value: ["200mA"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        "dacs": [0],
    }

    yokogawa_gs200_voltage = {
        RUNCARD.NAME: InstrumentName.YOKOGAWA_GS200,
        RUNCARD.ALIAS: "yokogawa_voltage",
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.SOURCE_MODE.value: "voltage",
        Parameter.CURRENT.value: [0.0],
        Parameter.VOLTAGE.value: [0.5],
        Parameter.SPAN.value: ["100mV"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        "dacs": [0],
    }

    rohde_schwarz: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ,
        "alias": "rohde_schwarz",
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    yokogawa_gs200_current_controller = {
        RUNCARD.NAME: InstrumentControllerName.YOKOGAWA_GS200,
        RUNCARD.ALIAS: "yokogawa_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.15",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "yokogawa_current",
                "slot_id": 0,
            }
        ],
    }

    yokogawa_gs200_voltage_controller = {
        RUNCARD.NAME: InstrumentControllerName.YOKOGAWA_GS200,
        RUNCARD.ALIAS: "yokogawa_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.15",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "yokogawa_voltage",
                "slot_id": 0,
            }
        ],
    }

    yokogawa_gs200_controller_wrong_module = {
        RUNCARD.NAME: InstrumentControllerName.YOKOGAWA_GS200,
        RUNCARD.ALIAS: "yokogawa_controller_wrong_module",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.15",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rohde_schwarz",
                "slot_id": 0,
            }
        ],
    }

    instruments = [yokogawa_gs200_current, yokogawa_gs200_voltage, rohde_schwarz]
    instrument_controllers = [
        yokogawa_gs200_current_controller,
        yokogawa_gs200_voltage_controller,
        yokogawa_gs200_controller_wrong_module,
    ]

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "flux_q0", "line": "flux", "nodes": ["q0"]},
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 3.451e09,
                "nodes": ["flux_q0"],
            },
        ],
    }

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "yokogawa_gs200_current_bus",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["yokogawa_current"],
            },
            "port": "flux_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "yokogawa_gs200_voltage_bus",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["yokogawa_voltage"],
            },
            "port": "flux_q0",
            RUNCARD.DISTORTIONS: [],
        },
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class SauronQDevil:
    """Test data of the sauron with yokogawa platform."""

    name = "sauron_qdevil"

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

    qdevil_qdac2 = {
        RUNCARD.NAME: InstrumentName.QDEVIL_QDAC2,
        RUNCARD.ALIAS: "qdac",
        RUNCARD.FIRMWARE: "A.15.10.06",
        Parameter.VOLTAGE.value: [0.0],
        Parameter.SPAN.value: ["low"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        Parameter.LOW_PASS_FILTER.value: ["dc"],
        "dacs": [1],
    }

    rohde_schwarz: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ,
        "alias": "rohde_schwarz",
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    qdevil_qdac2_controller_ip = {
        RUNCARD.NAME: InstrumentControllerName.QDEVIL_QDAC2,
        RUNCARD.ALIAS: "qdac_controller_ip",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.15",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "qdac",
                "slot_id": 0,
            }
        ],
    }

    qdevil_qdac2_controller_usb = {
        RUNCARD.NAME: InstrumentControllerName.QDEVIL_QDAC2,
        RUNCARD.ALIAS: "qdac_controller_usb",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.USB.value,
            CONNECTION.ADDRESS: "ttyUSB0",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "qdac",
                "slot_id": 0,
            }
        ],
    }

    qdevil_qdac2_controller_wrong_module = {
        RUNCARD.NAME: InstrumentControllerName.QDEVIL_QDAC2,
        RUNCARD.ALIAS: "qdac_controller_wrong_module",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.1.15",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rohde_schwarz",
                "slot_id": 0,
            }
        ],
    }

    instruments = [qdevil_qdac2, rohde_schwarz]
    instrument_controllers = [
        qdevil_qdac2_controller_ip,
        qdevil_qdac2_controller_usb,
        qdevil_qdac2_controller_wrong_module,
    ]

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "port_q0", "line": "flux", "nodes": ["q0"]},
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 3.451e09,
                "nodes": ["port_q0"],
            },
        ],
    }

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "qdac_bus",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qdac"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        }
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class SauronQuantumMachines:
    """Test data of the sauron with quantum machines platform."""

    name = "sauron_quantum_machines"

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

    qmm = {
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm",
        RUNCARD.FIRMWARE: "4.30.046.295",
        "address": "192.168.0.1",
        "cluster": "cluster_0",
        "controllers": [
            {
                "name": "con1",
                "analog_outputs": [
                    {"port": 1, "filter": {"feedforward": [0, 0, 0], "feedback": [0, 0, 0]}},
                    {"port": 2},
                    {"port": 3},
                    {"port": 4},
                    {"port": 5},
                    {"port": 6},
                    {"port": 7},
                    {"port": 8},
                    {"port": 9},
                    {"port": 10},
                ],
                "analog_inputs": [{"port": 1}, {"port": 2}],
                "digital_outputs": [{"port": 1}, {"port": 2}, {"port": 3}, {"port": 4}, {"port": 5}],
            }
        ],
        "octaves": [],
        "elements": [
            {
                "bus": "drive_q0",
                "mix_inputs": {
                    "I": {"controller": "con1", "port": 1},
                    "Q": {"controller": "con1", "port": 2},
                    "lo_frequency": 6e9,
                    "mixer_correction": [1.0, 0.0, 0.0, 1.0],
                },
                "intermediate_frequency": 6e9,
            },
            {
                "bus": "readout_q0",
                "mix_inputs": {
                    "I": {"controller": "con1", "port": 3},
                    "Q": {"controller": "con1", "port": 4},
                    "lo_frequency": 6e9,
                    "mixer_correction": [1.0, 0.0, 0.0, 1.0],
                },
                "outputs": {"out1": {"controller": "con1", "port": 1}, "out2": {"controller": "con1", "port": 2}},
                "time_of_flight": 40,
                "smearing": 10,
                "threshold_rotation": 0.5,
                "threshold": 0.09,
                "intermediate_frequency": 6e9,
            },
            {"bus": "flux_q0", "single_input": {"controller": "con1", "port": 5}},
        ],
        "run_octave_calibration": False,
    }

    qmm_with_octave = {
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_with_octave",
        RUNCARD.FIRMWARE: "4.30.046.295",
        "address": "192.168.0.1",
        "cluster": "cluster_0",
        "controllers": [
            {
                "name": "con1",
                "analog_outputs": [
                    {"port": 1, "filter": {"feedforward": [0, 0, 0], "feedback": [0, 0, 0]}},
                    {"port": 2},
                    {"port": 3},
                    {"port": 4},
                    {"port": 5},
                    {"port": 6},
                    {"port": 7},
                    {"port": 8},
                    {"port": 9},
                    {"port": 10},
                ],
                "analog_inputs": [{"port": 1}, {"port": 2}],
                "digital_outputs": [{"port": 1}, {"port": 2}, {"port": 3}, {"port": 4}, {"port": 5}],
            }
        ],
        "octaves": [
            {
                "name": "octave1",
                "port": 11555,
                "connectivity": {"controller": "con1"},
                "loopbacks": {"Synth": "Synth2", "Dmd": "Dmd2LO"},
                "rf_outputs": [
                    {"port": 1, "lo_frequency": 6e9},
                    {"port": 2, "lo_frequency": 6e9},
                    {"port": 3, "lo_frequency": 6e9},
                    {"port": 4, "lo_frequency": 6e9},
                    {"port": 5, "lo_frequency": 6e9},
                ],
                "rf_inputs": [{"port": 1, "lo_frequency": 6e9}, {"port": 2, "lo_frequency": 6e9}],
            }
        ],
        "elements": [
            {
                "bus": "drive_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 1},
                "digital_inputs": {"controller": "con1", "port": 1, "delay": 87, "buffer": 15},
                "digital_outputs": {"controller": "con1", "port": 1},
                "intermediate_frequency": 6e9,
            },
            {
                "bus": "readout_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 2},
                "digital_inputs": {"controller": "con1", "port": 2, "delay": 87, "buffer": 15},
                "rf_outputs": {"octave": "octave1", "port": 1},
                "intermediate_frequency": 6e9,
                "time_of_flight": 40,
                "smearing": 10,
            },
        ],
        "run_octave_calibration": True,
    }

    qmm_with_octave_custom_connectivity = {
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_with_octave_custom_connectivity",
        RUNCARD.FIRMWARE: "4.30.046.295",
        "address": "192.168.0.1",
        "cluster": "cluster_0",
        "controllers": [
            {
                "name": "con1",
                "analog_outputs": [
                    {"port": 1, "filter": {"feedforward": [0, 0, 0], "feedback": [0, 0, 0]}},
                    {"port": 2},
                    {"port": 3},
                    {"port": 4},
                    {"port": 5},
                    {"port": 6},
                    {"port": 7},
                    {"port": 8},
                    {"port": 9},
                    {"port": 10},
                ],
                "analog_inputs": [{"port": 1}, {"port": 2}],
                "digital_outputs": [{"port": 1}, {"port": 2}, {"port": 3}, {"port": 4}, {"port": 5}],
            }
        ],
        "octaves": [
            {
                "name": "octave1",
                "port": 11555,
                "rf_outputs": [
                    {
                        "port": 1,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "port": 1},
                        "q_connection": {"controller": "con1", "port": 2},
                    },
                    {
                        "port": 2,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "port": 3},
                        "q_connection": {"controller": "con1", "port": 4},
                    },
                    {
                        "port": 3,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "port": 5},
                        "q_connection": {"controller": "con1", "port": 6},
                    },
                    {
                        "port": 4,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "port": 7},
                        "q_connection": {"controller": "con1", "port": 8},
                    },
                    {
                        "port": 5,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "port": 9},
                        "q_connection": {"controller": "con1", "port": 10},
                    },
                ],
                "rf_inputs": [{"port": 1, "lo_frequency": 6e9}, {"port": 2, "lo_frequency": 6e9}],
                "if_outputs": [{"controller": "con1", "port": 1}, {"controller": "con1", "port": 2}],
                "loopbacks": {"Synth": "Synth2", "Dmd": "Dmd2LO"},
            }
        ],
        "elements": [
            {
                "bus": "drive_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 1},
                "digital_inputs": {"controller": "con1", "port": 1, "delay": 87, "buffer": 15},
                "digital_outputs": {"controller": "con1", "port": 1},
                "intermediate_frequency": 6e9,
            },
            {
                "bus": "readout_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 2},
                "digital_inputs": {"controller": "con1", "port": 2, "delay": 87, "buffer": 15},
                "rf_outputs": {"octave": "octave1", "port": 1},
                "intermediate_frequency": 6e9,
                "time_of_flight": 40,
                "smearing": 10,
            },
        ],
        "run_octave_calibration": True,
    }

    qmm_with_opx1000 = {
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_with_opx1000",
        RUNCARD.FIRMWARE: "4.30.046.295",
        "address": "192.168.0.1",
        "cluster": "cluster_0",
        "controllers": [
            {
                "name": "con1",
                "type": "opx1000",
                "fems": [
                    {
                        "fem": 1,
                        "analog_outputs": [
                            {"port": 1, "filter": {"feedforward": [0, 0, 0], "feedback": [0, 0, 0]}},
                            {"port": 2},
                            {"port": 3},
                            {"port": 4},
                            {"port": 5},
                            {"port": 6},
                            {"port": 7},
                            {"port": 8},
                        ],
                        "analog_inputs": [{"port": 1}, {"port": 2}],
                        "digital_outputs": [{"port": 1}, {"port": 2}, {"port": 3}, {"port": 4}, {"port": 5}],
                    }
                ],
            }
        ],
        "octaves": [
            {
                "name": "octave1",
                "port": 11555,
                "connectivity": {"controller": "con1", "fem": 1},
                "loopbacks": {"Synth": "Synth2", "Dmd": "Dmd2LO"},
                "rf_outputs": [
                    {"port": 1, "lo_frequency": 6e9},
                    {"port": 2, "lo_frequency": 6e9},
                    {"port": 3, "lo_frequency": 6e9},
                    {"port": 4, "lo_frequency": 6e9},
                    {"port": 5, "lo_frequency": 6e9},
                ],
                "rf_inputs": [{"port": 1, "lo_frequency": 6e9}, {"port": 2, "lo_frequency": 6e9}],
            }
        ],
        "elements": [
            {
                "bus": "drive_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 1},
                "digital_inputs": {"controller": "con1", "port": 1, "delay": 87, "buffer": 15},
                "digital_outputs": {"controller": "con1", "fem": 1, "port": 1},
                "intermediate_frequency": 6e9,
            },
            {
                "bus": "readout_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 2},
                "digital_inputs": {"controller": "con1", "port": 2, "delay": 87, "buffer": 15},
                "rf_outputs": {"octave": "octave1", "port": 1},
                "intermediate_frequency": 6e9,
                "time_of_flight": 40,
                "smearing": 10,
            },
        ],
        "run_octave_calibration": True,
    }

    qmm_controller = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.111",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "qmm",
                "slot_id": 0,
            }
        ],
    }

    qmm_with_octave_controller = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_with_octave_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.111",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "qmm_with_octave",
                "slot_id": 0,
            }
        ],
    }

    qmm_with_octave_custom_connectivity_controller = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_with_octave_custom_connectivity_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.111",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "qmm_with_octave_custom_connectivity",
                "slot_id": 0,
            }
        ],
    }

    qmm_with_opx1000_controller = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_with_opx1000_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.111",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "qmm_with_opx1000",
                "slot_id": 0,
            }
        ],
    }

    rohde_schwarz: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ,
        "alias": "rohde_schwarz",
        RUNCARD.FIRMWARE: "4.30.046.295",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    qmm_controller_wrong_module = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER,
        "alias": "qmm_controller_wrong_module",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.111",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rohde_schwarz",
                "slot_id": 0,
            }
        ],
    }

    instruments = [qmm, qmm_with_octave, qmm_with_octave_custom_connectivity, qmm_with_opx1000, rohde_schwarz]
    instrument_controllers = [
        qmm_controller,
        qmm_with_octave_controller,
        qmm_with_octave_custom_connectivity_controller,
        qmm_with_opx1000_controller,
        qmm_controller_wrong_module,
    ]

    chip: dict[str, Any] = {
        "nodes": [
            {"name": "port", "alias": "port_q0", "line": "flux", "nodes": ["q0"]},
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 3.451e09,
                "nodes": ["port_q0"],
            },
        ],
    }

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "drive_q0",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "readout_q0",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "flux_q0",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "drive_q0_rf",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm_with_octave"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "readout_q0_rf",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm_with_octave"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "drive_q0_rf_custom",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm_with_octave_custom_connectivity"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "readout_q0_rf_custom",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm_with_octave_custom_connectivity"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "drive_q0_opx1000",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm_with_opx1000"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
        {
            RUNCARD.ALIAS: "readout_q0_opx1000",
            RUNCARD.SYSTEM_CONTROL: {
                RUNCARD.NAME: SystemControlName.SYSTEM_CONTROL,
                RUNCARD.INSTRUMENTS: ["qmm_with_opx1000"],
            },
            "port": "port_q0",
            RUNCARD.DISTORTIONS: [],
        },
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.CHIP: chip,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }
