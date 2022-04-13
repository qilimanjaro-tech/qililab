"""Qblox pulsar QRM settings class."""
from dataclasses import dataclass

from qililab.settings.instruments.qblox.qblox_pulsar import QbloxPulsarSettings
from qililab.settings.instruments.qubit_readout import QubitReadoutSettings
from qililab.typings import AcquireTriggerMode, IntegrationMode


@dataclass
class QbloxPulsarQRMSettings(QbloxPulsarSettings, QubitReadoutSettings):
    """Contains the settings of a specific pulsar.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        ip (str): IP address of the instrument.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
        gain (float): Gain step used by the sequencer.
        acquire_trigger_mode (str): Set scope acquisition trigger mode. Options are 'sequencer' or 'level'.
        hardware_average_enabled (bool): Enable/disable hardware averaging of the data.
        start_integrate (int): Time (in ns) to start integrating the signal.
        integration_length (int): Duration (in ns) of the integration.
        integration_mode (str): Integration mode. Options are 'ssb'.
        sequence_timeout (int): Time (in minutes) to wait for the sequence to finish.
        If timeout is reached a TimeoutError is raised.
        acquisition_timeout (int): Time (in minutes) to wait for the acquisition to finish.
        If timeout is reached a TimeoutError is raised.
        acquisition_name (str): Name of the acquisition saved in the sequencer.
    """

    acquire_trigger_mode: str | AcquireTriggerMode
    hardware_average_enabled: bool
    start_integrate: int
    sampling_rate: int
    integration_length: int
    integration_mode: str | IntegrationMode
    sequence_timeout: int  # minutes
    acquisition_timeout: int  # minutes
    acquisition_name: str

    def __post_init__(self):
        """Cast acquire_trigger_mode and integration_mode to its corresponding Enum classes"""
        super().__post_init__()
        self.acquire_trigger_mode = AcquireTriggerMode(self.acquire_trigger_mode)
        self.integration_mode = IntegrationMode(self.integration_mode)
