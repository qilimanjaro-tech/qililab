import pytest

from qilisdk.digital import Circuit
from qilisdk.digital.gates import CZ, RZ, M

from qililab.digital.circuit_transpiler_passes.add_phases_to_drags_from_rz_and_cz import AddPhasesToDragsFromRZAndCZPass
from qililab.digital.native_gates import Drag
from qililab.settings.digital import DigitalCompilationSettings


@pytest.fixture(name="digital_settings")
def fixture_digital_compilation_settings() -> DigitalCompilationSettings:
    """Fixture that returns an instance of a ``Runcard.GatesSettings`` class."""
    digital_settings_dict = {
        "minimum_clock_time": 5,
        "delay_before_readout": 0,
        "topology": [(0, 2), (1, 2), (2, 3), (2, 4)],
        "gates": {
            "M(0)": [
                {
                    "bus": "readout_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "Drag(0)": [
                {
                    "bus": "drive_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 198,  # try some non-multiple of clock time (4)
                        "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                    },
                }
            ],
            # random X schedule
            "X(0)": [
                {
                    "bus": "drive_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                    },
                },
                {
                    "bus": "flux_q0",
                    "wait_time": 30,
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                    },
                },
                {
                    "bus": "drive_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "rectangular"},
                    },
                },
                {
                    "bus": "drive_q4",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "gaussian", "num_sigmas": 4},
                    },
                },
            ],
            "M(1)": [
                {
                    "bus": "readout_q1",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "M(2)": [
                {
                    "bus": "readout_q2",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "M(3)": [
                {
                    "bus": "readout_q3",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0.5,
                        "duration": 100,
                        "shape": {"name": "gaussian", "num_sigmas": 2},
                    },
                }
            ],
            "M(4)": [
                {
                    "bus": "readout_q4",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0.5,
                        "duration": 100,
                        "shape": {"name": "gaussian", "num_sigmas": 2},
                    },
                }
            ],
            "CZ(2,3)": [
                {
                    "bus": "flux_q2",
                    "wait_time": 10,
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 90,
                        "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                    },
                },
                # park pulse
                {
                    "bus": "flux_q0",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "rectangular"},
                    },
                },
            ],
            # test couplers
            "CZ(4, 0)": [
                {
                    "bus": "flux_c2",
                    "wait_time": 10,
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 90,
                        "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                    },
                },
                {
                    "bus": "flux_q0",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "rectangular"},
                    },
                },
            ],
            "CZ(0,1)": [
                {
                    "bus": "flux_q1",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                        "options": {"q0_phase_correction": 1, "q1_phase_correction": 2},
                    },
                }
            ],
            "CZ(0,2)": [
                {
                    "bus": "flux_q2",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                        "options": {"q1_phase_correction": 2, "q2_phase_correction": 0},
                    },
                }
            ],
        },
        "buses": {
            "readout_q0": {
                "line": "readout",
                "qubits": [0]
            },
            "readout_q1": {
                "line": "readout",
                "qubits": [1]
            },
            "readout_q2": {
                "line": "readout",
                "qubits": [2]
            },
            "readout_q3": {
                "line": "readout",
                "qubits": [3]
            },
            "readout_q4": {
                "line": "readout",
                "qubits": [4]
            },
            "drive_q0": {
                "line": "drive",
                "qubits": [0]
            },
            "drive_q1": {
                "line": "drive",
                "qubits": [1]
            },
            "drive_q2": {
                "line": "drive",
                "qubits": [2]
            },
            "drive_q3": {
                "line": "drive",
                "qubits": [3]
            },
            "drive_q4": {
                "line": "drive",
                "qubits": [4]
            },
            "flux_q0": {
                "line": "flux",
                "qubits": [0]
            },
            "flux_q1": {
                "line": "flux",
                "qubits": [1]
            },
            "flux_q2": {
                "line": "flux",
                "qubits": [2]
            },
            "flux_q3": {
                "line": "flux",
                "qubits": [3]
            },
            "flux_q4": {
                "line": "flux",
                "qubits": [4]
            },
            "flux_c2": {
                "line": "flux",
                "qubits": [2]
            }
        }
    }
    return DigitalCompilationSettings(**digital_settings_dict)  # type: ignore[arg-type]


class TestAddPhasesToDragsFromRZsAndCZs:
    def test_run(self, digital_settings):
            """Test that add_phases_from_RZs_and_CZs_to_drags behaves as expected"""
            transpile_step = AddPhasesToDragsFromRZAndCZPass(digital_settings)

            # gate list to optimize
            test_gates = [
                Drag(0, 1, 1),
                CZ(0, 1),
                RZ(1, 1),
                M(0),
                RZ(0, 2),
                Drag(0, 3, 3),
                CZ(0, 2),
                CZ(1, 0),
                Drag(1, 2, 3),
                RZ(1, 0),
            ]
            # resulting gate list from optimization
            result_gates = [
                Drag(0, 1, 1),
                CZ(0, 1),
                M(0),
                Drag(0, 3, 0),
                CZ(0, 2),
                CZ(1, 0),
                Drag(1, 2, -2),
            ]

            # create circuit to test function with
            circuit = Circuit(3)
            for gate in test_gates:
                circuit.add(gate)

            # check that lists are the same
            optimized_gates = transpile_step.run(circuit)
            for gate_r, gate_opt in zip(result_gates, optimized_gates):
                assert gate_r.name == gate_opt.name
                assert gate_r.parameters == gate_opt.parameters
                assert gate_r.qubits == gate_opt.qubits
