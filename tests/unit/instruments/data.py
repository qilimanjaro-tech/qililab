# data.py
""" Data to use alongside the test suite. """
qcm_0_settings_sample = {
    "id_": 0,
    "name": "qblox_qcm",
    "category": "qubit_control",
    "ip": "192.168.0.3",
    "reference_clock": "internal",
    "sequencer": 0,
    "sync_enabled": True,
    "gain": 1,
}

qrm_0_settings_sample = {
    "id_": 0,
    "name": "qblox_qrm",
    "category": "qubit_readout",
    "ip": "192.168.0.4",
    "reference_clock": "external",
    "sequencer": 0,
    "sync_enabled": True,
    "gain": 0.5,
    "acquire_trigger_mode": "sequencer",
    "hardware_average_enabled": True,
    "start_integrate": 130,
    "sampling_rate": 1000000000,
    "integration_length": 2000,
    "integration_mode": "ssb",
    "sequence_timeout": 1,
    "acquisition_timeout": 1,
    "acquisition_name": "single",
}

rohde_schwarz_0_settings_sample = {
    "id_": 0,
    "name": "rohde_schwarz",
    "category": "signal_generator",
    "ip": "192.168.0.10",
    "frequency": 3644000000.0,
    "power": 15,
}
