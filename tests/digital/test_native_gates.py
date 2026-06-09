# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math

import numpy as np
import pytest
from qilisdk.core import Parameter

from qililab.digital.native_gates import Rmw


class TestRmw:
    def test_name(self):
        assert Rmw(0, theta=0.0, phase=0.0).name == "Rmw"

    def test_parameter_names(self):
        assert Rmw.PARAMETER_NAMES == ["theta", "phase"]

    def test_qubits(self):
        assert Rmw(3, theta=0.0, phase=0.0).qubits == (3,)

    def test_target_qubits(self):
        assert Rmw(3, theta=0.0, phase=0.0).target_qubits == (3,)

    def test_nqubits(self):
        assert Rmw(0, theta=0.0, phase=0.0).nqubits == 1

    def test_theta_from_float(self):
        assert Rmw(0, theta=1.2, phase=0.0).theta == pytest.approx(1.2)

    def test_phase_from_float(self):
        assert Rmw(0, theta=0.0, phase=0.8).phase == pytest.approx(0.8)

    def test_get_parameters(self):
        gate = Rmw(0, theta=1.2, phase=0.8)
        assert gate.get_parameters() == pytest.approx({"theta": 1.2, "phase": 0.8})

    def test_theta_from_term_returns_real_value(self):
        p = Parameter("theta", value=1.5)
        term = p * 2  # evaluates to 3.0 (float)
        gate = Rmw(0, theta=term, phase=0.0)
        assert gate.theta == pytest.approx(3.0)

    def test_theta_from_term_complex_returns_real_part(self):
        p = Parameter("theta", value=1.5)
        term = p * 2j  # evaluates to 3j (complex)
        gate = Rmw(0, theta=term, phase=0.0)
        assert gate.theta == pytest.approx(0.0)

    def test_phase_from_term_returns_real_value(self):
        p = Parameter("phase", value=0.5)
        term = p * 2  # evaluates to 1.0 (float)
        gate = Rmw(0, theta=0.0, phase=term)
        assert gate.phase == pytest.approx(1.0)

    def test_phase_from_term_complex_returns_real_part(self):
        p = Parameter("phase", value=0.5)
        term = p * 2j  # evaluates to 1j (complex)
        gate = Rmw(0, theta=0.0, phase=term)
        assert gate.phase == pytest.approx(0.0)

    def test_matrix_identity(self):
        matrix = Rmw(0, theta=0.0, phase=0.0).matrix
        assert matrix == pytest.approx(np.eye(2, dtype=complex), abs=1e-12)

    def test_matrix_pi_rotation(self):
        # theta=pi, phase=0 → [[0, -i], [-i, 0]]
        matrix = Rmw(0, theta=math.pi, phase=0.0).matrix
        expected = np.array([[0, -1j], [-1j, 0]], dtype=complex)
        assert matrix == pytest.approx(expected, abs=1e-12)

    def test_matrix_half_pi_phase_pi_over_2(self):
        # theta=pi/2, phase=pi/2 → [[1/√2, -1/√2], [1/√2, 1/√2]]
        matrix = Rmw(0, theta=math.pi / 2, phase=math.pi / 2).matrix
        s = 1 / math.sqrt(2)
        expected = np.array([[s, -s], [s, s]], dtype=complex)
        assert matrix == pytest.approx(expected, abs=1e-12)
