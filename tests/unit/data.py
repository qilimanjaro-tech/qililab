""" Data to use alongside the test suite. """
import copy

platform_settings_sample = {
    "id_": 0,
    "name": "platform_0",
    "category": "platform",
}

qubit_0_settings_sample = {
    "id_": 0,
    "name": "qubit",
    "category": "qubit",
    "pi_pulse_amplitude": 1,
    "pi_pulse_duration": 100,
    "pi_pulse_frequency": 100000000.0,
    "qubit_frequency": 3544000000.0,
    "min_voltage": 950,
    "max_voltage": 1775,
}

qubit_1_settings_sample = {
    "id_": 1,
    "name": "qubit",
    "category": "qubit",
    "pi_pulse_amplitude": 1,
    "pi_pulse_duration": 100,
    "pi_pulse_frequency": 100000000.0,
    "qubit_frequency": 3544000000.0,
    "min_voltage": 950,
    "max_voltage": 1775,
}

qblox_qcm_0_settings_sample = {
    "id_": 0,
    "name": "qblox_qcm",
    "category": "qubit_instrument",
    "ip": "192.168.0.3",
    "firmware": "0.7.0",
    "reference_clock": "internal",
    "sequencer": 0,
    "sync_enabled": True,
    "gain": 1,
    "epsilon": 0,
    "delta": 0,
    "offset_i": 0,
    "offset_q": 0,
    "frequency": 100000000,
}

qblox_qrm_0_settings_sample = {
    "id_": 1,
    "name": "qblox_qrm",
    "category": "qubit_instrument",
    "ip": "192.168.0.4",
    "firmware": "0.7.0",
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
    "delay_before_readout": 50,
    "epsilon": 0,
    "delta": 0,
    "offset_i": 0,
    "offset_q": 0,
    "frequency": 20000000,
}

resonator_0_settings_sample = {
    "id_": 0,
    "name": "resonator",
    "category": "resonator",
    "qubits": [
        {
            "id_": 0,
            "category": "qubit",
            "pi_pulse_amplitude": 1,
            "pi_pulse_duration": 100,
            "pi_pulse_frequency": 100000000.0,
            "qubit_frequency": 3544000000.0,
            "min_voltage": 950,
            "max_voltage": 1775,
        }
    ],
}

resonator_1_settings_sample = {
    "id_": 1,
    "name": "resonator",
    "category": "resonator",
    "qubits": [
        {
            "id_": 1,
            "category": "qubit",
            "pi_pulse_amplitude": 1,
            "pi_pulse_duration": 100,
            "pi_pulse_frequency": 100000000.0,
            "qubit_frequency": 3544000000.0,
            "min_voltage": 950,
            "max_voltage": 1775,
        }
    ],
}

rohde_schwarz_0_settings_sample = {
    "id_": 0,
    "name": "rohde_schwarz",
    "category": "signal_generator",
    "ip": "192.168.0.10",
    "firmware": "4.30.046.295",
    "frequency": 3644000000.0,
    "power": 15,
}

rohde_schwarz_1_settings_sample = {
    "id_": 1,
    "name": "rohde_schwarz",  # unique name
    "category": "signal_generator",  # general name
    "ip": "192.168.0.7",
    "firmware": "4.30.046.295",
    "frequency": 7307720000.0,
    "power": 15,
}

mixer_0_settings_sample = {
    "id_": 0,
    "category": "mixer",  # general name
    "epsilon": 0,
    "delta": 0,
    "offset_i": 0,
    "offset_q": 0,
}

mixer_1_settings_sample = {
    "id_": 1,
    "category": "mixer",  # general name
    "epsilon": 0,
    "delta": 0,
    "offset_i": 0,
    "offset_q": 0,
}

mixer_2_settings_sample = {
    "id_": 2,
    "category": "mixer",  # general name
    "epsilon": 0,
    "delta": 0,
    "offset_i": 0,
    "offset_q": 0,
}

schema_settings_sample = {
    "elements": [
        {
            "id_": 0,
            "category": "bus",
            "bus_type": "control",
            "system_control": {
                "id_": 0,
                "category": "system_control",
                "name": "mixer_based_system_control",
                "qubit_instrument": qblox_qcm_0_settings_sample,
                "signal_generator": rohde_schwarz_0_settings_sample,
                "mixer_up": mixer_0_settings_sample,
            },
            "qubit": qubit_0_settings_sample,
        },
        {
            "id_": 0,
            "category": "bus",
            "bus_type": "readout",
            "system_control": {
                "id_": 1,
                "category": "system_control",
                "name": "mixer_based_system_control",
                "qubit_instrument": qblox_qrm_0_settings_sample,
                "signal_generator": rohde_schwarz_1_settings_sample,
                "mixer_up": mixer_1_settings_sample,
                "mixer_down": mixer_2_settings_sample,
            },
            "resonator": resonator_0_settings_sample,
        },
    ],
}


all_platform_settings_sample = {
    "settings": {
        "id_": 0,
        "name": "platform_0",
        "category": "platform",
    },
    "schema": schema_settings_sample,
}

experiment_settings_sample = {
    "settings": {
        "hardware_average": 4096,
        "software_average": 10,
        "repetition_duration": 200000,
    },
    "pulses": [
        {
            "bus_type": "readout",
            "start": 0,
            "duration": 60,
            "amplitude": 0.3,
            "frequency": 200000000.0,
            "phase": 1.57,
            "shape": {"name": "gaussian", "num_sigmas": 1},
            "qubit_ids": 0,
        },
        {
            "bus_type": "control",
            "start": 70,
            "duration": 60,
            "amplitude": 0.5,
            "frequency": 200000000.0,
            "phase": 3.14,
            "shape": {"name": "rectangular"},
            "qubit_ids": 0,
        },
    ],
}


class MockedSettingsHashTable:
    """Hash table that relates settings files to mocked data."""

    platform = platform_settings_sample
    qblox_qcm_0 = qblox_qcm_0_settings_sample
    qblox_qrm_0 = qblox_qrm_0_settings_sample
    qubit_0 = qubit_0_settings_sample
    resonator_0 = resonator_0_settings_sample
    rohde_schwarz_0 = rohde_schwarz_0_settings_sample
    rohde_schwarz_1 = rohde_schwarz_1_settings_sample
    schema = schema_settings_sample
    mixer_0 = mixer_0_settings_sample
    mixer_1 = mixer_1_settings_sample
    mixer_2 = mixer_2_settings_sample
    all_platform = all_platform_settings_sample
    experiment_0 = experiment_settings_sample

    @classmethod
    def get(cls, name: str) -> dict:
        """Return attribute with corresponding name."""
        return copy.deepcopy(getattr(cls, name))
