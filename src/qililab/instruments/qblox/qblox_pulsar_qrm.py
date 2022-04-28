"""Qblox pulsar QRM class"""
from dataclasses import dataclass

from qililab.instruments.pulse.pulse_sequence import PulseSequence
from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_readout import QubitReadout
from qililab.typings import AcquireTriggerMode, IntegrationMode


class QbloxPulsarQRM(QbloxPulsar, QubitReadout):
    """Qblox pulsar QRM class.

    Args:
        settings (QBloxPulsarQRMSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxPulsarQRMSettings(QbloxPulsar.QbloxPulsarSettings, QubitReadout.QubitReadoutSettings):
        """Contains the settings of a specific pulsar.

        Args:
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
            delay_before_readout (int): Delay (ns) between the readout pulse and the acquisition.
        """

        acquire_trigger_mode: AcquireTriggerMode
        hardware_average_enabled: bool
        start_integrate: int
        sampling_rate: int
        integration_length: int
        integration_mode: IntegrationMode
        sequence_timeout: int  # minutes
        acquisition_timeout: int  # minutes
        acquisition_name: str
        delay_before_readout: int  # ns

        def __post_init__(self):
            """Cast acquire_trigger_mode and integration_mode to its corresponding Enum classes"""
            super().__post_init__()
            self.acquire_trigger_mode = AcquireTriggerMode(self.acquire_trigger_mode)
            self.integration_mode = IntegrationMode(self.integration_mode)

    settings: QbloxPulsarQRMSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.QbloxPulsarQRMSettings(**settings)

    def execute(self, pulse_sequence: PulseSequence):
        """Run execution of a pulse sequence. Return acquisition results.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.

        Returns:
            Dict: Returns a dict with the acquisitions for the QRM and None for the QCM.
        """
        super().execute(pulse_sequence=pulse_sequence)
        return self.get_acquisitions()

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
        self.device.get_sequencer_state(sequencer=self.sequencer, timeout=self.sequence_timeout)
        self.device.get_acquisition_state(sequencer=self.sequencer, timeout=self.acquisition_timeout)
        self.device.store_scope_acquisition(sequencer=self.sequencer, name=self.acquisition_name)
        return self.device.get_acquisitions(sequencer=self.sequencer)

    def _set_hardware_averaging(self):
        """Enable/disable hardware averaging of the data for all paths."""
        self.device.scope_acq_avg_mode_en_path0(self.hardware_average_enabled)
        self.device.scope_acq_avg_mode_en_path1(self.hardware_average_enabled)

    def _set_acquisition_mode(self):
        """Set scope acquisition trigger mode for all paths. Options are 'sequencer' or 'level'."""
        self.device.scope_acq_trigger_mode_path0(self.acquire_trigger_mode)
        self.device.scope_acq_trigger_mode_path1(self.acquire_trigger_mode)

    @property
    def acquire_trigger_mode(self):
        """QbloxPulsarQRM 'acquire_trigger_mode' property.

        Returns:
            AcquireTriggerMode: settings.acquire_trigger_mode.
        """
        return self.settings.acquire_trigger_mode

    @property
    def hardware_average_enabled(self):
        """QbloxPulsarQRM 'hardware_average_enabled' property.

        Returns:
            bool: settings.hardware_average_enabled.
        """
        return self.settings.hardware_average_enabled

    @property
    def start_integrate(self):
        """QbloxPulsarQRM 'start_integrate' property.

        Returns:
            int: settings.start_integrate.
        """
        return self.settings.start_integrate

    @property
    def sampling_rate(self):
        """QbloxPulsarQRM 'sampling_rate' property.

        Returns:
            int: settings.sampling_rate.
        """
        return self.settings.sampling_rate

    @property
    def integration_length(self):
        """QbloxPulsarQRM 'integration_length' property.

        Returns:
            int: settings.integration_length.
        """
        return self.settings.integration_length

    @property
    def integration_mode(self):
        """QbloxPulsarQRM 'integration_mode' property.

        Returns:
            IntegrationMode: settings.integration_mode.
        """
        return self.settings.integration_mode

    @property
    def sequence_timeout(self):
        """QbloxPulsarQRM 'sequence_timeout' property.

        Returns:
            int: settings.sequence_timeout.
        """
        return self.settings.sequence_timeout

    @property
    def acquisition_timeout(self):
        """QbloxPulsarQRM 'acquisition_timeout' property.

        Returns:
            int: settings.acquisition_timeout.
        """
        return self.settings.acquisition_timeout

    @property
    def acquisition_name(self):
        """QbloxPulsarQRM 'acquisition_name' property.

        Returns:
            str: settings.acquisition_name.
        """
        return self.settings.acquisition_name

    @property
    def delay_before_readout(self):
        """QbloxPulsar 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.delay_before_readout
