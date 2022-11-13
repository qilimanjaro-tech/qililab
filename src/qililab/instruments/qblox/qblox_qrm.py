"""Qblox pulsar QRM class"""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire

from qililab.instruments.instrument import Instrument
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSequence
from qililab.result import QbloxResult
from qililab.typings.enums import (
    AcquireTriggerMode,
    InstrumentName,
    IntegrationMode,
    Parameter,
)


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

        scope_acquire_trigger_mode: List[AcquireTriggerMode]
        scope_hardware_averaging: List[bool]
        sampling_rate: List[int]
        hardware_integration: List[bool]  # integration flag
        hardware_demodulation: List[bool]  # demodulation flag
        integration_length: List[int]
        integration_mode: List[IntegrationMode]
        sequence_timeout: List[int]  # minutes
        acquisition_timeout: List[int]  # minutes

    settings: QbloxQRMSettings

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path) -> QbloxResult:
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
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        super().setup(parameter=parameter, value=value, channel_id=channel_id)
        if parameter.value == Parameter.HARDWARE_AVERAGE:
            self._set_scope_hardware_averaging_one_channel(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.HARDWARE_DEMODULATION:
            self._set_scope_hardware_averaging_one_channel(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.ACQUISITION_MODE:
            self._set_acquisition_mode_one_channel(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.INTEGRATION_LENGTH:
            self._set_integration_length(value=value, channel_id=channel_id)
            return

    def _set_hardware_demodulation(self, value: float | str | bool, channel_id: int):
        """set hardware demodulation

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if not isinstance(value, bool):
            raise ValueError(f"value must be a bool. Current type: {type(value)}")
        self.settings.hardware_demodulation[channel_id] = value
        self.device.sequencers[channel_id].demod_en_acq(value)

    def _set_acquisition_mode_one_channel(self, value: float | str | bool | AcquireTriggerMode, channel_id: int):
        """set acquisition_mode for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        if not isinstance(value, AcquireTriggerMode) and not isinstance(value, str):
            raise ValueError(f"value must be a string or AcquireTriggerMode. Current type: {type(value)}")
        self.settings.scope_acquire_trigger_mode[channel_id] = AcquireTriggerMode(value)
        self.device.scope_acq_sequencer_select(channel_id)
        self.device.scope_acq_trigger_mode_path0(self.scope_acquire_trigger_mode[channel_id].value)
        self.device.scope_acq_trigger_mode_path1(self.scope_acquire_trigger_mode[channel_id].value)

    def _set_integration_length(self, value: int | float | str | bool, channel_id: int):
        """set integration_length for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        if not isinstance(value, int) and not isinstance(value, float):
            raise ValueError(f"value must be a int or float. Current type: {type(value)}")
        self.settings.integration_length[channel_id] = int(value)
        self.device.sequencers[channel_id].integration_length_acq(self.integration_length)

    def _set_scope_hardware_averaging_one_channel(self, value: float | str | bool, channel_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if not isinstance(value, bool):
            raise ValueError(f"value must be a bool. Current type: {type(value)}")
        self.settings.scope_hardware_averaging[channel_id] = value
        self.device.scope_acq_sequencer_select(channel_id)
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

    def _acquire_result_one_sequencer(self, sequencer: int):
        """Acquire result for one sequencer

        Args:
            sequencer (int): _description_

        Returns:
            _type_: _description_
        """
        self.device.get_sequencer_state(sequencer=sequencer, timeout=self.sequence_timeout)
        self.device.get_acquisition_state(sequencer=sequencer, timeout=self.acquisition_timeout)
        if not self.hardware_integration[sequencer]:
            self.device.store_scope_acquisition(sequencer=sequencer, name=self.acquisition_name)
        return self.device.get_acquisitions(sequencer=sequencer)[self.acquisition_name]["acquisition"][
            self.data_name(sequencer=sequencer)
        ]

    @Instrument.CheckDeviceInitialized
    def get_acquisitions(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        results = [self._acquire_result_one_sequencer(sequencer=sequencer) for sequencer in range(self.num_sequencers)]

        # FIXME: the results are created into a QbloxResult with always a bins structure
        # it needs to accept a result that contains both scope and bins instead of one or the other
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
        for seq_idx in range(self.num_sequencers):
            self._set_acquisition_mode_one_channel(
                value=self.scope_acquire_trigger_mode[seq_idx].value, channel_id=seq_idx
            )
            if self.hardware_integration[seq_idx]:
                self._set_integration_length(value=self.integration_length, channel_id=seq_idx)

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
    def hardware_integration(self):
        """QbloxPulsarQRM 'integration' property.

        Returns:
            bool: Integration flag.
        """
        return self.settings.hardware_integration

    def data_name(self, sequencer: int) -> str:
        """QbloxPulsarQRM 'data_name' property:

        Returns:
            str: Name of the data. Options are "bins" or "scope".
        """
        return "bins" if self.hardware_integration[sequencer] else "scope"

    @property
    def acquisition_name(self) -> str:
        """QbloxPulsarQRM 'acquisition_name' property:

        Returns:
            str: Name of the acquisition. Options are "single" or "binning".
        """
        return "single" if self.scope_hardware_averaging else "binning"
