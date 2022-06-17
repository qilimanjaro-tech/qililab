"""Qblox pulsar QRM class"""
from pathlib import Path

from qpysequence.acquisitions import Acquisitions
from qpysequence.instructions.real_time import Acquire
from qpysequence.loop import Loop

from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_readout import QubitReadout
from qililab.pulse import PulseSequence
from qililab.result import QbloxResult
from qililab.typings import (
    AcquireTriggerMode,
    AcquisitionName,
    BusElementName,
    IntegrationMode,
)
from qililab.utils import Factory, nested_dataclass


@Factory.register
class QbloxPulsarQRM(QbloxPulsar, QubitReadout):
    """Qblox pulsar QRM class.

    Args:
        settings (QBloxPulsarQRMSettings): Settings of the instrument.
    """

    name = BusElementName.QBLOX_QRM

    @nested_dataclass
    class QbloxPulsarQRMSettings(QbloxPulsar.QbloxPulsarSettings, QubitReadout.QubitReadoutSettings):
        """Contains the settings of a specific pulsar.

        Args:
            acquire_trigger_mode (str): Set scope acquisition trigger mode. Options are 'sequencer' or 'level'.
            scope_acquisition_averaging (bool): Enable/disable hardware averaging of the data.
            integration_length (int): Duration (in ns) of the integration.
            integration_mode (str): Integration mode. Options are 'ssb'.
            sequence_timeout (int): Time (in minutes) to wait for the sequence to finish.
            If timeout is reached a TimeoutError is raised.
            acquisition_timeout (int): Time (in minutes) to wait for the acquisition to finish.
            If timeout is reached a TimeoutError is raised.
            acquisition_name (str): Name of the acquisition saved in the sequencer.
        """

        acquire_trigger_mode: AcquireTriggerMode
        scope_acquisition_averaging: bool
        sampling_rate: int
        integration_length: int
        integration_mode: IntegrationMode
        sequence_timeout: int  # minutes
        acquisition_timeout: int  # minutes
        acquisition_name: AcquisitionName

    acquisition_idx: int
    settings: QbloxPulsarQRMSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.QbloxPulsarQRMSettings(**settings)

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run execution of a pulse sequence. Return acquisition results.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.

        Returns:
            Dict: Returns a dict with the acquisitions for the QRM and None for the QCM.
        """
        if (pulse_sequence, nshots, repetition_duration) == self._cache:
            # TODO: Right now the only way of deleting the acquisition data is to re-upload the acquisition dictionary.
            self.device._delete_acquisition(sequencer=self.sequencer, name=self.acquisition_name.value)
            acquisition = self._generate_acquisitions()
            self.device._add_acquisitions(sequencer=self.sequencer, acquisitions=acquisition.to_dict())
        super().run(pulse_sequence=pulse_sequence, nshots=nshots, repetition_duration=repetition_duration, path=path)
        return self.get_acquisitions()

    @QbloxPulsar.CheckConnected
    def setup(self):
        """Connect to the instrument, reset it and configure its reference source and synchronization settings."""
        super().setup()
        self._set_hardware_averaging()
        self._set_acquisition_mode()

    @QbloxPulsar.CheckConnected
    def get_acquisitions(self):
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        self.device.get_sequencer_state(sequencer=self.sequencer, timeout=self.sequence_timeout)
        self.device.get_acquisition_state(sequencer=self.sequencer, timeout=self.acquisition_timeout)
        self.device.store_scope_acquisition(sequencer=self.sequencer, name=self.acquisition_name.value)
        result = self.device.get_acquisitions(sequencer=self.sequencer)[self.acquisition_name.value]["acquisition"][
            "bins"
        ]
        return QbloxResult(**result)

    def _set_nco(self):
        """Enable modulation of pulses and setup NCO frequency."""
        super()._set_nco()
        getattr(self.device, f"sequencer{self.sequencer}").demod_en_acq(True)

    def _set_hardware_averaging(self):
        """Enable/disable hardware averaging of the data for all paths."""
        self.device.scope_acq_avg_mode_en_path0(self.scope_acquisition_averaging)
        self.device.scope_acq_avg_mode_en_path1(self.scope_acquisition_averaging)

    def _set_acquisition_mode(self):
        """Set scope acquisition trigger mode for all paths. Options are 'sequencer' or 'level'."""
        self.device.scope_acq_sequencer_select(self.sequencer)
        self.device.scope_acq_trigger_mode_path0(self.acquire_trigger_mode.value)
        self.device.scope_acq_trigger_mode_path1(self.acquire_trigger_mode.value)
        getattr(self.device, f"sequencer{self.sequencer}").integration_length_acq(int(self.integration_length))

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "single", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        acquisitions = super()._generate_acquisitions()
        acquisitions.add(name="single", num_bins=1, index=0)
        acquisitions.add(name="large", num_bins=self.MAX_BINS, index=1)
        self.acquisition_idx = acquisitions.find_by_name(name=self.acquisition_name.value).index
        return acquisitions

    def _append_acquire_instruction(self, loop: Loop):
        """Append an acquire instruction to the loop."""
        loop.append_component(Acquire(acq_index=self.acquisition_idx, bin_index=0, wait_time=4))

    @property
    def acquire_trigger_mode(self):
        """QbloxPulsarQRM 'acquire_trigger_mode' property.

        Returns:
            AcquireTriggerMode: settings.acquire_trigger_mode.
        """
        return self.settings.acquire_trigger_mode

    @property
    def scope_acquisition_averaging(self):
        """QbloxPulsarQRM 'scope_acquisition_averaging' property.

        Returns:
            bool: settings.scope_acquisition_averaging.
        """
        return self.settings.scope_acquisition_averaging

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
    def final_wait_time(self) -> int:
        """QbloxPulsarQRM 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self.delay_time
