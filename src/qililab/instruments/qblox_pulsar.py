"""Qblox pulsar class"""
from numpy import isin
from pulsar_qcm.pulsar_qcm import pulsar_qcm
from pulsar_qrm.pulsar_qrm import pulsar_qrm

from qililab.instruments.instrument import Instrument
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.qblox_pulsar import QbloxPulsarSettings


class QbloxPulsar(Instrument):
    """Pulsar class

    Args:
        device (pulsar_qrm | pulsar_qcm): Instance of the Qblox instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    def __init__(self, name: str):
        self.device: pulsar_qrm | pulsar_qcm
        self.settings = SETTINGS_MANAGER.load(filename=name)
        if not isinstance(self.settings, QbloxPulsarSettings):
            raise ValueError(
                """The wrong settings class has been loaded.
                             Please correct the category of the settings"""
            )
        super().__init__()
        self.connect()
        self.initial_setup()

    def initial_setup(self):
        """Initial setup of the instrument."""
        self.connect()
        self.reset()
        self._set_reference_source()
        self._set_sync_enabled()

    def setup(self):
        """Sets Qblox instrument calibration settings."""
        self._set_gain()

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        sequencer = self.settings.sequencer
        getattr(self.device, f"sequencer{sequencer}_gain_awg_path0")(self.settings.gain)
        getattr(self.device, f"sequencer{sequencer}_gain_awg_path1")(self.settings.gain)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.settings.reference_clock)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        sequencer = self.settings.sequencer
        getattr(self.device, f"sequencer{sequencer}_sync_en")(self.settings.sync_enabled)

    def stop(self):
        """Stops the QBlox sequencer from sending pulses."""
        self.device.stop_sequencer()

    def close(self):
        """Disconnects from the instrument."""
        if self._connected:
            self.stop()
            self.device.close()
            self._connected = False

    def reset(self):
        """Reset instrument."""
        self.device.reset()
