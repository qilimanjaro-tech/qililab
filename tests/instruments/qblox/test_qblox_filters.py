"""This file tests the the ``qblox_filters`` class"""
import pytest
import numpy as np
from qililab.instruments.qblox import QbloxFilter
from qililab.constants import QBLOXCONSTANTS

class TestQbloxFilter:
    """This class contains the unit tests for the ``qblox_filter`` class."""
    def test_filter(self):
        fir_coeff = np.ones(32)

        filter = QbloxFilter(
            output_id=1,
            exponential_amplitude=[1, 0.3],
            exponential_time_constant=[10, 200],
            exponential_state=[True, False],
            fir_coeff=fir_coeff ,
            fir_state=True
        )

        assert filter.output_id == 1
        assert filter.exponential_amplitude == [1, 0.3, None, None]
        assert filter.exponential_time_constant == [10, 200, None, None]
        assert filter.exponential_state == ["enabled", "bypassed", None, None]
        assert np.array_equal(filter.fir_coeff, fir_coeff)
        assert filter.fir_state == "enabled"

    def test_filter_converts_to_list(self):
        fir_coeff = np.ones(32)

        filter = QbloxFilter(
            output_id=1,
            exponential_amplitude=1,
            exponential_time_constant=10,
            exponential_state=True,
            fir_coeff=fir_coeff ,
            fir_state=False
        )


        assert isinstance(filter.exponential_amplitude, list)
        assert isinstance(filter.exponential_time_constant, list)
        assert isinstance(filter.exponential_state, list)

        assert filter.exponential_amplitude == [1, None, None, None]
        assert filter.exponential_time_constant == [10, None, None, None]
        assert filter.exponential_state == ["enabled", None, None, None]

        assert filter.fir_state == "bypassed"

    def test_filter_coeff_wrong_length(self):
        fir_coeff = np.ones(30)
        output_id = 2

        with pytest.raises(ValueError, match=f"The number of elements in the list must be exactly {QBLOXCONSTANTS.FILTER_FIR_COEFF_LENGTH}. Received: {len(fir_coeff)}"):
            _ = QbloxFilter(
                output_id=output_id,
                fir_coeff=fir_coeff ,
            )