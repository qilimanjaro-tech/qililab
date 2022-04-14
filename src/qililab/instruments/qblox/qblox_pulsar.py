"""Qblox pulsar class"""
from qililab.instruments.instrument import Instrument
from qililab.settings import QbloxPulsarSettings
from qililab.typings import Pulsar


class QbloxPulsar(Instrument):
    """Pulsar class

    Args:
        name (str): Name of the instrument.
        device (Pulsar): Instance of the Qblox Pulsar class.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    device: Pulsar
    settings: QbloxPulsarSettings

    def __init__(self, name: str):
        super().__init__(name=name)

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        super().connect()
        self.initial_setup()

    @Instrument.CheckConnected
    def start(self):
        """Execute the uploaded instructions."""
        self.device.arm_sequencer()
        self.device.start_sequencer()

    @Instrument.CheckConnected
    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._set_gain()

    @Instrument.CheckConnected
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        self.device.stop_sequencer()

    @Instrument.CheckConnected
    def reset(self):
        """Reset instrument."""
        self.device.reset()

    @Instrument.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        self._set_reference_source()
        self._set_sync_enabled()

    @Instrument.CheckConnected
    def upload(self, sequence_path: str):
        """Upload sequence to sequencer.

        Args:
            sequence_path (str): Path to the json file containing the waveforms,
            weights, acquisitions and program of the sequence.
        """
        getattr(self.device, f"sequencer{self.settings.sequencer}").sequence(sequence_path)

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        getattr(self.device, f"sequencer{self.settings.sequencer}").gain_awg_path0(self.settings.gain)
        getattr(self.device, f"sequencer{self.settings.sequencer}").gain_awg_path1(self.settings.gain)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.settings.reference_clock)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        getattr(self.device, f"sequencer{self.settings.sequencer}").sync_en(self.settings.sync_enabled)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        self.device = Pulsar(name=self.name, identifier=self.settings.ip)
