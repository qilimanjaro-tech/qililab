Feature: Experiment

Scenario: Experiment can set parameter of a connected device
    Given There is an experiment with a device
    When The user connects to the device
    And The user sets the parameter  of the device
    Then The circuit contains the operation
