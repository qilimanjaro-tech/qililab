"""Qblox pulsar class"""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.typings import Pulsar, ReferenceClock


class QbloxPulsar(Instrument):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxPulsarSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific pulsar.

        Args:
            reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
            sequencer (int): Index of the sequencer to use.
            sync_enabled (bool): Enable synchronization over multiple instruments.
            gain (float): Gain step used by the sequencer.
        """

        reference_clock: ReferenceClock
        sequencer: int
        sync_enabled: bool
        gain: float

        def __post_init__(self):
            """Cast reference_clock to its corresponding Enum class"""
            super().__post_init__()
            self.reference_clock = ReferenceClock(self.reference_clock)

    device: Pulsar
    settings: QbloxPulsarSettings

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
        getattr(self.device, f"sequencer{self.sequencer}").sequence(sequence_path)

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path0(self.gain)
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path1(self.gain)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.reference_clock)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        getattr(self.device, f"sequencer{self.sequencer}").sync_en(self.sync_enabled)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        self.device = Pulsar(name=self.name, identifier=self.ip)

    @property
    def reference_clock(self):
        """QbloxPulsar 'reference_clock' property.

        Returns:
            ReferenceClock: settings.reference_clock.
        """
        return self.settings.reference_clock

    @property
    def sequencer(self):
        """QbloxPulsar 'sequencer' property.

        Returns:
            int: settings.sequencer.
        """
        return self.settings.sequencer

    @property
    def sync_enabled(self):
        """QbloxPulsar 'sync_enabled' property.

        Returns:
            bool: settings.sync_enabled.
        """
        return self.settings.sync_enabled

    @property
    def gain(self):
        """QbloxPulsar 'gain' property.

        Returns:
            float: settings.gain.
        """
        return self.settings.gain
