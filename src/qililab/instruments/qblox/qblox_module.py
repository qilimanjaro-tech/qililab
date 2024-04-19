# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Qblox module class"""
from dataclasses import dataclass
from typing import Sequence, cast

from qpysequence import Sequence as QpySequence

from qililab.config import logger
from qililab.instruments.awg import AWG
from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.typings.enums import Parameter
from qililab.typings.instruments import Pulsar, QcmQrm


class QbloxModule(AWG):
    """Qblox Module class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    _MAX_BINS: int = 131072
    _NUM_MAX_SEQUENCERS: int = 6
    _NUM_MAX_AWG_OUT_CHANNELS: int = 4
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxModuleSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            awg_sequencers (Sequence[AWGQbloxSequencer]): list of settings for each sequencer
            out_offsets (list[float]): list of offsets for each output of the qblox module
        """

        awg_sequencers: Sequence[AWGQbloxSequencer]
        out_offsets: list[float]

        def __post_init__(self):
            """build AWGQbloxSequencer"""
            if (
                self.num_sequencers <= 0
                or self.num_sequencers > QbloxModule._NUM_MAX_SEQUENCERS  # pylint: disable=protected-access
            ):
                raise ValueError(
                    "The number of sequencers must be greater than 0 and less or equal than "
                    + f"{QbloxModule._NUM_MAX_SEQUENCERS}. Received: {self.num_sequencers}"  # pylint: disable=protected-access
                )
            if len(self.awg_sequencers) != self.num_sequencers:
                raise ValueError(
                    f"The number of sequencers: {self.num_sequencers} does not match"
                    + f" the number of AWG Sequencers settings specified: {len(self.awg_sequencers)}"
                )

            self.awg_sequencers = [
                AWGQbloxSequencer(**sequencer)
                if isinstance(sequencer, dict)
                else sequencer  # pylint: disable=not-a-mapping
                for sequencer in self.awg_sequencers
            ]
            super().__post_init__()

    settings: QbloxModuleSettings
    device: Pulsar | QcmQrm
    # Cache containing the last compiled pulse schedule for each sequencer
    cache: dict[int, PulseBusSchedule] = {}

    def __init__(self, settings: dict):
        # The sequences dictionary contains all the compiled sequences for each sequencer. Sequences are saved and handled at the compiler
        self.sequences: dict[int, QpySequence] = {}  # {sequencer_idx: (program), ...}
        self.num_bins: int = 1
        super().__init__(settings=settings)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        self._map_connections()
        self.clear_cache()
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            # Set `sync_en` flag to False (this value will be set to True if the sequencer is used in the execution)
            self.device.sequencers[sequencer_id].sync_en(False)
            self._set_nco(sequencer_id=sequencer_id)
            self._set_gain_i(value=sequencer.gain_i, sequencer_id=sequencer_id)
            self._set_gain_q(value=sequencer.gain_q, sequencer_id=sequencer_id)
            self._set_offset_i(value=sequencer.offset_i, sequencer_id=sequencer_id)
            self._set_offset_q(value=sequencer.offset_q, sequencer_id=sequencer_id)
            self._set_hardware_modulation(value=sequencer.hardware_modulation, sequencer_id=sequencer_id)
            self._set_gain_imbalance(value=sequencer.gain_imbalance, sequencer_id=sequencer_id)
            self._set_phase_imbalance(value=sequencer.phase_imbalance, sequencer_id=sequencer_id)
            ALL_ON = 15  # 1111 in binary
            self._set_markers(value=ALL_ON, sequencer_id=sequencer_id)

        for idx, offset in enumerate(self.out_offsets):
            self._set_out_offset(output=idx, value=offset)

    def sync_by_port(self, port: str) -> None:
        """Syncs all sequencers."""
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            self.device.sequencers[sequencer.identifier].sync_en(True)

    def desync_by_port(self, port: str) -> None:
        """Syncs all sequencers."""
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            self.device.sequencers[sequencer.identifier].sync_en(False)

    def desync_sequencers(self) -> None:
        """Desyncs all sequencers."""
        for sequencer in self.awg_sequencers:
            self.device.sequencers[sequencer.identifier].sync_en(False)

    @property
    def module_type(self):
        """returns the qblox module type. Options: QCM or QRM"""
        return self.device.module_type()

    def run(self, port: str):
        """Run the uploaded program"""
        self.start_sequencer(port=port)

    def start_sequencer(self, port: str):
        """Start sequencer and execute the uploaded instructions."""
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            if sequencer.identifier in self.sequences:
                self.device.arm_sequencer(sequencer=sequencer.identifier)
                self.device.start_sequencer(sequencer=sequencer.identifier)

    def setup(  # pylint: disable=too-many-branches, too-many-return-statements
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None
    ):
        """Set Qblox instrument calibration settings."""
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            self._set_out_offset(output=output, value=value)
            return

        if channel_id is None:
            if self.num_sequencers == 1:
                channel_id = 0
            else:
                raise ParameterNotFound(f"Cannot update parameter {parameter.value} without specifying a channel_id.")

        if channel_id > self.num_sequencers - 1:
            raise ParameterNotFound(
                f"the specified channel id:{channel_id} is out of range. Number of sequencers is {self.num_sequencers}"
            )
        if parameter == Parameter.GAIN:
            self._set_gain(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_I:
            self._set_gain_i(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_Q:
            self._set_gain_q(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.OFFSET_I:
            self._set_offset_i(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.OFFSET_Q:
            self._set_offset_q(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.IF:
            self._set_frequency(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.HARDWARE_MODULATION:
            self._set_hardware_modulation(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.NUM_BINS:
            self._set_num_bins(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_IMBALANCE:
            self._set_gain_imbalance(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.PHASE_IMBALANCE:
            self._set_phase_imbalance(value=value, sequencer_id=channel_id)
            return
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    def get(self, parameter: Parameter, channel_id: int | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            return self.out_offsets[output]

        if channel_id is None:
            if self.num_sequencers == 1:
                channel_id = 0
            else:
                raise ParameterNotFound(f"Cannot update parameter {parameter.value} without specifying a channel_id.")

        sequencer = self._get_sequencer_by_id(id=channel_id)

        if parameter == Parameter.GAIN:
            return sequencer.gain_i, sequencer.gain_q

        if hasattr(sequencer, parameter.value):
            return getattr(sequencer, parameter.value)

        raise ParameterNotFound(f"Cannot find parameter {parameter.value} in instrument {self.alias}")

    @Instrument.CheckParameterValueFloatOrInt
    def _set_num_bins(self, value: float | str | bool, sequencer_id: int):
        """set num_bins for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if int(value) > self._MAX_BINS:
            raise ValueError(f"Value {value} greater than maximum bins: {self._MAX_BINS}")
        cast(AWGQbloxSequencer, self._get_sequencer_by_id(id=sequencer_id)).num_bins = int(value)

    @Instrument.CheckParameterValueBool
    def _set_hardware_modulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware modulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self._get_sequencer_by_id(id=sequencer_id).hardware_modulation = bool(value)

        if self.is_device_active():
            self.device.sequencers[sequencer_id].mod_en_awg(bool(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_frequency(self, value: float | str | bool, sequencer_id: int):
        """set frequency

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self._get_sequencer_by_id(id=sequencer_id).intermediate_frequency = float(value)

        if self.is_device_active():
            self.device.sequencers[sequencer_id].nco_freq(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_i(self, value: float | str | bool, sequencer_id: int):
        """Set the offset of the I channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).offset_i = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "offset_awg_path0")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_q(self, value: float | str | bool, sequencer_id: int):
        """Set the offset of the Q channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).offset_q = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "offset_awg_path1")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_out_offset(self, output: int, value: float | str | bool):
        """Set output offsets of the Qblox device.

        Args:
            output (int): output to update
            value (float | str | bool): value to update

        Raises:
            ValueError: when value type is not float or int
        """
        if output > len(self.out_offsets):
            raise IndexError(
                f"Output {output} is out of range. The runcard has only {len(self.out_offsets)} output offsets defined."
                " Please update the list of output offsets of the runcard such that it contains a value for each "
                "output of the device."
            )
        self.out_offsets[output] = value

        if self.is_device_active():
            getattr(self.device, f"out{output}_offset")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_i(self, value: float | str | bool, sequencer_id: int):
        """Set the gain of the I channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).gain_i = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "gain_awg_path0")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_q(self, value: float | str | bool, sequencer_id: int):
        """Set the gain of the Q channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).gain_q = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "gain_awg_path1")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain(self, value: float | str | bool, sequencer_id: int):
        """set gain

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self._set_gain_i(value=value, sequencer_id=sequencer_id)
        self._set_gain_q(value=value, sequencer_id=sequencer_id)

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop the QBlox sequencer from sending pulses."""
        for seq_idx in range(self.num_sequencers):
            self.device.stop_sequencer(sequencer=seq_idx)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turn on an instrument."""

    def clear_cache(self):
        """Empty cache."""
        self.cache = {}
        self.sequences = {}

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.clear_cache()
        self.device.reset()

    def upload_qpysequence(self, qpysequence: QpySequence, port: str):
        """Upload the qpysequence to its corresponding sequencer.

        Args:
            qpysequence (QpySequence): The qpysequence to upload.
            port (str): The port of the sequencer to upload to.
        """
        # FIXME: does not support readout on multiple qubits on the same bus
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            logger.info("Sequence program: \n %s", repr(qpysequence._program))  # pylint: disable=protected-access
            self.device.sequencers[sequencer.identifier].sequence(qpysequence.todict())
            self.sequences[sequencer.identifier] = qpysequence

    def upload(self, port: str):  # TODO: check compatibility with QProgram
        """Upload all the previously compiled programs to its corresponding sequencers.

        This method must be called after the method ``compile`` in the compiler
        Args:
            port (str): The port of the sequencer to upload to.
        """
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            seq_idx = sequencer.identifier
            # check is sequence has already been uploaded in a previous execution
            if seq_idx in self.sequences:
                # if the sequence was in the cache then it is to be run so we sync the sequencer to the others
                sequence = self.sequences[seq_idx]
                logger.info(
                    "Uploaded sequence program: \n %s", repr(sequence._program)  # pylint: disable=protected-access
                )
                self.device.sequencers[seq_idx].sequence(sequence.todict())
                self.device.sequencers[sequencer.identifier].sync_en(True)

    def _set_nco(self, sequencer_id: int):
        """Enable modulation of pulses and setup NCO frequency."""
        if self._get_sequencer_by_id(id=sequencer_id).hardware_modulation:
            self._set_hardware_modulation(
                value=self._get_sequencer_by_id(id=sequencer_id).hardware_modulation, sequencer_id=sequencer_id
            )
            self._set_frequency(
                value=self._get_sequencer_by_id(id=sequencer_id).intermediate_frequency, sequencer_id=sequencer_id
            )

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_imbalance(self, value: float | str | bool, sequencer_id: int):
        """Set I and Q gain imbalance of sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """

        self._get_sequencer_by_id(id=sequencer_id).gain_imbalance = float(value)

        if self.is_device_active():
            self.device.sequencers[sequencer_id].mixer_corr_gain_ratio(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_phase_imbalance(self, value: float | str | bool, sequencer_id: int):
        """Set I and Q phase imbalance of sequencer.

         Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self._get_sequencer_by_id(id=sequencer_id).phase_imbalance = float(value)
        if self.is_device_active():
            self.device.sequencers[sequencer_id].mixer_corr_phase_offset_degree(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_markers(self, value: int, sequencer_id: int):
        """Set markers ON/OFF on qblox modules.

        For the RF modules, this command is also used to enable/disable:
            - The 2 outputs (for the QCM-RF).
            - The input and the output (for QRM-RF).

         Args:
            value (int): ON/OFF of the 4 markers in binary (range: 0-15 -> (0000)-(1111)). For the RF modules, the
                first 2 bits correspond to the ON/OFF value of the outputs/inputs and the last 2 bits correspond
                to the 2 markers.
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not int
        """
        self.device.sequencers[sequencer_id].marker_ovr_en(True)
        self.device.sequencers[sequencer_id].marker_ovr_value(value)

    def _map_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        # Disable all connections
        self.device.disconnect_outputs()

        for sequencer_dataclass in self.awg_sequencers:
            sequencer = self.device.sequencers[sequencer_dataclass.identifier]
            for path, output in zip(["I", "Q"], sequencer_dataclass.outputs):
                getattr(sequencer, f"connect_out{output}")(path)

    @property
    def out_offsets(self):
        """Returns the offsets of each output of the qblox module."""
        return self.settings.out_offsets

    def _get_sequencer_by_id(self, id: int):  # pylint: disable=redefined-builtin
        """Returns a sequencer with the given `id`."

        Args:
            id (int): Id of the sequencer.

        Raises:
            IndexError: There is no sequencer with the given `id`.

        Returns:
            AWGQbloxSequencer: Sequencer with the given `id`.
        """
        for sequencer in self.awg_sequencers:
            if sequencer.identifier == id:
                return sequencer
        raise IndexError(f"There is no sequencer with id={id}.")
