import numpy as np
import pytest

from qilisdk.digital import Circuit
from qilisdk.digital.gates import CZ, RZ, M, Gate, X

from qililab.digital.circuit_transpiler_passes.add_phases_to_drags_from_rz_and_cz import (
    AddPhasesToRmwFromRZAndCZPass,
)
from qililab.digital.native_gates import Rmw
from qililab.settings.digital import DigitalCompilationSettings


@pytest.fixture(name="digital_settings")
def fixture_digital_compilation_settings() -> DigitalCompilationSettings:
    """
    Fixture that returns an instance of a ``DigitalCompilationSettings`` class.

    Notes on content:
    - CZ(0,1) has per-qubit phase corrections (q0=0.1, q1=0.2).
    - CZ(0,2) deliberately *does not* include "q0_phase_correction" (it has q1/q2),
      which exercises the 'no corrections found' branch in _extract_gate_corrections.
    """
    digital_settings_dict = {
        "topology": [(0, 2), (1, 2), (2, 3), (2, 4)],
        "gates": {
            "Rmw(0)": [
                {
                    "bus": "drive_q0",
                    "waveform": {
                        "type": "IQDrag",
                        "amplitude": 0.8,
                        "duration": 198,
                        "num_sigmas": 2,
                        "drag_coefficient": 0.8,
                    },
                    "phase": 0,
                }
            ],
            "Rmw(1)": [
                {
                    "bus": "drive_q1",
                    "waveform": {
                        "type": "IQDrag",
                        "amplitude": 0.8,
                        "duration": 198,
                        "num_sigmas": 2,
                        "drag_coefficient": 0.8,
                    },
                }
            ],
            "M(0)": [
                {
                    "bus": "readout_q0",
                    "waveform": {"type": "Square", "amplitude": 0.8, "duration": 200},
                }
            ],
            "M(1)": [
                {
                    "bus": "readout_q1",
                    "waveform": {"type": "Square", "amplitude": 0.8, "duration": 200},
                }
            ],
            "M(2)": [
                {
                    "bus": "readout_q2",
                    "waveform": {"type": "Square", "amplitude": 0.8, "duration": 200},
                }
            ],
            "CZ(0,1)": [
                {
                    "bus": "flux_q1",
                    "waveform": {"type": "Square", "amplitude": 0.8, "duration": 200},
                    "options": {"q0_phase_correction": 0.1, "q1_phase_correction": 0.2},
                }
            ],
            # Intentionally mismatched option keys (no q0_phase_correction present):
            "CZ(0,2)": [
                {
                    "bus": "flux_q2",
                    "waveform": {"type": "Square", "amplitude": 0.8, "duration": 200},
                    "options": {"q2_phase_correction": 0.1},
                }
            ],
        },
    }
    return DigitalCompilationSettings.model_validate(digital_settings_dict)


class TestAddPhasesToRmwFromRZAndCZ:
    def test_run_updated_behavior(self, digital_settings: DigitalCompilationSettings):
        """
        End-to-end test updated to the new semantics:
        - phases from RZ and CZ are ACCUMULATED and ADDED to Rmw.phase
        - RZ gates are removed (virtualized)
        - shift/frame is NOT reset after an Rmw
        - CZ(0,2) has no usable corrections, exercises the 'None' branch
        """
        transpile_step = AddPhasesToRmwFromRZAndCZPass(digital_settings)

        # Input gate list
        test_gates: list[Gate] = [
            Rmw(0, theta=1, phase=1),
            CZ(0, 1),
            RZ(1, phi=0.6),
            M(0),
            RZ(0, phi=0.3),
            Rmw(0, theta=3, phase=0),
            CZ(0, 2),      # no usable corrections (None branch)
            CZ(1, 0),      # should pick up corrections for q1 and q0 (0.2 and 0.1)
            Rmw(1, theta=2, phase=-2),
            RZ(1, phi=0),  # zero rotation; virtualized away
        ]

        # Expected list after transpilation
        #  - First Rmw(0): unchanged (no prior shift)
        #  - CZ(0,1): forwarded; shift[q0]+=0.1, shift[q1]+=0.2
        #  - RZ(1,0.6): shift[q1]+=0.6
        #  - M(0): forwarded
        #  - RZ(0,0.3): shift[q0]+=0.3 -> shift[q0]=0.4
        #  - Rmw(0): phase = 0 + 0.4 = +0.4
        #  - CZ(0,2): no corrections (options missing q0 key) => no shift change
        #  - CZ(1,0): consumes CZ(0,1) settings (ordered or symmetric), shift[q1]+=0.2, shift[q0]+=0.1
        #              so shift[q1]=0.2+0.6+0.2 = 1.0; shift[q0]=0.4+0.1 = 0.5
        #  - Rmw(1): phase = -2 + 1.0 = -1.0
        expected_gates: list[Gate] = [
            Rmw(0, theta=1, phase=1),
            CZ(0, 1),
            M(0),
            Rmw(0, theta=3, phase=+0.4),
            CZ(0, 2),
            CZ(1, 0),
            Rmw(1, theta=2, phase=-1.0),
        ]

        circuit = Circuit(3)
        for g in test_gates:
            circuit.add(g)

        transpiled = transpile_step.run(circuit)
        assert len(transpiled.gates) == len(expected_gates), "RZ must be virtualized/removed"

        for g_exp, g_tr in zip(expected_gates, transpiled.gates):
            assert g_exp.name == g_tr.name
            assert g_exp.qubits == g_tr.qubits
            if isinstance(g_exp, Rmw):
                assert np.isclose(g_exp.parameters["theta"].value, g_tr.parameters["theta"].value)
                assert np.isclose(g_exp.parameters["phase"].value, g_tr.parameters["phase"].value)

    def test_frame_persists_across_multiple_Rmw(self, digital_settings: DigitalCompilationSettings):
        """
        A single RZ before two consecutive Rmw on the same qubit should add the
        same (persisting) phase to both Rmw pulses because the frame is not reset.
        """
        step = AddPhasesToRmwFromRZAndCZPass(digital_settings)
        c = Circuit(1)
        c.add(RZ(0, phi=0.5))
        c.add(Rmw(0, theta=1.0, phase=0.0))
        c.add(Rmw(0, theta=1.0, phase=0.0))

        out = step.run(c)
        # Expect two gates (both Rmw), both with phase +0.5
        assert len(out.gates) == 2
        assert all(isinstance(g, Rmw) for g in out.gates)
        phases = [g.parameters["phase"].value for g in out.gates]
        assert np.allclose(phases, [0.5, 0.5])

    def test_cz_corrections_applied_to_both_qubits(self, digital_settings: DigitalCompilationSettings):
        """
        Put CZ(0,1) first, then Rmw on both 0 and 1.
        The pass should add +0.1 to q0 and +0.2 to q1 phases (from settings).
        """
        step = AddPhasesToRmwFromRZAndCZPass(digital_settings)
        c = Circuit(2)
        c.add(CZ(0, 1))             # shift[q0]+=0.1, shift[q1]+=0.2
        c.add(Rmw(0, theta=0.1, phase=0.0))
        c.add(Rmw(1, theta=0.1, phase=0.0))

        out = step.run(c)
        assert [g.name for g in out.gates] == ["CZ", "Rmw", "Rmw"]
        # Check applied phases
        p0 = out.gates[1].parameters["phase"].value
        p1 = out.gates[2].parameters["phase"].value
        assert np.isclose(p0, 0.1)  # q0
        assert np.isclose(p1, 0.2)  # q1

    def test_cz_without_corrections_is_noop(self, digital_settings: DigitalCompilationSettings):
        """
        CZ(0,2) in the fixture does NOT include 'q0_phase_correction' in options.
        That should exercise the None-return branch and thus NOT change any shift.
        """
        step = AddPhasesToRmwFromRZAndCZPass(digital_settings)
        c = Circuit(3)
        c.add(CZ(0, 2))  # no usable corrections for control qubit 0
        c.add(Rmw(0, theta=0.3, phase=0.05))
        c.add(Rmw(2, theta=0.3, phase=-0.07))

        out = step.run(c)
        assert [g.name for g in out.gates] == ["CZ", "Rmw", "Rmw"]
        # Phases must be unchanged (no shift applied from that CZ)
        assert np.isclose(out.gates[1].parameters["phase"].value, 0.05)
        assert np.isclose(out.gates[2].parameters["phase"].value, -0.07 + 0.1)

    def test_trailing_rz_is_removed_and_m_is_untouched(self, digital_settings: DigitalCompilationSettings):
        """
        RZ gates must be virtualized (not present in the output); M passes through.
        Also include an RZ with phi=0 to cover that no-op path.
        """
        step = AddPhasesToRmwFromRZAndCZPass(digital_settings)
        c = Circuit(3)
        c.add(RZ(2, phi=0.5))  # no following Rmw on q2; should be removed
        c.add(M(2))
        c.add(RZ(2, phi=0.0))  # zero angle RZ; still virtualized

        out = step.run(c)
        # Only the measurement should remain
        assert len(out.gates) == 1
        assert isinstance(out.gates[0], M)
        assert out.gates[0].qubits == (2,)

    def test_unsupported_gate_raises(self, digital_settings: DigitalCompilationSettings):
        step = AddPhasesToRmwFromRZAndCZPass(digital_settings)
        c = Circuit(1)
        c.add(X(0))  # not in (RZ, Rmw, CZ, M)

        with pytest.raises(ValueError, match="Unsupported gate X"):
            step.run(c)
