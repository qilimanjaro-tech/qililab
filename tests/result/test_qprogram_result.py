""" Test Results """

import json

import numpy as np
import pytest
from qblox_instruments import DummyBinnedAcquisitionData, DummyScopeAcquisitionData, Pulsar, PulsarType
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.result.qblox_results.qblox_qprogram_measurement_result import QbloxQProgramMeasurementResult
from qililab.result.qprogram_results import QProgramResults
from qililab.result.quantum_machines_results.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.utils.signal_processing import modulate
from tests.test_utils import dummy_qrm_name_generator


@pytest.fixture(name="qblox_qprogram_results")
def fixture_qblox_qprogram_result():
    """fixture_qblox_result_noscope

    Args:
        dummy_qrm (Pulsar): _description_

    Returns:
        _type_: _description_
    """
    results = QProgramResults()
    results.append_result(bus="readout", result=QbloxQProgramMeasurementResult(raw_measurement_data={"abc": 123}))
    return results


@pytest.fixture(name="qm_qprogram_results")
def fixture_qm_qprogram_result():
    """fixture_qblox_result_noscope

    Args:
        dummy_qrm (Pulsar): _description_

    Returns:
        _type_: _description_
    """
    results = QProgramResults()
    results.append_result(
        bus="readout", result=QuantumMachinesMeasurementResult(I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11))
    )
    return results


class TestsQProgramResult:
    """Test `QbloxQProgramResults` functionalities."""

    def test_qm_append_result(self, qm_qprogram_results: QProgramResults):
        """Tests the instantiation of a QbloxQProgramResult object.

        Args:
            qblox_result_scope (QbloxQProgramResult): QbloxQProgramResult instance.
        """
        assert "readout" in qm_qprogram_results.results
        assert len(qm_qprogram_results.results["readout"]) == 1

        qm_qprogram_results.append_result(
            "readout", result=QuantumMachinesMeasurementResult(I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11))
        )
        assert len(qm_qprogram_results.results["readout"]) == 2

        qm_qprogram_results.append_result(
            "another_readout",
            result=QuantumMachinesMeasurementResult(I=np.linspace(0, 10, 11), Q=np.linspace(90, 100, 11)),
        )
        assert "another_readout" in qm_qprogram_results.results
        assert len(qm_qprogram_results.results["another_readout"]) == 1

    def test_qblox_append_result(self, qblox_qprogram_results: QProgramResults):
        """Tests the instantiation of a QbloxQProgramResult object.

        Args:
            qblox_result_scope (QbloxQProgramResult): QbloxQProgramResult instance.
        """
        assert "readout" in qblox_qprogram_results.results
        assert len(qblox_qprogram_results.results["readout"]) == 1

        qblox_qprogram_results.append_result(
            "readout", result=QbloxQProgramMeasurementResult(raw_measurement_data={"def": 456})
        )
        assert len(qblox_qprogram_results.results["readout"]) == 2

        qblox_qprogram_results.append_result(
            "another_readout", result=QbloxQProgramMeasurementResult(raw_measurement_data={"def": 456})
        )
        assert "another_readout" in qblox_qprogram_results.results
        assert len(qblox_qprogram_results.results["another_readout"]) == 1

    def test_serialization_method(self, qblox_qprogram_results: QProgramResults):
        """Test serialization and deserialization works."""
        serialized_dictionary = qblox_qprogram_results.to_dict()
        assert "type" in serialized_dictionary
        assert "attributes" in serialized_dictionary

        deserialized_qp = QProgramResults.from_dict(serialized_dictionary["attributes"])
        assert isinstance(deserialized_qp, QProgramResults)

        again_serialized_dictionary = deserialized_qp.to_dict()
        assert serialized_dictionary == again_serialized_dictionary

        as_json = json.dumps(again_serialized_dictionary)
        dictionary_from_json = json.loads(as_json)
        assert serialized_dictionary == dictionary_from_json
