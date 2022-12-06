"""Qblox pulsar QRM class"""
from dataclasses import dataclass
from pathlib import Path

from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire

from qililab.instruments.digital_analog_converter import AWGDigitalAnalogConverter
from qililab.instruments.instrument import Instrument
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseBusSchedule
from qililab.result import QbloxResult
from qililab.typings.enums import AcquireTriggerMode, InstrumentName, Parameter


@InstrumentFactory.register
class QbloxQRM(QbloxModule, AWGDigitalAnalogConverter):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM
    _NUM_SEQUENCERS: int = 1

    @dataclass
    class QbloxQRMSettings(
        QbloxModule.QbloxModuleSettings, AWGDigitalAnalogConverter.AWGDigitalAnalogConverterSettings
    ):
        """Contains the settings of a specific QRM."""

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
            self._set_hardware_demodulation(
                value=self.settings.hardware_demodulation[channel_id], channel_id=channel_id
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

    def _set_device_hardware_demodulation(self, value: bool, channel_id: int):
        """set hardware demodulation

        Args:
            value (bool): value to update
            channel_id (int): sequencer to update the value
        """
        self.device.sequencers[channel_id].demod_en_acq(value)

    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, channel_id: int):
        """set acquisition_mode for the specific channel

        Args:
            mode (AcquireTriggerMode): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        self.device.scope_acq_sequencer_select(channel_id)
        self.device.scope_acq_trigger_mode_path0(mode.value)
        self.device.scope_acq_trigger_mode_path1(mode.value)

    def _set_device_integration_length(self, value: int, channel_id: int):
        """set integration_length for the specific channel

        Args:
            value (int): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.device.sequencers[channel_id].integration_length_acq(value)

    def _set_device_scope_hardware_averaging(self, value: bool, channel_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
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

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        try:
            AWGDigitalAnalogConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ValueError:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id)
