"""Test the one qubit 2 level transpiler"""

from unittest.mock import MagicMock, patch

import pytest

import qililab as ql
from qililab.analog import Qubit2LevelTranspiler


@patch.object(ql.analog.fluqe_parameter.FluqeParameter, "foo")
@pytest.fixture(name="dummy_transpiler")
def dummy_transpiler():
    """Transpiler dummy fixture"""
    mock_delta = MagicMock(return_value=2)
    mock_delta.name = "mock_delta"
    mock_epsilon = MagicMock(return_value=3)
    mock_epsilon.name = "mock_epsilon"
    return Qubit2LevelTranspiler(epsilon_model=mock_epsilon, delta_model=mock_delta)


class TestQubit2LevelTranspiler:
    def test_init(self, dummy_transpiler):
        """Test init method"""
        assert dummy_transpiler.delta_model.name == "mock_delta"
        assert dummy_transpiler.epsilon_model.name == "mock_epsilon"
        assert dummy_transpiler.delta.name == "delta"
        assert dummy_transpiler.epsilon.name == "epsilon"
        assert dummy_transpiler.phiz.name == "phiz"
        assert dummy_transpiler.phix.name == "phix"

    def test_transpiler(self, dummy_transpiler):
        """Test transpiler"""
        # test set delta
        dummy_transpiler.delta(4)
        dummy_transpiler.delta_model.assert_called_once_with(4)
        assert dummy_transpiler.phix() == 2
        # test set epsilon
        dummy_transpiler.epsilon(5)
        dummy_transpiler.epsilon_model.assert_called_once_with(phix=2, epsilon=5)
        assert dummy_transpiler.phiz() == 3
        # test call method
        phix, phiz = dummy_transpiler(delta=1, epsilon=2)
        assert phix == 2
        assert phiz == 3
