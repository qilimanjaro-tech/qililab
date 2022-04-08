"""Qblox pulsar class"""
from qblox_instruments import Pulsar

from qililab.instruments.instrument import Instrument
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.instruments.qblox.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.settings.instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRMSettings


class QbloxPulsar(Instrument):
    """Pulsar class

    Args:
        name (str): Name of the instrument.
        device (Pulsar): Instance of the Qblox Pulsar class.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    def __init__(self, name: str):
        super().__init__(name=name)
        self.device: Pulsar | None = None
        self.settings = self.load_settings()

    def load_settings(self):
        """Load instrument settings"""
        settings = SETTINGS_MANAGER.load(filename=self.name)
        # FIXME: Can't use parent class (QbloxPulsarSettings) in isinstance, because
        # then mypy can't infer the type of 'hardware_average_enabled' int the QbloxPulsarQRM class
        if not isinstance(settings, (QbloxPulsarQRMSettings, QbloxPulsarQCMSettings)):
            raise ValueError(
                f"""Using instance of class {type(settings).__name__} instead of class QbloxPulsarSettings."""
            )
        return settings

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        if not self._connected:
            # TODO: We need to update the firmware of the instruments to be able to connect
            self.device = Pulsar(name=self.name, identifier=self.settings.ip)
            self._connected = True
            self.initial_setup()

    def start(self):
        """Execute the uploaded instructions."""
        # FIXME: Find a solution to check the connection before running all methods (except connect and load_settings)
        # without having to call self._check_connected() every time.
        self._check_connected()
        self.device.arm_sequencer()
        self.device.start_sequencer()

    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        self._check_connected()
        self.device.stop_sequencer()

    def close(self):
        """Disconnect from the instrument."""
        self._check_connected()
        self.stop()
        self.device.close()
        self._connected = False

    def reset(self):
        """Reset instrument."""
        self._check_connected()
        self.device.reset()

    def initial_setup(self):
        """Initial setup of the instrument."""
        self._check_connected()
        self._set_reference_source()
        self._set_sync_enabled()

    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._check_connected()
        self._set_gain()

    def upload(self, sequence_path: str):
        """Upload sequence to sequencer.

        Args:
            sequence_path (str): Path to the json file containing the waveforms,
            weights, acquisitions and program of the sequence.
        """
        self.device.sequencer0.sequence(sequence_path)
        self.device.sequencer1.sequence(sequence_path)

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        self._check_connected()
        sequencer = self.settings.sequencer
        getattr(self.device, f"sequencer{sequencer}_gain_awg_path0")(self.settings.gain)
        getattr(self.device, f"sequencer{sequencer}_gain_awg_path1")(self.settings.gain)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self._check_connected()
        self.device.reference_source(self.settings.reference_clock)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        self._check_connected()
        sequencer = self.settings.sequencer
        getattr(self.device, f"sequencer{sequencer}_sync_en")(self.settings.sync_enabled)
