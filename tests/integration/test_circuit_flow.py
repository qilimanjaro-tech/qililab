import pytest
from pytest_bdd import given, scenarios, then, when

from qililab.circuit import Circuit, Operation, X

scenarios("circuit_flow.feature")


# @pytest.fixture
# def circuit() -> Circuit:
#     return Circuit(2)


# @pytest.fixture
# def operation() -> Operation:
#     return X()


@given("There is a circuit", target_fixture="circuit")
def there_is_a_circuit():
    return Circuit(2)


@given("There is an operation", target_fixture="operation")
def there_is_an_operation():
    return X()


@when("The user adds the operation to the circuit")
def add_operation(circuit, operation):
    circuit.add(0, operation)


@then("The circuit contains the operation")
def circuit_contains_operation(circuit, operation):
    assert (
        any([node.operation.name == operation.name for layer in circuit.get_operation_layers() for node in layer])
        is True
    )
