"""Data to use alongside the test suite."""

from typing import Any

from qililab.constants import CONNECTION, INSTRUMENTCONTROLLER, PLATFORM, RUNCARD, AWGTypes
from qililab.typings.enums import (
    AcquireTriggerMode,
    ConnectionName,
    DistortionState,
    InstrumentControllerName,
    InstrumentName,
    IntegrationMode,
    Parameter,
    VNASweepTypes,
)


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    digital_compilation_settings: dict[str, Any] = {
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BEFORE_READOUT: 0,
        "topology": [[0, 2], [1, 2], [2, 3], [2, 4]],
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
            "M(2)": [
                {
                    "bus": "feedline_input_output_bus_2",
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
                        "options": {"q0_phase_correction": 0.1, "q1_phase_correction": 0.2},
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
                        "options": {"q0_phase_correction": 0.1, "q2_phase_correction": 0.2},
                    },
                }
            ],
        },
        "buses": {
            "drive_line_q0_bus": {
                "line": "drive",
                "qubits": [0],
                "distortions": [
                    {"name": "lfilter", "a": [1.0, 0.0, 1.0], "auto_norm": True, "b": [0.5, 0.5], "norm_factor": 1.0}
                ],
            },
            "drive_line_q1_bus": {"line": "drive", "qubits": [1]},
            "drive_line_q2_bus": {"line": "drive", "qubits": [1]},
            "feedline_input_output_bus": {
                "line": "readout",
                "qubits": [0],
                "delay": 0,
                "distortions": [],
            },
            "feedline_input_output_bus_1": {
                "line": "readout",
                "qubits": [1],
                "delay": 0,
                "distortions": [],
            },
            "feedline_input_output_bus_2": {
                "line": "readout",
                "qubits": [2],
                "delay": 0,
                "distortions": [],
            },
            "flux_line_q0_bus": {"line": "flux", "qubits": [0]},
        },
    }

    analog_compilation_settings: dict[str, Any] = {
        "flux_control_topology": [
            {"flux": "phix_q0", "bus": "flux_line_q0_bus"},
            {"flux": "phiz_q0", "bus": "flux_line_q0_bus"},
            {"flux": "phix_q1", "bus": "drive_line_q0_bus"},
            {"flux": "phiz_q1", "bus": "drive_line_q0_bus"},
            {"flux": "phix_c0_1", "bus": "flux_line_q0_bus"},
            {"flux": "phiz_c0_1", "bus": "flux_line_q0_bus"},
        ]
    }

    qblox_qcm_0: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QCM.value,
        "alias": InstrumentName.QBLOX_QCM.value,
        AWGTypes.OUT_OFFSETS: [0, 0, 0.7, 0.8],
        AWGTypes.FILTERS:[
            {   "output_id": 0,
                Parameter.EXPONENTIAL_AMPLITUDE.value: 0.7,
                Parameter.EXPONENTIAL_TIME_CONSTANT.value: 200,
                Parameter.EXPONENTIAL_STATE.value: [DistortionState.ENABLED.value],
                Parameter.FIR_COEFF.value: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
                Parameter.FIR_STATE.value: DistortionState.ENABLED.value,
            },
            {   "output_id": 1,
                Parameter.EXPONENTIAL_AMPLITUDE.value: 1,
                Parameter.EXPONENTIAL_TIME_CONSTANT.value: 20,
                Parameter.EXPONENTIAL_STATE.value: [DistortionState.BYPASSED.value],
                Parameter.FIR_COEFF.value: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
                Parameter.FIR_STATE.value: DistortionState.ENABLED.value,
            },
            {   "output_id": 3,
                Parameter.EXPONENTIAL_AMPLITUDE: 0.1,
                Parameter.EXPONENTIAL_TIME_CONSTANT: 2000,
                Parameter.EXPONENTIAL_STATE: [DistortionState.DELAY_COMP.value],
                Parameter.FIR_COEFF: None,
                Parameter.FIR_STATE: DistortionState.BYPASSED.value,
            },
        ],
        AWGTypes.AWG_SEQUENCERS: [
            {
                "identifier": 0,
                "outputs": [0, 1],
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0.34,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: True,
            },
            {
                "identifier": 1,
                "outputs": [0],
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
                "identifier": 2,
                "outputs": [1],
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
                "identifier": 3,
                "outputs": [2],
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
                "identifier": 4,
                "outputs": [3],
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
        "name": InstrumentName.QCMRF.value,
        "alias": InstrumentName.QCMRF.value,
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
                "outputs": [0],
                "intermediate_frequency": 20000000,
                "gain_i": 0.001,
                "gain_q": 0.02,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_i": 0,
                "offset_q": 0,
                "hardware_modulation": True,
            },
            {
                "identifier": 1,
                "outputs": [1],
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
        "name": InstrumentName.QRMRF.value,
        "alias": InstrumentName.QRMRF.value,
        "out0_in0_lo_freq": 3e9,
        "out0_in0_lo_en": True,
        "out0_att": 34,
        "in0_att": 28,
        "out0_offset_path0": 0.123,
        "out0_offset_path1": 1.234,
        "awg_sequencers": [
            {
                "identifier": 0,
                "outputs": [0],
                "threshold": 0.5,
                "threshold_rotation": 45.0,
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

    qblox_qrm_0: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QRM.value,
        "alias": f"{InstrumentName.QBLOX_QRM.value}_0",
        AWGTypes.OUT_OFFSETS: [0.123, 1.23],
        AWGTypes.AWG_SEQUENCERS: [
            {
                "identifier": 0,
                "outputs": [0, 1],
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
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
            {
                "identifier": 1,
                "outputs": [0, 1],
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
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
        ],
    }

    qblox_qrm_1: dict[str, Any] = {
        "name": InstrumentName.QBLOX_QRM.value,
        "alias": f"{InstrumentName.QBLOX_QRM.value}_1",
        AWGTypes.OUT_OFFSETS: [0.123, 1.23],
        AWGTypes.AWG_SEQUENCERS: [
            {
                "identifier": 0,
                "outputs": [0],
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
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
        ],
    }

    qblox_qblox_cluster_controller: dict[str, Any] = {
        "name": "qblox_cluster",
        "alias": "qblox_qblox_cluster_controller",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.2"
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.QBLOX_QCM.value,
                "slot_id": 15,
            }
        ],
        INSTRUMENTCONTROLLER.RESET: True,
        "reference_clock": "internal",

    }

    rohde_schwarz_controller_0: dict[str, Any] = {
        "name": "rohde_schwarz",
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
        "name": "rohde_schwarz",
        "alias": "rs_0",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    rohde_schwarz_controller_1: dict[str, Any] = {
        "name": "rohde_schwarz",
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
        "name": InstrumentName.ROHDE_SCHWARZ.value,
        "alias": "rs_1",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 3.351e09,
        Parameter.RF_ON.value: True,
    }

    attenuator_controller_0: dict[str, Any] = {
        "name": InstrumentControllerName.MINI_CIRCUITS.value,
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
        "name": InstrumentName.MINI_CIRCUITS.value,
        "alias": "attenuator",
        Parameter.ATTENUATION.value: 30,
    }

    keithley_2400_controller_0: dict[str, Any] = {
        "name": InstrumentControllerName.KEITHLEY2400.value,
        "alias": "keithley_2400_controller_0",
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.113",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": InstrumentName.KEITHLEY2400.value,
                "slot_id": 0,
            }
        ],
        INSTRUMENTCONTROLLER.RESET: True,
    }

    keithley_2400: dict[str, Any] = {
        "name": InstrumentName.KEITHLEY2400.value,
        "alias": InstrumentControllerName.KEITHLEY2400.value,
        Parameter.VOLTAGE.value: 2.0,
        "mode": "VOLT",
    }

    keithley_2600_controller_0: dict[str, Any] = {
        "name": InstrumentControllerName.KEITHLEY2600.value,
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
        "name": InstrumentName.KEITHLEY2600.value,
        "alias": InstrumentControllerName.KEITHLEY2600.value,
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
        keithley_2400,
        keithley_2600,
    ]

    instrument_controllers: list[dict] = [
        qblox_qblox_cluster_controller,
        rohde_schwarz_controller_0,
        rohde_schwarz_controller_1,
        attenuator_controller_0,
        keithley_2400_controller_0,
        keithley_2600_controller_0,
    ]

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "drive_line_q0_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            RUNCARD.CHANNELS: [0, None],
            "distortions": [
                {"name": "lfilter", "a": [1.0, 0.0, 1.0], "auto_norm": True, "b": [0.5, 0.5], "norm_factor": 1.0}
            ],
        },
        {RUNCARD.ALIAS: "drive_line_q1_bus", RUNCARD.INSTRUMENTS: [InstrumentName.QCMRF.value], RUNCARD.CHANNELS: [0]},
        {RUNCARD.ALIAS: "drive_line_q2_bus", RUNCARD.INSTRUMENTS: [InstrumentName.QCMRF.value], RUNCARD.CHANNELS: [1]},
        {
            "alias": "feedline_input_output_bus",
            RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_0", "rs_1"],
            RUNCARD.CHANNELS: [0, None],
        },
        {
            "alias": "feedline_input_output_bus_1",
            RUNCARD.INSTRUMENTS: [f"{InstrumentName.QRMRF.value}"],
            RUNCARD.CHANNELS: [0],
        },
        {
            "alias": "feedline_input_output_bus_2",
            RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_1"],
            RUNCARD.CHANNELS: [0],
        },
        {
            RUNCARD.ALIAS: "flux_line_q0_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            RUNCARD.CHANNELS: [1, None],
        },
        {
            RUNCARD.ALIAS: "flux_line_q1_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            RUNCARD.CHANNELS: [2, None],
        },
        {
            RUNCARD.ALIAS: "flux_line_q2_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            RUNCARD.CHANNELS: [3, None],
        },
        {
            RUNCARD.ALIAS: "flux_line_q3_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            RUNCARD.CHANNELS: [4, None],
        },
        {
            RUNCARD.ALIAS: "flux_line_too_many_instr",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, InstrumentName.QBLOX_QCM.value],
            RUNCARD.CHANNELS: [1, 4],
        },
    ]

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
        RUNCARD.BUSES: buses,
        RUNCARD.DIGITAL: digital_compilation_settings,
        RUNCARD.ANALOG: analog_compilation_settings,
    }


class SauronYokogawa:
    """Test data of the sauron with yokogawa platform."""

    name = "sauron_yokogawa"

    yokogawa_gs200_current = {
        RUNCARD.NAME: InstrumentName.YOKOGAWA_GS200,
        RUNCARD.ALIAS: "yokogawa_current",
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
        Parameter.SOURCE_MODE.value: "voltage",
        Parameter.CURRENT.value: [0.0],
        Parameter.VOLTAGE.value: [0.5],
        Parameter.SPAN.value: ["100mV"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        "dacs": [0],
    }

    rohde_schwarz: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ.value,
        "alias": "rohde_schwarz",
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

    buses: list[dict[str, Any]] = [
        {RUNCARD.ALIAS: "yokogawa_gs200_current_bus", RUNCARD.INSTRUMENTS: ["yokogawa_current"], RUNCARD.CHANNELS: [0]},
        {RUNCARD.ALIAS: "yokogawa_gs200_voltage_bus", RUNCARD.INSTRUMENTS: ["yokogawa_voltage"], RUNCARD.CHANNELS: [0]},
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
        RUNCARD.BUSES: buses,
    }


class SauronSpiRack:
    """Test data of the sauron with spi rack platform."""

    name = "sauron_spi_rack"

    spi_rack = {
        RUNCARD.NAME: InstrumentName.QBLOX_S4G,
        RUNCARD.ALIAS: "S4g_1",
        Parameter.CURRENT.value: [0.0],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        Parameter.SPAN.value: ["range_min_bi"],
        "dacs": [1],
    }

    rohde_schwarz: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ.value,
        "alias": "rohde_schwarz",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    spi_rack_controller_usb = {
        RUNCARD.NAME: InstrumentControllerName.QBLOX_SPIRACK,
        RUNCARD.ALIAS: "spi_controller_usb",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.USB.value,
            CONNECTION.ADDRESS: "ttyUSB0",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "S4g_1",
                "slot_id": 1,
            }
        ],
    }

    spi_rack_controller_wrong_module = {
        RUNCARD.NAME: InstrumentControllerName.QBLOX_SPIRACK,
        RUNCARD.ALIAS: "spi_controller_wrong_module",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.USB.value,
            CONNECTION.ADDRESS: "ttyUSB0",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rohde_schwarz",
                "slot_id": 1,
            }
        ],
    }

    instruments = [spi_rack, rohde_schwarz]
    instrument_controllers = [
        spi_rack_controller_usb,
        spi_rack_controller_wrong_module,
    ]

    buses: list[dict[str, Any]] = [{RUNCARD.ALIAS: "spi_bus", RUNCARD.INSTRUMENTS: ["S4g_1"], RUNCARD.CHANNELS: [1]}]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
        RUNCARD.BUSES: buses,
    }


class SauronQDevil:
    """Test data of the sauron with yokogawa platform."""

    name = "sauron_qdevil"

    qdevil_qdac2 = {
        RUNCARD.NAME: InstrumentName.QDEVIL_QDAC2,
        RUNCARD.ALIAS: "qdac",
        Parameter.VOLTAGE.value: [0.0],
        Parameter.SPAN.value: ["low"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        Parameter.LOW_PASS_FILTER.value: ["dc"],
        "dacs": [1],
    }

    rohde_schwarz: dict[str, Any] = {
        "name": InstrumentName.ROHDE_SCHWARZ.value,
        "alias": "rohde_schwarz",
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

    buses: list[dict[str, Any]] = [{RUNCARD.ALIAS: "qdac_bus", RUNCARD.INSTRUMENTS: ["qdac"], RUNCARD.CHANNELS: [1]}]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
        RUNCARD.BUSES: buses,
    }


class SauronVNA:
    """Test data of the sauron platform."""

    name = "sauron_vna"

    keysight_e5080b_controller: dict[str, Any] = {
        "name": InstrumentControllerName.KEYSIGHT_E5080B,
        "alias": InstrumentControllerName.KEYSIGHT_E5080B.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            "name": ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "169.254.150.105",
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
    }

    instruments = [keysight_e5080b]
    instrument_controllers = [
        keysight_e5080b_controller,
    ]

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "keysight_e5080b_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.KEYSIGHT_E5080B.value],
            RUNCARD.CHANNELS: [0],
        },
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
        RUNCARD.BUSES: buses,
    }


class SauronQuantumMachines:
    """Test data of the sauron with quantum machines platform."""

    name = "sauron_quantum_machines"

    qmm = {
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER.value,
        "alias": "qmm",
        "address": "192.168.0.1",
        "cluster": "cluster_0",
        "controllers": [
            {
                "name": "con1",
                "analog_outputs": [
                    {"port": 1, "filter": {"feedforward": [0, 0, 0], "feedback": [0, 0, 0]}, "shareable": True},
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
                "identifier": "drive_q0",
                "mix_inputs": {
                    "I": {"controller": "con1", "port": 1},
                    "Q": {"controller": "con1", "port": 2},
                    "lo_frequency": 6e9,
                    "mixer_correction": [1.0, 0.0, 0.0, 1.0],
                },
                "intermediate_frequency": 6e9,
            },
            {
                "identifier": "readout_q0",
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
            {"identifier": "flux_q0", "single_input": {"controller": "con1", "port": 5}},
        ],
        "run_octave_calibration": False,
    }

    qmm_with_octave = {
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER.value,
        "alias": "qmm_with_octave",
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
                "identifier": "drive_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 1},
                "digital_inputs": {"controller": "con1", "port": 1, "delay": 87, "buffer": 15},
                "digital_outputs": {"controller": "con1", "port": 1},
                "intermediate_frequency": 6e9,
            },
            {
                "identifier": "readout_q0_rf",
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
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER.value,
        "alias": "qmm_with_octave_custom_connectivity",
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
                "identifier": "drive_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 1},
                "digital_inputs": {"controller": "con1", "port": 1, "delay": 87, "buffer": 15},
                "digital_outputs": {"controller": "con1", "port": 1},
                "intermediate_frequency": 6e9,
            },
            {
                "identifier": "readout_q0_rf",
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
        "name": InstrumentName.QUANTUM_MACHINES_CLUSTER.value,
        "alias": "qmm_with_opx1000",
        "address": "192.168.0.1",
        "cluster": "cluster_0",
        "controllers": [
            {
                "name": "con1",
                "type": "opx1000",
                "fems": [
                    {
                        "fem": 1,
                        "shareable": True,
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
                    {
                        "port": 1,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "fem": 1, "port": 1},
                        "q_connection": {"controller": "con1", "fem": 1, "port": 2},
                    },
                    {
                        "port": 2,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "fem": 1, "port": 3},
                        "q_connection": {"controller": "con1", "fem": 1, "port": 4},
                    },
                    {
                        "port": 3,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "fem": 1, "port": 5},
                        "q_connection": {"controller": "con1", "fem": 1, "port": 6},
                    },
                    {
                        "port": 4,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "fem": 1, "port": 7},
                        "q_connection": {"controller": "con1", "fem": 1, "port": 8},
                    },
                    {
                        "port": 5,
                        "lo_frequency": 6e9,
                        "i_connection": {"controller": "con1", "fem": 1, "port": 9},
                        "q_connection": {"controller": "con1", "fem": 1, "port": 10},
                    },
                ],
                "rf_inputs": [{"port": 1, "lo_frequency": 6e9}, {"port": 2, "lo_frequency": 6e9}],
            }
        ],
        "elements": [
            {
                "identifier": "drive_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 1},
                "digital_inputs": {"controller": "con1", "port": 1, "delay": 87, "buffer": 15},
                "digital_outputs": {"controller": "con1", "fem": 1, "port": 1},
                "intermediate_frequency": 6e9,
            },
            {
                "identifier": "readout_q0_rf",
                "rf_inputs": {"octave": "octave1", "port": 2},
                "digital_inputs": {"controller": "con1", "port": 2, "delay": 87, "buffer": 15},
                "rf_outputs": {"octave": "octave1", "port": 1},
                "intermediate_frequency": 6e9,
                "time_of_flight": 40,
                "smearing": 10,
            },
            {"identifier": "flux_q0", "single_input": {"controller": "con1", "fem": 1, "port": 5}},
        ],
        "run_octave_calibration": True,
    }

    qmm_controller = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER.value,
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
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER.value,
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
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER.value,
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
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER.value,
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
        "name": InstrumentName.ROHDE_SCHWARZ.value,
        "alias": "rohde_schwarz",
        Parameter.POWER.value: 15,
        Parameter.LO_FREQUENCY.value: 7.24730e09,
        Parameter.RF_ON.value: True,
    }

    qmm_controller_wrong_module = {
        "name": InstrumentControllerName.QUANTUM_MACHINES_CLUSTER.value,
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

    buses: list[dict[str, Any]] = [
        {RUNCARD.ALIAS: "drive_q0", RUNCARD.INSTRUMENTS: ["qmm"], RUNCARD.CHANNELS: ["drive_q0"]},
        {RUNCARD.ALIAS: "readout_q0", RUNCARD.INSTRUMENTS: ["qmm"], RUNCARD.CHANNELS: ["readout_q0"]},
        {RUNCARD.ALIAS: "flux_q0", RUNCARD.INSTRUMENTS: ["qmm"], RUNCARD.CHANNELS: ["flux_q0"]},
        {RUNCARD.ALIAS: "drive_q0_rf", RUNCARD.INSTRUMENTS: ["qmm_with_octave"], RUNCARD.CHANNELS: ["drive_q0_rf"]},
        {RUNCARD.ALIAS: "readout_q0_rf", RUNCARD.INSTRUMENTS: ["qmm_with_octave"], RUNCARD.CHANNELS: ["readout_q0_rf"]},
        {
            RUNCARD.ALIAS: "drive_q0_rf_custom",
            RUNCARD.INSTRUMENTS: ["qmm_with_octave_custom_connectivity"],
            RUNCARD.CHANNELS: ["drive_q0_rf"],
        },
        {
            RUNCARD.ALIAS: "readout_q0_rf_custom",
            RUNCARD.INSTRUMENTS: ["qmm_with_octave_custom_connectivity"],
            RUNCARD.CHANNELS: ["readout_q0_rf"],
        },
        {
            RUNCARD.ALIAS: "drive_q0_opx1000",
            RUNCARD.INSTRUMENTS: ["qmm_with_opx1000"],
            RUNCARD.CHANNELS: ["drive_q0_rf"],
        },
        {
            RUNCARD.ALIAS: "readout_q0_opx1000",
            RUNCARD.INSTRUMENTS: ["qmm_with_opx1000"],
            RUNCARD.CHANNELS: ["readout_q0_rf"],
        },
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }
