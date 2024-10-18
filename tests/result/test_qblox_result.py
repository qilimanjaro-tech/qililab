# """ Test Results """
# import re

# import numpy as np
# import pandas as pd
# import pytest
# from qblox_instruments import DummyBinnedAcquisitionData, DummyScopeAcquisitionData
# from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

# from qililab.constants import QBLOXCONSTANTS, RESULTSDATAFRAME
# from qililab.exceptions.data_unavailable import DataUnavailable
# from qililab.result.qblox_results.qblox_result import QbloxResult
# from qililab.utils.signal_processing import modulate
# from tests.test_utils import compare_pair_of_arrays, complete_array, dummy_qrm_name_generator


# @pytest.fixture(name="qrm_sequence")
# def fixture_qrm_sequence() -> Sequence:
#     """Returns an instance of Sequence with an empty program, a pair of waveforms (ones and zeros), a single
#     acquisition specification and without weights.

#     Returns:
#         Sequence: Sequence object.
#     """
#     program = Program()
#     waveforms = Waveforms()
#     waveforms.add_pair_from_complex(np.ones(1000))
#     acquisitions = Acquisitions()
#     weights = Weights()
#     acquisitions.add("single")
#     return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)


# @pytest.fixture(name="dummy_qrm")
# def fixture_dummy_qrm(qrm_sequence: Sequence) -> Pulsar:
#     """dummy QRM

#     Args:
#         qrm_sequence (Sequence): _description_

#     Returns:
#         Pulsar: _description_
#     """
#     qrm = Pulsar(name=next(dummy_qrm_name_generator), dummy_type=PulsarType.PULSAR_QRM)
#     qrm.sequencers[0].sequence(qrm_sequence.todict())
#     qrm.sequencers[0].nco_freq(10e6)
#     qrm.sequencers[0].demod_en_acq(True)
#     qrm.scope_acq_sequencer_select(0)
#     qrm.scope_acq_trigger_mode_path0("sequencer")
#     qrm.scope_acq_trigger_mode_path1("sequencer")
#     qrm.get_sequencer_state(0)
#     qrm.get_acquisition_state(0, 1)

#     waveform_length = 1000
#     zeros = np.zeros(waveform_length, dtype=np.float32)
#     ones = np.ones(waveform_length, dtype=np.float32)
#     mod_i, mod_q = modulate(i=ones, q=zeros, frequency=10e6, phase_offset=0.0)
#     filler = [0.0] * (16380 - waveform_length)
#     mod_i = np.append(mod_i, filler)
#     mod_q = np.append(mod_q, filler)
#     qrm.set_dummy_scope_acquisition_data(
#         sequencer=0,
#         data=DummyScopeAcquisitionData(data=list(zip(mod_i, mod_q)), out_of_range=(False, False), avg_cnt=(1000, 1000)),
#     )
#     qrm.set_dummy_binned_acquisition_data(
#         sequencer=0,
#         acq_index_name="single",
#         data=[DummyBinnedAcquisitionData(data=(sum(ones[:1000]), sum(zeros[:1000])), thres=0, avg_cnt=1000)],
#     )
#     return qrm


# @pytest.fixture(name="qblox_result_noscope")
# def fixture_qblox_result_noscope(dummy_qrm: Pulsar):
#     """fixture_qblox_result_noscope

#     Args:
#         dummy_qrm (Pulsar): _description_

#     Returns:
#         _type_: _description_
#     """
#     dummy_qrm.start_sequencer(0)
#     acquisition = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]
#     return QbloxResult(integration_lengths=[1000], qblox_raw_results=[acquisition])


# @pytest.fixture(name="qblox_result_scope")
# def fixture_qblox_result_scope(dummy_qrm: Pulsar):
#     """fixture_qblox_result_scope

#     Args:
#         dummy_qrm (Pulsar): _description_

#     Returns:
#         _type_: _description_
#     """
#     dummy_qrm.start_sequencer(0)
#     dummy_qrm.store_scope_acquisition(0, "single")
#     acquisition = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]
#     acquisition["qubit"] = 0
#     acquisition["measurement"] = 0
#     return QbloxResult(integration_lengths=[1000], qblox_raw_results=[acquisition])


# @pytest.fixture(name="qblox_multi_m_results")
# def fixture_qblox_multi_m_results():
#     return QbloxResult(
#         integration_lengths=[1, 1],
#         qblox_raw_results=[
#             {
#                 "scope": {
#                     "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
#                     "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
#                 },
#                 "bins": {
#                     "integration": {"path0": [1], "path1": [1]},
#                     "threshold": [0],
#                     "avg_cnt": [1],
#                 },
#                 "qubit": 0,
#                 "measurement": 0,
#             },
#             {
#                 "scope": {
#                     "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
#                     "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
#                 },
#                 "bins": {
#                     "integration": {"path0": [1], "path1": [1]},
#                     "threshold": [1],
#                     "avg_cnt": [1],
#                 },
#                 "qubit": 0,
#                 "measurement": 1,
#             },
#         ],
#     )


# @pytest.fixture(name="qblox_asymmetric_bins_result")
# def fixture_qblox_asymmetric_bins_result():
#     qblox_raw_results = [
#         {
#             "scope": {
#                 "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
#                 "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
#             },
#             "bins": {
#                 "integration": {"path0": [0.0, 0.0], "path1": [0.0, 0.0]},
#                 "threshold": [0.0, 1.0],
#                 "avg_cnt": [1, 1],
#             },
#             "qubit": 0,
#             "measurement": 0,
#         },
#         {
#             "scope": {
#                 "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
#                 "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
#             },
#             "bins": {
#                 "integration": {"path0": [0.0, 0.0, 0.0], "path1": [0.0, 0.0, 0.0]},
#                 "threshold": [1.0, 0.0, 1.0],
#                 "avg_cnt": [1, 1, 1],
#             },
#             "qubit": 0,
#             "measurement": 0,
#         },
#     ]
#     return QbloxResult(integration_lengths=[1000, 1000], qblox_raw_results=qblox_raw_results)


# class TestsQbloxResult:
#     """Test `QbloxResults` functionalities."""

#     def test_qblox_result_instantiation(self, qblox_result_scope: QbloxResult):
#         """Tests the instantiation of a QbloxResult object.

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance.
#         """
#         assert isinstance(qblox_result_scope, QbloxResult)

#     def test_qblox_result_scoped_has_scope_and_bins(self, qblox_result_scope: QbloxResult):
#         """Tests that a QbloxResult with scope has qblox_scope_acquisitions and qblox_bins_acquisitions.

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance with scope available.
#         """
#         assert qblox_result_scope.qblox_scope_acquisitions is not None
#         assert qblox_result_scope.qblox_bins_acquisitions is not None

#     def test_qblox_result_noscoped_has_no_scope_but_bins(self, qblox_result_noscope: QbloxResult):
#         """Tests that a QbloxResult without scope doesn't has qblox_scope_acquisitions but has qblox_bins_acquisitions.

#         Args:
#             qblox_result_noscope (QbloxResult): QbloxResult instance without scope available.
#         """
#         assert qblox_result_noscope.qblox_scope_acquisitions is None
#         assert qblox_result_noscope.qblox_bins_acquisitions is not None

#     def test_qblox_result_acquisitions_type(self, qblox_result_noscope: QbloxResult):
#         """Tests that a QbloxResult acquisitions method returns a Pandas Dataframe.

#         Args:
#             qblox_result_noscope (QbloxResult): QbloxResult instance.
#         """
#         acquisitions = qblox_result_noscope.acquisitions()
#         assert isinstance(acquisitions, pd.DataFrame)

#     def test_qblox_result_acquisitions(self, qblox_result_noscope: QbloxResult):
#         """Tests that the dataframe returned by QbloxResult.acquisitions is valid.

#         Args:
#             qblox_result_noscope (QbloxResult): QbloxResult instance.
#         """
#         acquisitions = qblox_result_noscope.acquisitions()
#         assert acquisitions.keys().tolist() == [
#             RESULTSDATAFRAME.ACQUISITION_INDEX,
#             RESULTSDATAFRAME.BINS_INDEX,
#             "i",
#             "q",
#             "amplitude",
#             "phase",
#         ]
#         assert np.isclose(acquisitions["i"].iloc[0], 1.0, 1e-10)
#         assert np.isclose(acquisitions["q"].iloc[0], 0.0, 1e-10)
#         assert np.isclose(acquisitions["amplitude"].iloc[0], 0.0, 1e-10)
#         assert np.isclose(acquisitions["phase"].iloc[0], 0.0, 1e-10)

#     def test_qblox_result_acquisitions_scope(self, qblox_result_scope: QbloxResult):
#         """Tests that the default acquisitions_scope method of QbloxResult returns the scope as it is.

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
#                 modulated at 10MHz.
#         """
#         acquisition = qblox_result_scope.acquisitions_scope()
#         assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
#         assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
#         time = np.arange(0, 1e-6, 1e-9)
#         expected_i = (np.cos(2 * np.pi * 10e6 * time) / np.sqrt(2)).tolist()
#         expected_q = (np.sin(2 * np.pi * 10e6 * time) / np.sqrt(2)).tolist()
#         expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
#         expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
#         assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

#     def test_qblox_result_acquisitions_scope_demod(self, qblox_result_scope: QbloxResult):
#         """Tests the demodulation of acquisitions_scope.

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
#                 modulated at 10MHz.
#         """
#         acquisition = qblox_result_scope.acquisitions_scope(demod_freq=10e6)
#         assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
#         assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
#         expected_i = [1.0 for _ in range(1000)]
#         expected_q = [0.0 for _ in range(1000)]
#         expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
#         expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
#         assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

#     def test_qblox_result_acquisitions_scope_integrated(self, qblox_result_scope: QbloxResult):
#         """Tests the integration of acquisitions_scope.

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
#                 modulated at 10MHz.
#         """
#         acquisition = qblox_result_scope.acquisitions_scope(integrate=True, integration_range=(0, 1000))
#         assert len(acquisition[0]) == 1
#         assert len(acquisition[1]) == 1
#         assert compare_pair_of_arrays(pair_a=acquisition, pair_b=([0.0], [0.0]), tolerance=1e-5)

#     def test_qblox_result_acquisitions_scope_demod_integrated(self, qblox_result_scope: QbloxResult):
#         """Tests the demodulation and integration of acquisitions_scope.

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
#                 modulated at 10MHz.
#         """
#         acquisition = qblox_result_scope.acquisitions_scope(
#             demod_freq=10e6, integrate=True, integration_range=(0, 1000)
#         )
#         assert compare_pair_of_arrays(pair_a=acquisition, pair_b=([1.0], [0.0]), tolerance=1e-5)

#     def test_qblox_result_noscoped_raises_data_unavailable(self, qblox_result_noscope: QbloxResult):
#         """Tests if DataUnavailable exception is raised

#         Args:
#             qblox_result_noscope (QbloxResult): QbloxResult instance with no scope available.
#         """
#         with pytest.raises(DataUnavailable):
#             qblox_result_noscope.acquisitions_scope(demod_freq=10e6, integrate=True, integration_range=(0, 1000))

#     def test_qblox_result_scoped_no_raises_data_unavailable(self, qblox_result_scope: QbloxResult):
#         """Tests if DataUnavailable exception is not raised

#         Args:
#             qblox_result_scope (QbloxResult): QbloxResult instance with scope available.
#         """
#         try:
#             qblox_result_scope.acquisitions_scope(demod_freq=10e6, integrate=True, integration_range=(0, 1000))
#         except DataUnavailable as exc:
#             assert False, f"acquisitions_scope raised an exception {exc}"

#     def test_qblox_result_asymmetric_bins_raise_error(self, qblox_asymmetric_bins_result: QbloxResult):
#         """Tests if IndexError exception is raised when sequencers have different number of bins.

#         Args:
#             qblox_asymmetric_bins_result (QbloxResult): QbloxResult instance with different number of bins on each sequencer.
#         """
#         bins = [len(result["bins"]["threshold"]) for result in qblox_asymmetric_bins_result.qblox_raw_results]
#         measurements = len(bins)
#         with pytest.raises(
#             IndexError,
#             match=re.escape(
#                 f"All measurements must have the same number of bins to return an array. Obtained {measurements} measurements with {bins} bins respectively."
#             ),
#         ):
#             qblox_asymmetric_bins_result.array()

#     def test_array_property_of_scope(self, dummy_qrm: Pulsar, qblox_result_scope: QbloxResult):
#         """Test the array property of the QbloxResult class."""
#         array = qblox_result_scope.array
#         dummy_qrm.start_sequencer()
#         dummy_qrm.store_scope_acquisition(0, "single")
#         scope_data = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]["scope"]
#         path0, path1 = scope_data["path0"]["data"], scope_data["path1"]["data"]
#         assert np.shape(array) == (2, 16380)  # I/Q values of the whole scope
#         assert np.allclose(array, np.array([path0, path1]))

#     def test_array_property_of_binned_data(self, dummy_qrm: Pulsar, qblox_result_noscope: QbloxResult):
#         """Test the array property of the QbloxResult class."""
#         array = qblox_result_noscope.array
#         assert np.shape(array) == (2, 1)  # (1 sequencer, I/Q, 1 bin)
#         dummy_qrm.start_sequencer(0)
#         dummy_qrm.store_scope_acquisition(0, "single")
#         bin_data = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]["bins"]["integration"]
#         path0, path1 = bin_data["path0"], bin_data["path1"]
#         assert np.allclose(array, [path0, path1])

#     def test_array_property_asymmetric_bins_raise_error(self, qblox_asymmetric_bins_result: QbloxResult):
#         """Tests if IndexError exception is raised when sequencers have different number of bins.

#         Args:
#             qblox_asymmetric_bins_result (QbloxResult): QbloxResult instance with different number of bins on each sequencer.
#         """
#         bin_shape = [len(bin_s["bins"]["threshold"]) for bin_s in qblox_asymmetric_bins_result.qblox_raw_results]
#         with pytest.raises(
#             IndexError,
#             match=re.escape(
#                 f"All measurements must have the same number of bins to return an array. Obtained {len(bin_shape)} measurements with {bin_shape} bins respectively."
#             ),
#         ):
#             _ = qblox_asymmetric_bins_result.array

#     def test_counts_error_multi_measurement(self, qblox_multi_m_results: QbloxResult):
#         """Test that an error is raised in counts if there is more than one result for a single qubit"""
#         with pytest.raises(
#             NotImplementedError, match="Counts for multiple measurements on a single qubit are not supported"
#         ):
#             _ = qblox_multi_m_results.counts()

#     def test_samples_error_multi_measurement(self, qblox_multi_m_results: QbloxResult):
#         """Test that an error is raised in counts if there is more than one result for a single qubit"""
#         with pytest.raises(
#             NotImplementedError, match="Samples for multiple measurements on a single qubit are not supported"
#         ):
#             _ = qblox_multi_m_results.samples()

#     def test_to_dataframe(self, qblox_result_noscope: QbloxResult):
#         """Test the to_dataframe method."""
#         dataframe = qblox_result_noscope.to_dataframe()
#         assert isinstance(dataframe, pd.DataFrame)
