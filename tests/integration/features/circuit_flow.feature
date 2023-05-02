Feature: Circuit

Scenario: Operations are added to the circuit
    Given There is a circuit
    Given There is an operation
    When The user adds the operation to the circuit
    Then The circuit contains the operation
