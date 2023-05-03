""" Test Results """
from collections import Counter

import pytest

from qililab.result.counts import Counts


@pytest.fixture(name="psi_plus_counts")
def psi_plus_counts_fixture() -> Counts:
    counts = Counts(n_qubits=2)
    counter = Counter({"00": 500, "01": 12, "10": 12, "11": 500})
    counts._counter = counter
    counts._total_measurements = sum(counter.values())
    return counts


class TestsCounts:
    """Test `Counts` functionalities."""

    def test_str(self, psi_plus_counts: Counts):
        """Test `__str__` method."""
        assert str(psi_plus_counts) == "{'00': 500, '01': 12, '10': 12, '11': 500}"

    def test_verify_state_errors(self, psi_plus_counts: Counts):
        """Test _verify_state checks when adding a new state."""
        bad_n_qubits_state = "001"
        bad_basis_state = "35"

        bad_n_qubits_error_msg = (
            f"State '{bad_n_qubits_state}' can't be added to Counts object with {psi_plus_counts.n_qubits} qubits."
        )
        bad_basis_error_msg = f"A state can only be made of 0s and 1s, got state '{bad_basis_state}'."

        with pytest.raises(IndexError, match=bad_n_qubits_error_msg):
            psi_plus_counts.add_measurement(state=bad_n_qubits_state)

        with pytest.raises(ValueError, match=bad_basis_error_msg):
            psi_plus_counts.add_measurement(state=bad_basis_state)

    def test_bad_merge_error(self, psi_plus_counts: Counts):
        """Test that a Counts object can't be merged with another Counts object with different number of qubits."""
        one_qubit_counts = Counts(n_qubits=1)
        erorr_msg = f"Counts object with {one_qubit_counts.n_qubits} can't be added to Counts object with {psi_plus_counts.n_qubits} qubits."
        with pytest.raises(IndexError, match=erorr_msg):
            psi_plus_counts.add_counts(one_qubit_counts)
