from dataclasses import dataclass

from qililab.settings.pulsar import QbloxPulsarSettings
from qililab.settings.pulse import PulseSettings


@dataclass
class QbloxPulsarQRMSettings(QbloxPulsarSettings):
    """Contains the settings of a specific pulsar.

    Args:
        ip (str): IP address of the instrument.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
        gain (float): Gain step used by the sequencer.
        acquire_trigger_mode (str): Set scope acquisition trigger mode. Options are 'sequencer' or 'level'.
        hardware_average_enabled (bool): Enable/disable hardware averaging of the data.
        start_integrate (int): Time (in ns) to start integrating the signal.
        integration_length (int): Duration (in ns) of the integration.
        mode (str): Integration mode. Options are 'ssb'.
        readout_pulse (PulseSettings): Pulse used for readout.
    """

    acquire_trigger_mode: str
    hardware_average_enabled: bool
    start_integrate: int
    sampling_rate: int
    integration_length: int
    mode: str
    readout_pulse: PulseSettings
