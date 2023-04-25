import pytest

from qililab.circuit.operation_factory import OperationFactory


class TestOperationFactory:
    """Unit tests checking the OperationFactory attributes and methods"""

    def test_get_method_raises_error_when_operation_is_not_registered(self):
        operation_name = "non_existant"
        with pytest.raises(ValueError, match=f"Operation '{operation_name}' is not registered."):
            OperationFactory.get(operation_name)
