Feature: Circuit

Scenario: Operation is added to the circuit
    Given There is a circuit with 4 qubits
    And There is the operation X()
    When The user adds the operation to the circuit at qubit 1
    Then The circuit contains the operation at qubit 1

Scenario Outline: Random operation is added to a random circuit
    Given There is a circuit with random qubits
    And There is the operation <operation_str>
    When The user adds the operation to the circuit at a random qubit
    Then The circuit contains the operation at the same qubit

    Examples: Operation
        | operation_str             |
        | X()                       |
        | Wait(t=100)               |
        | Rxy(theta=90,phi=50)      |
