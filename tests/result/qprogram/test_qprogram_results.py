""" Test Results """
import os

import numpy as np
import pytest

from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.result.qprogram.qprogram_results import QProgramResults, probabilities
from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


@pytest.fixture(name="qblox_qprogram_results")
def fixture_qblox_qprogram_results():
    """fixture_qblox_result_noscope

    Returns:
        QProgramResults: `QProgramResults` from Qblox instrument fixture.
    """
    results = QProgramResults()
    results.append_result(bus="readout", result=QbloxMeasurementResult(raw_measurement_data={"abc": 123}))
    return results


@pytest.fixture(name="quantum_machines_qprogram_results")
def fixture_quantum_machines_qprogram_results():
    """fixture_quantum_machines_result_noscope

    Returns:
        QProgramResults: `QProgramResults` from Quantum Machines instrument fixture.
    """
    results = QProgramResults()
    results.append_result(
        bus="readout", result=QuantumMachinesMeasurementResult(I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11))
    )
    return results


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
                raw_measurement_data={"bins": {"integration": {"path0": [0], "path1": [0]}, "threshold": [th_q0]}}
            ),
        )
        results.append_result(
            bus="readout_q1",
            result=QbloxMeasurementResult(
                raw_measurement_data={"bins": {"integration": {"path0": [0], "path1": [0]}, "threshold": [th_q1]}}
            ),
        )
    return results


class TestsQProgramResult:
    """Test `QbloxQProgramResults` functionalities."""

    def test_append_result_method_with_quantum_machines(self, quantum_machines_qprogram_results: QProgramResults):
        """Tests the instantiation of a QbloxQProgramResult object.

        Args:
            qblox_result_scope (QbloxQProgramResult): QbloxQProgramResult instance.
        """
        assert "readout" in quantum_machines_qprogram_results.results
        assert len(quantum_machines_qprogram_results.results["readout"]) == 1

        quantum_machines_qprogram_results.append_result(
            "readout", result=QuantumMachinesMeasurementResult(I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11))
        )
        assert len(quantum_machines_qprogram_results.results["readout"]) == 2

        quantum_machines_qprogram_results.append_result(
            "another_readout",
            result=QuantumMachinesMeasurementResult(I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11)),
        )
        assert "another_readout" in quantum_machines_qprogram_results.results
        assert len(quantum_machines_qprogram_results.results["another_readout"]) == 1

    def test_append_result_method_with_qblox(self, qblox_qprogram_results: QProgramResults):
        """Tests the instantiation of a QbloxQProgramResult object.

        Args:
            qblox_result_scope (QbloxQProgramResult): QbloxQProgramResult instance.
        """
        assert "readout" in qblox_qprogram_results.results
        assert len(qblox_qprogram_results.results["readout"]) == 1

        qblox_qprogram_results.append_result(
            "readout", result=QbloxMeasurementResult(raw_measurement_data={"def": 456})
        )
        assert len(qblox_qprogram_results.results["readout"]) == 2

        qblox_qprogram_results.append_result(
            "another_readout", result=QbloxMeasurementResult(raw_measurement_data={"def": 456})
        )
        assert "another_readout" in qblox_qprogram_results.results
        assert len(qblox_qprogram_results.results["another_readout"]) == 1

    def test_serialization_method(
        self, qblox_qprogram_results: QProgramResults, quantum_machines_qprogram_results: QProgramResults
    ):
        """Test serialization and deserialization works."""
        serialized = serialize(qblox_qprogram_results)
        deserialized_qblox_qprogram_results = deserialize(serialized, QProgramResults)

        assert isinstance(deserialized_qblox_qprogram_results, QProgramResults)

        serialize_to(qblox_qprogram_results, file="qblox_qprogram_results.yml")
        deserialized_qblox_qprogram_results = deserialize_from("qblox_qprogram_results.yml", QProgramResults)

        assert isinstance(deserialized_qblox_qprogram_results, QProgramResults)

        os.remove("qblox_qprogram_results.yml")

        serialized = serialize(quantum_machines_qprogram_results)
        deserialized_quantum_machines_qprogram_results = deserialize(serialized, QProgramResults)

        assert isinstance(deserialized_quantum_machines_qprogram_results, QProgramResults)

        serialize_to(qblox_qprogram_results, file="quantum_machines_qprogram_results.yml")
        deserialized_quantum_machines_qprogram_results = deserialize_from(
            "quantum_machines_qprogram_results.yml", QProgramResults
        )

        assert isinstance(deserialized_quantum_machines_qprogram_results, QProgramResults)

        os.remove("quantum_machines_qprogram_results.yml")


class TestProbabilities:
    """Class to test the `probabilities` method."""

    @pytest.mark.parametrize(
        "bus_mapping, expected_probs",
        [
            (None, {"00": 0.2, "01": 0.2, "10": 0.4, "11": 0.2}),
            (["readout_q1", "readout_q0"], {"00": 0.2, "01": 0.4, "10": 0.2, "11": 0.2}),
        ],
    )
    def test_probabilities(self, qblox_qprogram_results_probs: QProgramResults, bus_mapping, expected_probs):
        """Test probabilities are computed correctly with and without qubit mapping"""
        assert probabilities(qblox_qprogram_results_probs, bus_mapping) == expected_probs

    def test_probabilities_raises_empty(self):
        """Test an error is raised when the `qprogram_results` is empty"""
        qp_results = QProgramResults()
        with pytest.raises(ValueError) as empty_error:
            probabilities(qp_results)
        (msg,) = empty_error.value.args
        assert msg == f"Can not obtain probabilities with no measurments, {qp_results.__class__} empty"

    @pytest.mark.parametrize(
        "bus_mapping", [[], ["readout_q1", "readout_q1"], ["readout_q0", "readout_q1", "readout_q2"]]
    )
    def test_probabilities_raises_len_missmatch(self, qblox_qprogram_results_probs: QProgramResults, bus_mapping):
        """Test an error is raised when a mapping is not specified for all qubits"""
        n_qubits = len(qblox_qprogram_results_probs.results)
        unique_mapping = set(bus_mapping)
        with pytest.raises(ValueError) as len_missmatch:
            probabilities(qblox_qprogram_results_probs, bus_mapping)
        (msg,) = len_missmatch.value.args
        assert (
            msg
            == f"Expected mapping for all qubits. Results have {n_qubits} qubits, but only {len(unique_mapping)} diferent buses were specified on the mapping."
        )

    @pytest.mark.parametrize("bus_mapping", [["readout_q1", "readout_q2"], ["readout_q2", "readout_q3"]])
    def test_probabilities_raises_bus_missmatch(self, qblox_qprogram_results_probs: QProgramResults, bus_mapping):
        """Test an error is raised when not all buses are mapped into a qubit"""
        with pytest.raises(ValueError) as bus_missmatch:
            probabilities(qblox_qprogram_results_probs, bus_mapping)
        (msg,) = bus_missmatch.value.args
        assert (
            msg
            == "No measurements found for all specified buses, check the name of the buses provided with the mapping match all the buses specified in runcard."
        )
