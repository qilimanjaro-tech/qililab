""" Test Results """
from collections import Counter

import numpy as np
import pytest

from qililab.extra.quantum_machines import QuantumMachinesMeasurementResult
from qililab.result.counts import Counts
from qililab.result.qprogram import QProgramResults
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult


@pytest.fixture(name="psi_plus_counts")
def psi_plus_counts_fixture() -> Counts:
    """Fixture of counts measuring the Psi+ Bell state"""
    counts = Counts(n_qubits=2)
    counter = Counter({"00": 500, "01": 12, "10": 12, "11": 500})
    counts._counter = counter
    counts._total_measurements = sum(counter.values())
    return counts


@pytest.fixture(name="phi_plus_counts")
def phi_plus_counts_fixture() -> Counts:
    """Fixture of counts measuring the Phi+ Bell state"""
    counts = Counts(n_qubits=2)
    counter = Counter({"00": 12, "01": 500, "10": 500, "11": 12})
    counts._counter = counter
    counts._total_measurements = sum(counter.values())
    return counts


@pytest.fixture(name="qblox_qprogram_results_probs")
def fixture_raw_measurement_data() -> QProgramResults:
    """Fixture to obtain proabilities from a QProgramResult"""
    results = QProgramResults()
    thresholds_q0 = [1.0, 1.0, 0.0, 1.0, 0.0]
    thresholds_q1 = [0.0, 1.0, 0.0, 0.0, 1.0]
    for th_q0, th_q1 in zip(thresholds_q0, thresholds_q1):
        results.append_result(
            bus="readout_q0",
            result=QbloxMeasurementResult(
                bus="readout_q0",
                raw_measurement_data={"bins": {"integration": {"path0": [0], "path1": [0]}, "threshold": [th_q0]}},
            ),
        )
        results.append_result(
            bus="readout_q1",
            result=QbloxMeasurementResult(
                bus="readout_q1",
                raw_measurement_data={"bins": {"integration": {"path0": [0], "path1": [0]}, "threshold": [th_q1]}},
            ),
        )
    return results


@pytest.fixture(name="qm_qprogram_results_probs")
def fixture_raw_measurement_data_qm() -> QProgramResults:
    """Fixture to obtain proabilities from a QProgramResult"""
    results = QProgramResults()

    res_0 = QuantumMachinesMeasurementResult(
        bus="readout", I=np.array([0.2, 1.3, 0.07, 1.0, 0.7]), Q=np.array([0.5, 1.4, 0.6, 1.02, 0.1])
    )
    res_1 = QuantumMachinesMeasurementResult(
        bus="readout", I=np.array([0.76, 1.2, 1.8, 0.4, 0.9]), Q=np.array([0.9, 1.0, 0.46, 2.6, 0.97])
    )
    res_0.set_classification_threshold(0.4)
    res_1.set_classification_threshold(0.5)

    results.append_result(bus="readout_q0", result=res_0)
    results.append_result(bus="readout_q1", result=res_1)

    return results


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

    def test_iadd(self, psi_plus_counts: Counts, phi_plus_counts: Counts):
        """Test `__iadd__` method."""
        psi_plus_counts += phi_plus_counts
        for count in psi_plus_counts.as_dict().values():
            assert count == 512

    def test_add_measurement(self, psi_plus_counts: Counts):
        """Test `add_measurement` method."""
        total_measurements_before = psi_plus_counts.total_measurements
        measurements_10_before = psi_plus_counts.as_dict()["10"]
        psi_plus_counts.add_measurement("10")
        assert psi_plus_counts.total_measurements == total_measurements_before + 1
        assert psi_plus_counts.as_dict()["10"] == measurements_10_before + 1


class TestProbabilitiesWithQProgram:
    """Class to test the `probabilities` method."""

    @pytest.mark.parametrize(
        "bus_mapping, expected_probs",
        [
            (None, {"00": 0.2, "01": 0.2, "10": 0.4, "11": 0.2}),
            (["readout_q1", "readout_q0"], {"00": 0.2, "01": 0.4, "10": 0.2, "11": 0.2}),
        ],
    )
    def test_probabilities_with_qblox(self, qblox_qprogram_results_probs: QProgramResults, bus_mapping, expected_probs):
        """Test probabilities are computed correctly with and without qubit mapping"""
        assert Counts.from_qprogram(qblox_qprogram_results_probs, bus_mapping).probabilities() == expected_probs

    @pytest.mark.parametrize(
        "bus_mapping, expected_probs",
        [
            (None, {"00": 0.0, "01": 0.4, "10": 0.2, "11": 0.4}),
            (["readout_q1", "readout_q0"], {"00": 0.0, "01": 0.2, "10": 0.4, "11": 0.4}),
        ],
    )
    def test_probabilities_with_quantum_machines(
        self, qm_qprogram_results_probs: QProgramResults, bus_mapping, expected_probs
    ):
        """Test probabilities are computed correctly with and without qubit mapping"""
        assert Counts.from_qprogram(qm_qprogram_results_probs, bus_mapping).probabilities() == expected_probs

    def test_probabilities_raises_empty(self):
        """Test an error is raised when the `qprogram_results` is empty"""
        qp_results = QProgramResults()
        with pytest.raises(ValueError) as empty_error:
            Counts.from_qprogram(qp_results)
        (msg,) = empty_error.value.args
        assert msg == f"Can not obtain counts with no measurments, {qp_results.__class__} empty"

    @pytest.mark.parametrize(
        "bus_mapping", [[], ["readout_q1", "readout_q1"], ["readout_q0", "readout_q1", "readout_q2"]]
    )
    def test_probabilities_raises_len_missmatch(self, qblox_qprogram_results_probs: QProgramResults, bus_mapping):
        """Test an error is raised when a mapping is not specified for all qubits"""
        n_qubits = len(qblox_qprogram_results_probs.results)
        unique_mapping = set(bus_mapping)
        with pytest.raises(ValueError) as len_missmatch:
            Counts.from_qprogram(qblox_qprogram_results_probs, bus_mapping)
        (msg,) = len_missmatch.value.args
        assert (
            msg
            == f"Expected mapping for all qubits. Results have {n_qubits} qubits, but only {len(unique_mapping)} diferent buses were specified on the mapping."
        )

    @pytest.mark.parametrize("bus_mapping", [["readout_q1", "readout_q2"], ["readout_q2", "readout_q3"]])
    def test_probabilities_raises_bus_missmatch(self, qblox_qprogram_results_probs: QProgramResults, bus_mapping):
        """Test an error is raised when not all buses are mapped into a qubit"""
        with pytest.raises(ValueError) as bus_missmatch:
            Counts.from_qprogram(qblox_qprogram_results_probs, bus_mapping)
        (msg,) = bus_missmatch.value.args
        assert (
            msg
            == "No measurements found for all specified buses, check the name of the buses provided with the mapping match all the buses specified in runcard."
        )
