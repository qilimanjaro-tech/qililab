"""Qblox pulsar QRM class"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire

from qililab.instruments.instrument import Instrument
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseBusSchedule
from qililab.result import QbloxResult
from qililab.typings.enums import AcquireTriggerMode, InstrumentName, IntegrationMode


@InstrumentFactory.register
class QbloxQRM(QbloxModule, QubitReadout):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM

    @dataclass
    class QbloxQRMSettings(QbloxModule.QbloxModuleSettings, QubitReadout.QubitReadoutSettings):
        """Contains the settings of a specific pulsar.

        Args:
            acquire_trigger_mode (str): Set scope acquisition trigger mode. Options are 'sequencer' or 'level'.
            scope_hardware_averaging (bool): Enable/disable hardware averaging of the data during scope mode.
            integration_length (int): Duration (in ns) of the integration.
            integration_mode (str): Integration mode. Options are 'ssb'.
            sequence_timeout (int): Time (in minutes) to wait for the sequence to finish.
            If timeout is reached a TimeoutError is raised.
            acquisition_timeout (int): Time (in minutes) to wait for the acquisition to finish.
            If timeout is reached a TimeoutError is raised.
            acquisition_name (str): Name of the acquisition saved in the sequencer.
        """

        scope_acquire_trigger_mode: AcquireTriggerMode
        scope_hardware_averaging: bool
        sampling_rate: int
        integration: bool  # integration flag
        integration_length: int
        integration_mode: IntegrationMode
        sequence_timeout: int  # minutes
        acquisition_timeout: int  # minutes

    settings: QbloxQRMSettings

    def _check_cached_values(self, pulse_sequence: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path):
        """check if values are already cached and upload if not cached"""
        readout_pulse_duration = pulse_sequence.readout_pulse_duration
        if self.integration_length != readout_pulse_duration:
            self._update_integration_length_with_readout_pulse_duration(readout_pulse_duration=readout_pulse_duration)
        super()._check_cached_values(
            pulse_sequence=pulse_sequence,
            nshots=nshots,
            repetition_duration=repetition_duration,
            path=path,
        )

    def _update_integration_length_with_readout_pulse_duration(self, readout_pulse_duration: int):
        """update integration length with readout pulse duration and performs a new setup to
        the instrument to update the values"""
        self.settings.integration_length = readout_pulse_duration
        self.setup()

    def run(self, pulse_sequence: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path) -> QbloxResult:
        """Run execution of a pulse sequence. Return acquisition results.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.

        Returns:
            Dict: Returns a dict with the acquisitions for the QRM and None for the QCM.
        """
        if (pulse_sequence, nshots, repetition_duration) == self._cache:
            # TODO: Right now the only way of deleting the acquisition data is to re-upload the acquisition dictionary.
            for seq_idx in range(self.num_sequencers):
                self.device._delete_acquisition(  # pylint: disable=protected-access
                    sequencer=seq_idx, name=self.acquisition_name
                )
                acquisition = self._generate_acquisitions()
                self.device._add_acquisitions(  # pylint: disable=protected-access
                    sequencer=seq_idx, acquisitions=acquisition.to_dict()
                )
        super().run(pulse_sequence=pulse_sequence, nshots=nshots, repetition_duration=repetition_duration, path=path)
        return self.get_acquisitions()

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Connect to the instrument, reset it and configure its reference source and synchronization settings."""
        super().setup()
        self._set_scope_hardware_averaging()
        self._set_acquisition_mode()

    @Instrument.CheckDeviceInitialized
    def get_acquisitions(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        for seq_idx in range(self.num_sequencers):
            self.device.get_sequencer_state(sequencer=seq_idx, timeout=self.sequence_timeout)
            self.device.get_acquisition_state(sequencer=seq_idx, timeout=self.acquisition_timeout)
        if not self.integration:
            self.device.store_scope_acquisition(sequencer=0, name=self.acquisition_name)
            result = self.device.get_acquisitions(sequencer=0)[self.acquisition_name]["acquisition"][self.data_name]
            return QbloxResult(pulse_length=self.integration_length, scope=result)

        results = [
            self.device.get_acquisitions(sequencer=seq_idx)[self.acquisition_name]["acquisition"][self.data_name]
            for seq_idx in range(self.num_sequencers)
        ]

        return QbloxResult(pulse_length=self.integration_length, bins=results)

    def _set_nco(self):
        """Enable modulation of pulses and setup NCO frequency."""
        super()._set_nco()
        for seq_idx in range(self.num_sequencers):
            self.device.sequencers[seq_idx].demod_en_acq(True)

    def _set_scope_hardware_averaging(self):
        """Enable/disable hardware averaging of the data for all paths."""
        self.device.scope_acq_avg_mode_en_path0(self.scope_hardware_averaging)
        self.device.scope_acq_avg_mode_en_path1(self.scope_hardware_averaging)

    def _set_acquisition_mode(self):
        """Set scope acquisition trigger mode for all paths. Options are 'sequencer' or 'level'."""
        self.device.scope_acq_sequencer_select(0)
        self.device.scope_acq_trigger_mode_path0(self.scope_acquire_trigger_mode.value)
        self.device.scope_acq_trigger_mode_path1(self.scope_acquire_trigger_mode.value)
        if self.integration:
            for seq_idx in range(self.num_sequencers):
                self.device.sequencers[seq_idx].integration_length_acq(int(self.integration_length))
                self.device.sequencers[seq_idx].integration_length_acq(int(self.integration_length))

    def _append_acquire_instruction(self, loop: Loop, register: Register):
        """Append an acquire instruction to the loop."""
        acquisition_idx = 0 if self.scope_hardware_averaging else 1  # use binned acquisition if averaging is false
        loop.append_component(Acquire(acq_index=acquisition_idx, bin_index=register, wait_time=self._MIN_WAIT_TIME))

    @property
    def scope_acquire_trigger_mode(self):
        """QbloxPulsarQRM 'acquire_trigger_mode' property.

        Returns:
            AcquireTriggerMode: settings.acquire_trigger_mode.
        """
        return self.settings.scope_acquire_trigger_mode

    @property
    def scope_hardware_averaging(self):
        """QbloxPulsarQRM 'scope_hardware_averaging' property.

        Returns:
            bool: settings.scope_hardware_averaging.
        """
        return self.settings.scope_hardware_averaging

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
    def final_wait_time(self) -> int:
        """QbloxPulsarQRM 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self.acquisition_delay_time

    @property
    def integration(self) -> bool:
        """QbloxPulsarQRM 'integration' property.

        Returns:
            bool: Integration flag.
        """
        return self.settings.integration

    @property
    def data_name(self) -> str:
        """QbloxPulsarQRM 'data_name' property:

        Returns:
            str: Name of the data. Options are "bins" or "scope".
        """
        return "bins" if self.integration else "scope"

    @property
    def acquisition_name(self) -> str:
        """QbloxPulsarQRM 'acquisition_name' property:

        Returns:
            str: Name of the acquisition. Options are "single" or "binning".
        """
        return "single" if self.scope_hardware_averaging else "binning"
