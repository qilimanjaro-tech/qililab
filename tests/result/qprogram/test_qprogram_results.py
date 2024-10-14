""" Test Results """
import os

import numpy as np
import pytest

from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


@pytest.fixture(name="qblox_qprogram_results")
def fixture_qblox_qprogram_results():
    """fixture_qblox_result_noscope

    Returns:
        QProgramResults: `QProgramResults` from Qblox instrument fixture.
    """
    results = QProgramResults()
    results.append_result(
        bus="readout", result=QbloxMeasurementResult(bus="readout", raw_measurement_data={"abc": 123})
    )
    return results


@pytest.fixture(name="quantum_machines_qprogram_results")
def fixture_quantum_machines_qprogram_results():
    """fixture_quantum_machines_result_noscope

    Returns:
        QProgramResults: `QProgramResults` from Quantum Machines instrument fixture.
    """
    results = QProgramResults()
    results.append_result(
        bus="readout",
        result=QuantumMachinesMeasurementResult(bus="readout", I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11)),
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
            "readout",
            result=QuantumMachinesMeasurementResult(
                bus="readout", I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11)
            ),
        )
        assert len(quantum_machines_qprogram_results.results["readout"]) == 2

        quantum_machines_qprogram_results.append_result(
            "another_readout",
            result=QuantumMachinesMeasurementResult(
                bus="readout", I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11)
            ),
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
            "readout", result=QbloxMeasurementResult(bus="readout", raw_measurement_data={"def": 456})
        )
        assert len(qblox_qprogram_results.results["readout"]) == 2

        qblox_qprogram_results.append_result(
            "another_readout", result=QbloxMeasurementResult(bus="another_readout", raw_measurement_data={"def": 456})
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
