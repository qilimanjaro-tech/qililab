import random

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from qililab.circuit import Circuit, Operation, X

scenarios("circuit_flow.feature")


@given(parsers.parse("There is a circuit with {num_qubits:d} qubits"), target_fixture="circuit")
def there_is_a_circuit(num_qubits):
    return Circuit(num_qubits=num_qubits)


@given(parsers.parse("There is a circuit with random qubits"), target_fixture="circuit")
def there_is_a_random_circuit():
    num_qubits = random.randint(1, 5)
    return Circuit(num_qubits=num_qubits)


@given("There is the operation <operation_str>", target_fixture="operation")
@given(parsers.parse("There is the operation {operation_str}"), target_fixture="operation")
def there_is_an_operation(operation_str):
    return Operation.parse(operation_str)


@when(parsers.parse("The user adds the operation to the circuit at qubit {qubit:d}"))
def add_operation(qubit, circuit, operation):
    circuit.add(qubit, operation)


@when(parsers.parse("The user adds the operation to the circuit at a random qubit"), target_fixture="qubit")
def add_operation_random_qubit(circuit, operation):
    qubit = random.randint(0, circuit.num_qubits - 1)
    circuit.add(qubit, operation)
    return qubit


@then(parsers.parse("The circuit contains the operation at the same qubit"))
@then(parsers.parse("The circuit contains the operation at qubit {qubit:d}"))
def circuit_contains_operation(circuit, operation, qubit):
    assert (
        any(
            [
                node.qubits == (qubit,) and node.operation == operation
                for layer in circuit.get_operation_layers()
                for node in layer
            ]
        )
        is True
    )


@then("The circuit has all transpilation flags set to False")
def circuit_has_transpilation_flags_set_to(circuit: Circuit):
    assert circuit.has_timings_calculated is False
    assert circuit.has_special_operations_removed is False
    assert circuit.has_transpiled_to_pulses is False
