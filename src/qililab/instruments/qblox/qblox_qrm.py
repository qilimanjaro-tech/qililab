"""Qblox pulsar QRM class"""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire

from qililab.instruments.instrument import Instrument
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.qubit_readout import AWGReadout
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseBusSchedule
from qililab.result import QbloxResult
from qililab.typings.enums import (
    AcquireTriggerMode,
    InstrumentName,
    IntegrationMode,
    Parameter,
)


@InstrumentFactory.register
class QbloxQRM(QbloxModule, AWGReadout):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM
    _NUM_SEQUENCERS: int = 2

    @dataclass
    class QbloxQRMSettings(QbloxModule.QbloxModuleSettings, AWGReadout.AWGReadoutSettings):
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
        sampling_rate: List[int]  # default sampling rate for Qblox is 1.e+09
        hardware_integration: List[bool]  # integration flag
        hardware_demodulation: List[bool]  # demodulation flag
        integration_length: List[int]
        integration_mode: List[IntegrationMode]
        sequence_timeout: List[int]  # minutes
        acquisition_timeout: List[int]  # minutes

    settings: QbloxQRMSettings

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        for channel_id in range(self.num_sequencers):
            self._set_integration_length(value=self.settings.integration_length[channel_id], channel_id=channel_id)
            self._set_acquisition_mode(
                value=self.settings.scope_acquire_trigger_mode[channel_id], channel_id=channel_id
            )
            self._set_scope_hardware_averaging(
                value=self.settings.scope_hardware_averaging[channel_id], channel_id=channel_id
            )

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetitition duration
            path (Path): path to save the program to upload
        """
        if (pulse_bus_schedule, nshots, repetition_duration) == self._cache:
            # TODO: Right now the only way of deleting the acquisition data is to re-upload the acquisition dictionary.
            for seq_idx in range(self.num_sequencers):
                self.device._delete_acquisition(  # pylint: disable=protected-access
                    sequencer=seq_idx, name=self.acquisition_name
                )
                acquisition = self._generate_acquisitions()
                self.device._add_acquisitions(  # pylint: disable=protected-access
                    sequencer=seq_idx, acquisitions=acquisition.to_dict()
                )
        super().generate_program_and_upload(
            pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, path=path
        )

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        return self.get_acquisitions()

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        super().setup(parameter=parameter, value=value, channel_id=channel_id)
        if parameter.value == Parameter.HARDWARE_AVERAGE.value:
            self._set_scope_hardware_averaging(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.HARDWARE_DEMODULATION.value:
            self._set_hardware_demodulation(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.ACQUISITION_MODE.value:
            self._set_acquisition_mode(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.INTEGRATION_LENGTH.value:
            self._set_integration_length(value=value, channel_id=channel_id)
            return
        raise ValueError(f"Invalid Parameter: {parameter.value}")

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

    def _set_acquisition_mode(self, value: float | str | bool | AcquireTriggerMode, channel_id: int):
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

    def _set_scope_hardware_averaging(self, value: float | str | bool, channel_id: int):
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
            self.device.store_scope_acquisition(sequencer=sequencer, name=self.acquisition_name(sequencer=sequencer))
        return self.device.get_acquisitions(sequencer=sequencer)[self.acquisition_name(sequencer=sequencer)][
            "acquisition"
        ][self.data_name(sequencer=sequencer)]

    def _set_nco(self, channel_id: int):
        """Enable modulation/demodulation of pulses and setup NCO frequency."""
        super()._set_nco(channel_id=channel_id)
        if self.settings.hardware_demodulation[channel_id]:
            self._set_hardware_demodulation(value=self.settings.hardware_modulation[channel_id], channel_id=channel_id)

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

    def _append_acquire_instruction(self, loop: Loop, register: Register):
        """Append an acquire instruction to the loop."""
        # FIXME: scope_hardware_averaging it is a list now, it should return the desired channel
        acquisition_idx = 0 if self.scope_hardware_averaging[0] else 1  # use binned acquisition if averaging is false
        loop.append_component(Acquire(acq_index=acquisition_idx, bin_index=register, wait_time=self._MIN_WAIT_TIME))

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "single", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        acquisitions = Acquisitions()
        acquisitions.add(name="single", num_bins=1, index=0)
        # FIXME: using first channel instead of the desired
        acquisitions.add(name="binning", num_bins=int(self.num_bins[0]) + 1, index=1)  # binned acquisition
        return acquisitions

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

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

    def acquisition_name(self, sequencer: int) -> str:
        """QbloxPulsarQRM 'acquisition_name' property:

        Returns:
            str: Name of the acquisition. Options are "single" or "binning".
        """
        return "single" if self.scope_hardware_averaging[sequencer] else "binning"
