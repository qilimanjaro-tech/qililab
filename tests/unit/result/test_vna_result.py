import numpy as np
import pytest

from qililab.result.vna_result import VNAResult
from qililab.typings.enums import ResultName


@pytest.fixture(name="vna_result")
def fixture_vna_result() -> VNAResult:
    """Return Loop object"""
    return VNAResult(i=np.array([1, 2]), q=np.array([3, 4]))


class TestVNAResult:
    """Unit tests checking the Loop attributes and methods"""

    def test_properties(self, vna_result: VNAResult):
        assert hasattr(vna_result, "i")
        assert hasattr(vna_result, "q")
        assert isinstance(vna_result.i, np.ndarray)
        assert isinstance(vna_result.q, np.ndarray)
        assert vna_result.name == ResultName.VECTOR_NETWORK_ANALYZER

    def test_acquisitions(self, vna_result: VNAResult):
        """Test the acquisition method"""
        test_i, test_q = vna_result.acquisitions()
        np.testing.assert_array_equal(test_i, vna_result.i)
        np.testing.assert_array_equal(test_q, vna_result.q)
