"""Qblox pulsar QRM class"""
from qililab.instruments.qblox_pulsar import QbloxPulsar


class QbloxPulsarQRM(QbloxPulsar):
    """Pulsar QCM class"""

    def setup(self):
        """Connect to the instrument, reset it and configure its reference source and synchronization settings."""
        super().setup()
        self._set_hardware_averaging()
        self._set_acquisition_mode()

    def _set_hardware_averaging(self):
        """Enable/disable hardware averaging of the data for all paths."""
        self.device.scope_acq_avg_mode_en_path0(self.settings.hardware_average_enabled)
        self.device.scope_acq_avg_mode_en_path1(self.settings.hardware_average_enabled)

    def _set_acquisition_mode(self):
        """Set scope acquisition trigger mode for all paths. Options are 'sequencer' or 'level'."""
        self.device.scope_acq_trigger_mode_path0(self.settings.acquire_trigger_mode)
        self.device.scope_acq_trigger_mode_path1(self.settings.acquire_trigger_mode)
