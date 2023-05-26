""" Test Results """

import numpy as np
import pandas as pd
import pytest
from dummy_qblox import DummyPulsar
from qblox_instruments import PulsarType
from qpysequence import Sequence
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.waveforms import Waveforms

from qililab.constants import QBLOXCONSTANTS, RESULTSDATAFRAME
from qililab.exceptions.data_unavailable import DataUnavailable
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.utils.signal_processing import modulate
from tests.utils import dummy_qrm_name_generator

from ...utils import compare_pair_of_arrays, complete_array


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
    acquisitions.add("single")
    return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights={})


@pytest.fixture(name="dummy_qrm")
def fixture_dummy_qrm(qrm_sequence: Sequence) -> DummyPulsar:
    """dummy QRM

    Args:
        qrm_sequence (Sequence): _description_

    Returns:
        DummyPulsar: _description_
    """
    qrm = DummyPulsar(name=next(dummy_qrm_name_generator), pulsar_type=PulsarType.PULSAR_QRM)
    waveform_length = 1000
    zeros = np.zeros(waveform_length, dtype=np.float32)
    ones = np.ones(waveform_length, dtype=np.float32)
    sim_in_0, sim_in_1 = modulate(i=ones, q=zeros, frequency=10e6, phase_offset=0.0)
    filler = [0.0] * (16380 - waveform_length)
    sim_in_0 = np.append(sim_in_0, filler)
    sim_in_1 = np.append(sim_in_1, filler)
    qrm.feed_input_data(input_path0=sim_in_0, input_path1=sim_in_1)
    qrm.sequencers[0].sequence(qrm_sequence.todict())
    qrm.sequencers[0].nco_freq(10e6)
    qrm.sequencers[0].demod_en_acq(True)
    qrm.scope_acq_sequencer_select(0)
    qrm.scope_acq_trigger_mode_path0("sequencer")
    qrm.scope_acq_trigger_mode_path1("sequencer")
    qrm.get_sequencer_state(0)
    qrm.get_acquisition_state(0, 1)
    return qrm


@pytest.fixture(name="qblox_result_noscope")
def fixture_qblox_result_noscope(dummy_qrm: DummyPulsar):
    """fixture_qblox_result_noscope

    Args:
        dummy_qrm (DummyPulsar): _description_

    Returns:
        _type_: _description_
    """
    acquisition = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]
    import numpy as np

    acquisition = {
        "scope": {
            "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
            "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
        },
        "bins": {
            "integration": {"path0": [1000.0, 19, 20], "path1": [-1.3504188124071826e-15, 0.000000, 1.0]},
            "threshold": [np.nan, np.nan],
            "avg_cnt": [1, 1, 0],
        },
    }
    return QbloxResult(
        integration_lengths=[1000, 1000, 1000], qblox_raw_results=[acquisition, acquisition, acquisition]
    )


@pytest.fixture(name="qblox_result_scope")
def fixture_qblox_result_scope(dummy_qrm: DummyPulsar):
    """fixture_qblox_result_scope

    Args:
        dummy_qrm (DummyPulsar): _description_

    Returns:
        _type_: _description_
    """
    dummy_qrm.store_scope_acquisition(0, "single")
    acquisition = dummy_qrm.get_acquisitions(0)["single"]["acquisition"]
    return QbloxResult(integration_lengths=[1000, 1000], qblox_raw_results=[acquisition, acquisition])


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
    return QbloxResult(integration_lengths=[1000, 1000], qblox_raw_results=qblox_raw_results)


class TestsQbloxResult:
    """Test `QbloxResult` functionalities."""

    def test_qblox_result_instantiation(self, qblox_result_scope: QbloxResult):
        """Tests the instantiation of a QbloxResult object.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance.
        """
        assert isinstance(qblox_result_scope, QbloxResult)

    def test_qblox_result_scoped_has_scope_and_bins(self, qblox_result_scope: QbloxResult):
        """Tests that a QbloxResult with scope has qblox_scope_acquisitions and qblox_bins_acquisitions.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available.
        """
        assert qblox_result_scope.qblox_scope_acquisitions is not None
        assert qblox_result_scope.qblox_bins_acquisitions is not None

    def test_qblox_result_noscoped_has_no_scope_but_bins(self, qblox_result_noscope: QbloxResult):
        """Tests that a QbloxResult without scope doesn't has qblox_scope_acquisitions but has qblox_bins_acquisitions.

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance without scope available.
        """
        assert qblox_result_noscope.qblox_scope_acquisitions is None
        assert qblox_result_noscope.qblox_bins_acquisitions is not None

    def test_qblox_result_acquisitions_type(self, qblox_result_noscope: QbloxResult):
        """Tests that a QbloxResult acquisitions method returns a Pandas Dataframe.

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance.
        """
        acquisitions = qblox_result_noscope.acquisitions()
        assert isinstance(acquisitions, pd.DataFrame)

    def test_qblox_result_acquisitions(self, qblox_result_noscope: QbloxResult):
        """Tests that the dataframe returned by QbloxResult.acquisitions is valid.

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance.
        """
        acquisitions = qblox_result_noscope.acquisitions()
        assert set(acquisitions.keys().tolist()) == {
            RESULTSDATAFRAME.ACQUISITION_INDEX,
            RESULTSDATAFRAME.BINS_INDEX,
            RESULTSDATAFRAME.QUBIT_INDEX,
            "i",
            "q",
            "amplitude",
            "phase",
        }
        assert np.isclose(acquisitions["i"].iloc[0], 1.0, 1e-10)
        assert np.isclose(acquisitions["q"].iloc[0], 0.0, 1e-10)
        assert np.isclose(acquisitions["amplitude"].iloc[0], 0.0, 1e-10)
        assert np.isclose(acquisitions["phase"].iloc[0], 0.0, 1e-10)

    def test_qblox_result_acquisitions_scope(self, qblox_result_scope: QbloxResult):
        """Tests that the default acquisitions_scope method of QbloxResult returns the scope as it is.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope()
        assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
        assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
        time = np.arange(0, 1e-6, 1e-9)
        expected_i = (np.cos(2 * np.pi * 10e6 * time) / np.sqrt(2)).tolist()
        expected_q = (np.sin(2 * np.pi * 10e6 * time) / np.sqrt(2)).tolist()
        expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_demod(self, qblox_result_scope: QbloxResult):
        """Tests the demodulation of acquisitions_scope.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope(demod_freq=10e6)
        assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
        assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
        expected_i = [1.0 for _ in range(1000)]
        expected_q = [0.0 for _ in range(1000)]
        expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_integrated(self, qblox_result_scope: QbloxResult):
        """Tests the integration of acquisitions_scope.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope(integrate=True, integration_range=(0, 1000))
        assert len(acquisition[0]) == 1
        assert len(acquisition[1]) == 1
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=([0.0], [0.0]), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_demod_integrated(self, qblox_result_scope: QbloxResult):
        """Tests the demodulation and integration of acquisitions_scope.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope(
            demod_freq=10e6, integrate=True, integration_range=(0, 1000)
        )
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=([1.0], [0.0]), tolerance=1e-5)

    def test_qblox_result_noscoped_raises_data_unavailable(self, qblox_result_noscope: QbloxResult):
        """Tests if DataUnavailable exception is raised

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance with no scope available.
        """
        with pytest.raises(DataUnavailable):
            qblox_result_noscope.acquisitions_scope(demod_freq=10e6, integrate=True, integration_range=(0, 1000))

    def test_qblox_result_scoped_no_raises_data_unavailable(self, qblox_result_scope: QbloxResult):
        """Tests if DataUnavailable exception is not raised

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available.
        """
        try:
            qblox_result_scope.acquisitions_scope(demod_freq=10e6, integrate=True, integration_range=(0, 1000))
        except DataUnavailable as exc:
            assert False, f"acquisitions_scope raised an exception {exc}"

    def test_qblox_result_asymmetric_bins_raise_error(self, qblox_asymmetric_bins_result: QbloxResult):
        """Tests if IndexError exception is raised when sequencers have different number of bins.

        Args:
            qblox_asymmetric_bins_result (QbloxResult): QbloxResult instance with different number of bins on each sequencer.
        """
        with pytest.raises(IndexError, match="Sequencers must have the same number of bins."):
            qblox_asymmetric_bins_result.counts()
