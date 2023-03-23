"""Tests for the Operation class."""
import pytest

from qililab.circuit.operations import R180, Barrier, Measure, Operation, Reset, Rxy, Wait, X


@pytest.fixture(
    name="operation", params=[Rxy(theta=90, phi=90), R180(phi=90), X(), Wait(t=100), Barrier(), Measure(), Reset()]
)
def fixture_operation(request: pytest.FixtureRequest) -> Operation:
    """Return operation object."""
    return request.param  # type: ignore


class TestOperation:
    """Unit tests checking the Operation attributes and methods"""

    def test_parameters_property(self, operation: Operation):
        """Test parameters property"""
        parameters = operation.parameters
        assert isinstance(parameters, dict)

    def test_has_parameters_method(self, operation: Operation):
        """Test has_parameters method"""
        has_parameters = operation.has_parameters()
        assert isinstance(has_parameters, bool)

    def test_get_parameter(self, operation: Operation):
        """Test get_parameter method returns correct value"""
        for name, value in operation.parameters.items():
            retrieved_value = operation.get_parameter(name)
            assert value == retrieved_value

    def test_get_paramater_raises_error_when_parameter_does_not_exist(self, operation: Operation):
        """Test get_parameter method raises a ValueError when parameter does not exist"""
        non_existant_parameter_name = "non_existant"
        with pytest.raises(
            ValueError, match=f"Operation {operation.name} has no parameter '{non_existant_parameter_name}'"
        ):
            operation.get_parameter(non_existant_parameter_name)

    def test_set_parameter(self, operation: Operation):
        """Test set_parameter method correctly sets parameter's value"""
        for name, value in operation.parameters.items():
            new_value = value + 1 if isinstance(value, (int, float)) else not value
            operation.set_parameter(name, new_value)
            assert operation.parameters[name] == new_value
            assert getattr(operation, name) == new_value

    def test_set_parameters_raises_error_when_parameter_does_not_exist(self, operation: Operation):
        """Test set_parameter method raises a ValueError when parameter does not exist"""
        non_existant_parameter_name = "non_existant"
        with pytest.raises(
            ValueError, match=f"Operation {operation.name} has no parameter '{non_existant_parameter_name}'"
        ):
            operation.set_parameter(non_existant_parameter_name, 1)

    @pytest.mark.parametrize(
        "operation,expected_result", [(X(), "X"), (Rxy(theta=180, phi=45), "Rxy(theta=180,phi=45)")]
    )
    def test_str_method(self, operation: Operation, expected_result: str):
        """Test __str__ method"""
        result = str(operation)
        assert isinstance(result, str)
        assert result == expected_result

    @pytest.mark.parametrize("string_representation", ["X", "Wait(t=1000)", "Rxy(theta=180,phi=45)"])
    def test_parse_method(self, string_representation: str):
        operation = Operation.parse(string_representation=string_representation)
        assert isinstance(operation, Operation)
