import numpy as np
import pytest

from qilisdk.digital import Circuit
from qilisdk.digital.gates import CZ, RZ, M, Gate

from qililab.digital.circuit_transpiler_passes.add_phases_to_drags_from_rz_and_cz import AddPhasesToDragsFromRZAndCZPass
from qililab.digital.native_gates import Drag
from qililab.settings.digital import DigitalCompilationSettings


@pytest.fixture(name="digital_settings")
def fixture_digital_compilation_settings() -> DigitalCompilationSettings:
    """Fixture that returns an instance of a ``Runcard.GatesSettings`` class."""
    digital_settings_dict = {
        "topology": [(0, 2), (1, 2), (2, 3), (2, 4)],
        "gates": {
            "Drag(0)": [
                {
                    "bus": "drive_q0",
                    "waveform": {
                         "type": "IQDrag",
                         "amplitude": 0.8,
                         "duration": 198,
                         "num_sigmas": 2,
                         "drag_coefficient": 0.8
                    },
                    "phase": 0,
                }
            ],
            "Drag(1)": [
                {
                    "bus": "drive_q1",
                    "waveform": {
                         "type": "IQDrag",
                         "amplitude": 0.8,
                         "duration": 198,
                         "num_sigmas": 2,
                         "drag_coefficient": 0.8
                    },
                    "phase": 0,
                }
            ],
            "M(0)": [
                {
                    "bus": "readout_q0",
                    "waveform": {
                         "type": "Square",
                         "amplitude": 0.8,
                         "duration": 200
                    },
                    "phase": 0,
                }
            ],
            "M(1)": [
                {
                    "bus": "readout_q1",
                    "waveform": {
                         "type": "Square",
                         "amplitude": 0.8,
                         "duration": 200
                    },
                    "phase": 0,
                }
            ],
            "M(2)": [
                {
                    "bus": "readout_q2",
                    "waveform": {
                         "type": "Square",
                         "amplitude": 0.8,
                         "duration": 200
                    },
                    "phase": 0,
                }
            ],
            "CZ(0,1)": [
                {
                    "bus": "flux_q1",
                    "waveform": {
                         "type": "Square",
                         "amplitude": 0.8,
                         "duration": 200,
                    },
                    "phase": 0,
                    "options": {"q0_phase_correction": 0.1, "q1_phase_correction": 0.2}
                }
            ],
            "CZ(0,2)": [
                {
                    "bus": "flux_q2",
                    "waveform": {
                         "type": "Square",
                         "amplitude": 0.8,
                         "duration": 200,
                    },
                    "phase": 0,
                    "options": {"q1_phase_correction": 0.2, "q2_phase_correction": 0.1},
                }
            ],
        },
    }
    return DigitalCompilationSettings.model_validate(digital_settings_dict)


class TestAddPhasesToDragsFromRZsAndCZs:
    def test_run(self, digital_settings: DigitalCompilationSettings):
            """Test that AddPhasesToDragsFromRZAndCZPass behaves as expected"""
            transpile_step = AddPhasesToDragsFromRZAndCZPass(digital_settings)

            # gate list to optimize
            test_gates: list[Gate] = [
                Drag(0, theta=1, phase=1),
                CZ(0, 1),
                RZ(1, phi=0.6),
                M(0),
                RZ(0, phi=0.3),
                Drag(0, theta=3, phase=0),
                CZ(0, 2),
                CZ(1, 0),
                Drag(1, theta=2, phase=-2),
                RZ(1, phi=0),
            ]
            # resulting gate list from optimization
            expected_gates: list[Gate] = [
                Drag(0, theta=1, phase=1),
                CZ(0, 1),
                M(0),
                Drag(0, theta=3, phase=(0-0.1-0.3)),
                CZ(0, 2),
                CZ(1, 0),
                Drag(1, theta=2, phase=(-2-0.2-0.6-0.2)),
            ]

            # create circuit to test function with
            circuit = Circuit(3)
            for gate in test_gates:
                circuit.add(gate)

            # check that lists are the same
            transpiled_circuit = transpile_step.run(circuit)
            for gate_exp, gate_trans in zip(expected_gates, transpiled_circuit.gates):
                assert gate_exp.name == gate_trans.name
                if isinstance(gate_exp, Drag):
                    assert np.isclose(gate_exp.parameters["theta"].value, gate_trans.parameters["theta"].value)
                    assert np.isclose(gate_exp.parameters["phase"].value, gate_trans.parameters["phase"].value)
                assert gate_exp.qubits == gate_trans.qubits
