import pytest

from qililab.analog import FluqeParameter


@pytest.fixture(name="test_parameter")
def test_parameter():
    """Dummy parameter for testing"""
    return FluqeParameter(name="foo", value=2, set_method=lambda x: 2 * x)


class TestParameter:
    """Unit tests for the ``Parameter`` class."""

    def test_init(self, test_parameter):
        """Test init method"""
        assert test_parameter.name == "foo"
        assert test_parameter._value == 2
        # test set method
        test_parameter(2)
        assert test_parameter._value == 4

    def test_get(self, test_parameter):
        """Test get method"""
        assert test_parameter() == 2

    def test_set_raw(self, test_parameter):
        """Test set_raw method"""
        test_parameter.set_raw(7)
        assert test_parameter._value == 7
