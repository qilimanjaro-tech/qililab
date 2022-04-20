# data.py
""" Data to use alongside the test suite. """
platform_settings_sample = {
    "category": "platform",
    "number_qubits": 1,
    "hardware_average": 4096,
    "software_average": 10,
    "repetition_duration": 200000,
    "delay_between_pulses": 0,
    "delay_before_readout": 50,
    "drag_coefficient": 0,
    "number_of_sigmas": 4,
}
qubit_0_settings_sample = {
    "category": "qubit",
    "pi_pulse_amplitude": 1,
    "pi_pulse_duration": 100,
    "pi_pulse_frequency": 100000000.0,
    "qubit_frequency": 3544000000.0,
    "min_voltage": 950,
    "max_voltage": 1775,
}

schema_settings_sample = {
    "category": "schema",
    "buses": {
        "bus_0": {
            "instrument": "qcm_0",
            "resonator": "resonator_0",
            "qubit": "qubit_0",
        },
        "bus_1": {
            "instrument": "qrm_0",
            "resonator": "resonator_0",
            "qubit": "qubit_0",
        },
    },
}
