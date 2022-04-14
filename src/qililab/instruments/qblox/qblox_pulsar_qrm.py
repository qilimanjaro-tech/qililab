"""Qblox pulsar QRM class"""
from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_readout import QubitReadout
from qililab.settings import QbloxPulsarQRMSettings


class QbloxPulsarQRM(QbloxPulsar, QubitReadout):
    """Pulsar QCM class"""

    settings: QbloxPulsarQRMSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = QbloxPulsarQRMSettings(**settings)

    @QbloxPulsar.CheckConnected
    def setup(self):
        """Connect to the instrument, reset it and configure its reference source and synchronization settings."""
        super().setup()
        self._set_hardware_averaging()
        self._set_acquisition_mode()

    @QbloxPulsar.CheckConnected
    def get_acquisitions(self) -> dict:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised. The returned dictionary is structured as follows:

        - name: acquisition name.
            - index: acquisition index used by the sequencer Q1ASM program to refer to the acquisition.
            - acquisition: acquisition dictionary.
                - scope: Scope data.
                    -path0: input path 0.
                        - data: acquisition samples in a range of 1.0 to -1.0.
                        - out-of-range: out-of-range indication for the entire
                        acquisition (False=in-range, True=out-of-range).
                        - avg_cnt: number of averages.
                    - path1: input path 1
                        - data: acquisition samples in a range of 1.0 to -1.0.
                        - out-of-range: out-of-range indication for the entire
                        acquisition (False=in-range, True=out-of-range).
                        - avg_cnt: number of averages.
                - bins: bin data.
                    - integration: integration data.
                        - path_0: input path 0 integration result bin list.
                        - path_1: input path 1 integration result bin list.
                    - threshold: threshold result bin list.
                    - valid: list of valid indications per bin.
                    - avg_cnt: list of number of averages per bin.
        Returns:
            dict: Dictionary with the acquisition results.

        """
        self.device.get_sequencer_state(sequencer=self.settings.sequencer, timeout=self.settings.sequence_timeout)
        self.device.get_acquisition_state(sequencer=self.settings.sequencer, timeout=self.settings.acquisition_timeout)
        self.device.store_scope_acquisition(sequencer=self.settings.sequencer, name=self.settings.acquisition_name)
        acquisitions = self.device.get_acquisitions(sequencer=self.settings.sequencer)
        return acquisitions

    def _set_hardware_averaging(self):
        """Enable/disable hardware averaging of the data for all paths."""
        self.device.scope_acq_avg_mode_en_path0(self.settings.hardware_average_enabled)
        self.device.scope_acq_avg_mode_en_path1(self.settings.hardware_average_enabled)

    def _set_acquisition_mode(self):
        """Set scope acquisition trigger mode for all paths. Options are 'sequencer' or 'level'."""
        self.device.scope_acq_trigger_mode_path0(self.settings.acquire_trigger_mode)
        self.device.scope_acq_trigger_mode_path1(self.settings.acquire_trigger_mode)
