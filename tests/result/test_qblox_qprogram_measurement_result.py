""" Test Results """

import json

import numpy as np
import pytest
from qblox_instruments import DummyBinnedAcquisitionData, DummyScopeAcquisitionData, Pulsar, PulsarType
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.constants import QBLOXMEASUREMENTRESULT, RUNCARD
from qililab.result.qblox_results.qblox_qprogram_measurement_result import QbloxQProgramMeasurementResult
from qililab.utils.signal_processing import modulate
from tests.test_utils import dummy_qrm_name_generator


@pytest.fixture(name="qrm_sequence")
def fixture_qrm_sequence() -> Sequence:
    """Returns an instance of Sequence with an empty program, a pair of waveforms (ones and zeros), a single
    acquisition specification and without weights.

    Returns:
        Sequence: Sequence object.
    """
    program = Program()
    waveforms = Waveforms()
    waveforms.add_pair_from_complex(np.ones(1000))
    acquisitions = Acquisitions()
    weights = Weights()
    acquisitions.add("single")
    return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)


@pytest.fixture(name="dummy_qrm")
def fixture_dummy_qrm(qrm_sequence: Sequence) -> Pulsar:
    """dummy QRM

    Args:
        qrm_sequence (Sequence): _description_

    Returns:
        Pulsar: _description_
    """
    qrm = Pulsar(name=next(dummy_qrm_name_generator), dummy_type=PulsarType.PULSAR_QRM)
    qrm.sequencers[0].sequence(qrm_sequence.todict())
    qrm.sequencers[0].nco_freq(10e6)
    qrm.sequencers[0].demod_en_acq(True)
    qrm.scope_acq_sequencer_select(0)
    qrm.scope_acq_trigger_mode_path0("sequencer")
    qrm.scope_acq_trigger_mode_path1("sequencer")
    qrm.get_sequencer_state(0)
    qrm.get_acquisition_state(0, 1)

    waveform_length = 1000
    zeros = np.zeros(waveform_length, dtype=np.float32)
    ones = np.ones(waveform_length, dtype=np.float32)
    mod_i, mod_q = modulate(i=ones, q=zeros, frequency=10e6, phase_offset=0.0)
    filler = [0.0] * (16380 - waveform_length)
    mod_i = np.append(mod_i, filler)
    mod_q = np.append(mod_q, filler)
    qrm.set_dummy_scope_acquisition_data(
        sequencer=0,
        data=DummyScopeAcquisitionData(data=list(zip(mod_i, mod_q)), out_of_range=(False, False), avg_cnt=(1000, 1000)),
    )
    qrm.set_dummy_binned_acquisition_data(
        sequencer=0,
        acq_index_name="single",
        data=[DummyBinnedAcquisitionData(data=(sum(ones[:1000]), sum(zeros[:1000])), thres=0, avg_cnt=1000)],
    )
    return qrm


@pytest.fixture(name="qblox_measurement_result")
def fixture_qblox_result_noscope(dummy_qrm: Pulsar):
    """fixture_qblox_result_noscope

    Args:
        dummy_qrm (Pulsar): _description_

    Returns:
        _type_: _description_
    """
    dummy_qrm.start_sequencer(0)
    acquisition = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]
    return QbloxQProgramMeasurementResult(raw_measurement_data=acquisition)


@pytest.fixture(name="qblox_asymmetric_bins_result")
def fixture_qblox_asymmetric_bins_result():
    qblox_raw_results = [
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [0.0, 0.0], "path1": [0.0, 0.0]},
                "threshold": [0.0, 1.0],
                "avg_cnt": [1, 1],
            },
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [0.0, 0.0, 0.0], "path1": [0.0, 0.0, 0.0]},
                "threshold": [1.0, 0.0, 1.0],
                "avg_cnt": [1, 1, 1],
            },
        },
    ]
    return QbloxQProgramMeasurementResult(raw_measurement_data=qblox_raw_results)


class TestsQbloxQProgramMeasurementResult:
    """Test `QbloxQProgramResults` functionalities."""

    def test_qblox_result_instantiation(self, qblox_measurement_result: QbloxQProgramMeasurementResult):
        """Tests the instantiation of a QbloxQProgramResult object.

        Args:
            qblox_result_scope (QbloxQProgramResult): QbloxQProgramResult instance.
        """
        assert isinstance(qblox_measurement_result, QbloxQProgramMeasurementResult)

    def test_array_property_of_binned_data(
        self, dummy_qrm: Pulsar, qblox_measurement_result: QbloxQProgramMeasurementResult
    ):
        """Test the array property of the QbloxQProgramResult class."""
        array = qblox_measurement_result.array
        assert np.shape(array) == (2, 1)  # (1 sequencer, I/Q, 1 bin)
        dummy_qrm.start_sequencer(0)
        dummy_qrm.store_scope_acquisition(0, "single")
        bin_data = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]["bins"]["integration"]
        path0, path1 = bin_data["path0"], bin_data["path1"]
        assert np.allclose(array, [path0, path1])

    def test_serialization_method(self, qblox_measurement_result: QbloxQProgramMeasurementResult):
        """Test serialization and deserialization works."""
        serialized_dictionary = qblox_measurement_result.to_dict()
        assert "type" in serialized_dictionary
        assert "attributes" in serialized_dictionary

        deserialized_qp = QbloxQProgramMeasurementResult.from_dict(serialized_dictionary["attributes"])
        assert isinstance(deserialized_qp, QbloxQProgramMeasurementResult)

        again_serialized_dictionary = deserialized_qp.to_dict()
        assert serialized_dictionary == again_serialized_dictionary

        as_json = json.dumps(again_serialized_dictionary)
        dictionary_from_json = json.loads(as_json)
        assert serialized_dictionary == dictionary_from_json
