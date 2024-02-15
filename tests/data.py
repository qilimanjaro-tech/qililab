""" Data to use alongside the test suite. """
# pylint: disable=too-many-lines
import copy
from typing import Any

import numpy as np
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
    Line,
    Parameter,
    PulseShapeName,
    ReferenceClock,
)


class Galadriel:
    """Test data of the galadriel platform."""

    name = "galadriel"

    device_id = 9

    gates_settings: dict[str, Any] = {
        PLATFORM.MINIMUM_CLOCK_TIME: 4,
        PLATFORM.DELAY_BEFORE_READOUT: 0,
        "gates": {
            "M(0)": [
                {
                    "bus": "readout_line_q0_bus",
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
                    "bus": "readout_line_q1_bus",
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
                    "bus": "readout_line_q2_bus",
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
        "buses": {
            "drive_line_q0_bus": {"line": Line.DRIVE, "qubits": [0], "distortions": [], "delay": 0},
            "flux_line_q0_bus": {"line": Line.FLUX, "qubits": [0], "distortions": [], "delay": 0},
            "readout_line_q0_bus": {"line": Line.READOUT, "qubits": [0], "distortions": [], "delay": 0},
            "readout_line_q1_bus": {"line": Line.READOUT, "qubits": [0], "distortions": [], "delay": 0},
            "readout_line_q2_bus": {"line": Line.READOUT, "qubits": [2], "distortions": [], "delay": 0},
        },
    }

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

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "drive_line_q0_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            "channels": [0, None],
        },
        {
            "alias": "readout_line_q0_bus",
            RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_0", "rs_1"],
            "channels": [0, None],
        },
        {
            "alias": "readout_line_q1_bus",
            RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_0", "rs_1"],
            "channels": [1, None],
        },
        {
            "alias": "readout_line_q2_bus",
            RUNCARD.INSTRUMENTS: [f"{InstrumentName.QBLOX_QRM.value}_1"],
            "channels": [0],
        },
        {
            RUNCARD.ALIAS: "flux_line_q0_bus",
            RUNCARD.INSTRUMENTS: [InstrumentName.QBLOX_QCM.value, "rs_0"],
            "channels": [1, None],
        },
    ]

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.GATES_SETTINGS: gates_settings,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
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


class SauronVNA:
    """Test data of the sauron platform."""

    name = "sauron_vna"

    device_id = 9

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

    buses: list[dict[str, Any]] = [
        {
            "alias": "keysight_e5080b_readout_bus",
            "instruments": [InstrumentName.KEYSIGHT_E5080B.value],
            "channels": [None],
        },
        {
            "alias": "agilent_e5071b_readout_bus",
            "instruments": [InstrumentName.AGILENT_E5071B.value],
            "channels": [None],
        },
    ]

    runcard: dict[str, Any] = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class SauronYokogawa:
    """Test data of the sauron with yokogawa platform."""

    name = "sauron_yokogawa"
    device_id = 9

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

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "yokogawa_gs200_current_bus",
            "instruments": ["yokogawa_current"],
            "channels": [None],
        },
        {
            RUNCARD.ALIAS: "yokogawa_gs200_voltage_bus",
            "instruments": ["yokogawa_voltage"],
            "channels": [None],
        },
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class SauronQDevil:
    """Test data for QDevil instruments in sauron platform."""

    name = "sauron_qdevil"
    device_id = 9

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

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "qdac_bus",
            "instruments": ["qdac"],
            "channels": [0],
        }
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }


class SauronQuantumMachines:
    """Test data of the sauron with quantum machines platform."""

    name = "sauron_quantum_machines"
    device_id = 9

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
                    {"port": 1},
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
                    {"port": 1},
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
                "controller": "con1",
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

    instruments = [qmm, qmm_with_octave, rohde_schwarz]
    instrument_controllers = [qmm_controller, qmm_with_octave_controller, qmm_controller_wrong_module]

    buses: list[dict[str, Any]] = [
        {
            RUNCARD.ALIAS: "drive_q0",
            "instruments": ["qmm"],
            "channels": ["drive_q0"],
        },
        {
            RUNCARD.ALIAS: "readout_q0",
            "instruments": ["qmm"],
            "channels": ["readout_q0"],
        },
        {
            RUNCARD.ALIAS: "flux_q0",
            "instruments": ["qmm"],
            "channels": ["flux_q0"],
        },
        {
            RUNCARD.ALIAS: "drive_q0_rf",
            "instruments": ["qmm_with_octave"],
            "channels": ["drive_q0_rf"],
        },
        {
            RUNCARD.ALIAS: "readout_q0_rf",
            "instruments": ["qmm_with_octave"],
            "channels": ["readout_q0_rf"],
        },
    ]

    runcard = {
        RUNCARD.NAME: name,
        RUNCARD.DEVICE_ID: device_id,
        RUNCARD.BUSES: buses,
        RUNCARD.INSTRUMENTS: instruments,
        RUNCARD.INSTRUMENT_CONTROLLERS: instrument_controllers,
    }
