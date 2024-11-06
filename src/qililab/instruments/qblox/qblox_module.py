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
from typing import ClassVar, Sequence

from qpysequence import Sequence as QpySequence

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.qblox.qblox_sequencer import QbloxSequencer
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.typings import ChannelID, Parameter, ParameterValue
from qililab.typings.instruments import QcmQrm


class QbloxModule(Instrument):
    """Qblox Module class.

    Args:
        device (QcmQrm): Instance of the Qblox QcmQrm class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    _MAX_BINS: int = 131072
    _NUM_MAX_SEQUENCERS: int = 6
    _NUM_MAX_AWG_OUT_CHANNELS: int = 4
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxModuleSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific module.

        Args:
            awg_sequencers (Sequence[QbloxSequencer]): list of settings for each sequencer
            out_offsets (list[float]): list of offsets for each output of the qblox module
        """

        awg_sequencers: Sequence[QbloxSequencer]
        out_offsets: list[float]

        def __post_init__(self):
            """build QbloxSequencer"""
            if len(self.awg_sequencers) > QbloxModule._NUM_MAX_SEQUENCERS:
                raise ValueError(
                    f"The number of sequencers must be less or equal than {QbloxModule._NUM_MAX_SEQUENCERS}. Received: {len(self.awg_sequencers)}"
                )

            self.awg_sequencers = [
                (QbloxSequencer(**sequencer) if isinstance(sequencer, dict) else sequencer)
                for sequencer in self.awg_sequencers
            ]
            super().__post_init__()

    settings: QbloxModuleSettings
    device: QcmQrm
    # Cache containing the last compiled pulse schedule for each sequencer
    cache: ClassVar[dict[int, PulseBusSchedule]] = {}

    def __init__(self, settings: dict):
        # The sequences dictionary contains all the compiled sequences for each sequencer. Sequences are saved and handled at the compiler
        self.sequences: dict[int, QpySequence] = {}  # {sequencer_idx: (program), ...}
        self.num_bins: int = 1
        super().__init__(settings=settings)

    @property
    def num_sequencers(self):
        """Number of sequencers in the AWG

        Returns:
            int: number of sequencers
        """
        return len(self.settings.awg_sequencers)

    @property
    def awg_sequencers(self):
        """AWG 'awg_sequencers' property."""
        return self.settings.awg_sequencers

    def get_sequencer(self, sequencer_id: int) -> QbloxSequencer:
        """Get sequencer from the sequencer identifier

        Args:
            sequencer_id (int): sequencer identifier

        Returns:
            AWGSequencer: sequencer associated with the sequencer_id
        """
        for sequencer in self.awg_sequencers:
            if sequencer.identifier == sequencer_id:
                return sequencer
        raise IndexError(f"There is no sequencer with id={sequencer_id}.")

    @check_device_initialized
    def initial_setup(self):
        """Initial setup"""
        self._map_connections()
        self.clear_cache()
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            # Set `sync_en` flag to False (this value will be set to True if the sequencer is used in the execution)
            self.device.sequencers[sequencer_id].sync_en(False)
            self.device.sequencers[sequencer_id].marker_ovr_en(False)
            self._set_nco(sequencer_id=sequencer_id)
            self._set_gain_i(value=sequencer.gain_i, sequencer_id=sequencer_id)
            self._set_gain_q(value=sequencer.gain_q, sequencer_id=sequencer_id)
            self._set_offset_i(value=sequencer.offset_i, sequencer_id=sequencer_id)
            self._set_offset_q(value=sequencer.offset_q, sequencer_id=sequencer_id)
            self._set_hardware_modulation(value=sequencer.hardware_modulation, sequencer_id=sequencer_id)
            self._set_gain_imbalance(value=sequencer.gain_imbalance, sequencer_id=sequencer_id)
            self._set_phase_imbalance(value=sequencer.phase_imbalance, sequencer_id=sequencer_id)

        for idx, offset in enumerate(self.out_offsets):
            self._set_out_offset(output=idx, value=offset)

    def sync_sequencer(self, sequencer_id: int) -> None:
        """Syncs all sequencers."""
        sequencer = self.get_sequencer(sequencer_id=sequencer_id)
        self.device.sequencers[sequencer.identifier].sync_en(True)

    def desync_sequencer(self, sequencer_id: int) -> None:
        """Syncs all sequencers."""
        sequencer = self.get_sequencer(sequencer_id=sequencer_id)
        self.device.sequencers[sequencer.identifier].sync_en(False)

    def desync_sequencers(self) -> None:
        """Desyncs all sequencers."""
        for sequencer in self.awg_sequencers:
            self.device.sequencers[sequencer.identifier].sync_en(False)

    def set_markers_override_enabled(self, value: bool, sequencer_id: int):
        """Set markers override flag ON/OFF for the sequencers associated with port."""
        sequencer = self.get_sequencer(sequencer_id=sequencer_id)
        self.device.sequencers[sequencer.identifier].marker_ovr_en(value)

    def set_markers_override_value(self, value: int, sequencer_id: int):
        """Set markers override value for all sequencers."""
        sequencer = self.get_sequencer(sequencer_id=sequencer_id)
        self.device.sequencers[sequencer.identifier].marker_ovr_value(value)

    def module_type(self):
        """returns the qblox module type. Options: QCM or QRM"""
        return self.device.module_type()

    def run(self, channel_id: ChannelID):
        """Run the uploaded program"""
        sequencer = next((sequencer for sequencer in self.awg_sequencers if sequencer.identifier == channel_id), None)
        if sequencer is not None and sequencer.identifier in self.sequences:
            self.device.arm_sequencer(sequencer=sequencer.identifier)
            self.device.start_sequencer(sequencer=sequencer.identifier)

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None) -> None:
        """Set Qblox instrument calibration settings."""
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            self._set_out_offset(output=output, value=value)
            return

        if channel_id is None:
            raise Exception(f"Cannot update parameter {parameter.value} without specifying a channel_id.")

        channel_id = int(channel_id)
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
        if parameter == Parameter.GAIN_IMBALANCE:
            self._set_gain_imbalance(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.PHASE_IMBALANCE:
            self._set_phase_imbalance(value=value, sequencer_id=channel_id)
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            return self.out_offsets[output]

        if channel_id is None:
            raise Exception(f"Cannot update parameter {parameter.value} without specifying a channel_id.")

        channel_id = int(channel_id)
        sequencer = self.get_sequencer(sequencer_id=channel_id)

        if parameter == Parameter.GAIN:
            return sequencer.gain_i, sequencer.gain_q

        if hasattr(sequencer, parameter.value):
            return getattr(sequencer, parameter.value)

        raise ParameterNotFound(self, parameter)

    def _set_hardware_modulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware modulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.get_sequencer(sequencer_id=sequencer_id).hardware_modulation = bool(value)

        if self.is_device_active():
            self.device.sequencers[sequencer_id].mod_en_awg(bool(value))

    def _set_frequency(self, value: float | str | bool, sequencer_id: int):
        """set frequency

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.get_sequencer(sequencer_id=sequencer_id).intermediate_frequency = float(value)

        if self.is_device_active():
            self.device.sequencers[sequencer_id].nco_freq(float(value))

    def _set_offset_i(self, value: float | str | bool, sequencer_id: int):
        """Set the offset of the I channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self.get_sequencer(sequencer_id=sequencer_id).offset_i = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "offset_awg_path0")(float(value))

    def _set_offset_q(self, value: float | str | bool, sequencer_id: int):
        """Set the offset of the Q channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self.get_sequencer(sequencer_id=sequencer_id).offset_q = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "offset_awg_path1")(float(value))

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

    def _set_gain_i(self, value: float | str | bool, sequencer_id: int):
        """Set the gain of the I channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self.get_sequencer(sequencer_id=sequencer_id).gain_i = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "gain_awg_path0")(float(value))

    def _set_gain_q(self, value: float | str | bool, sequencer_id: int):
        """Set the gain of the Q channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self.get_sequencer(sequencer_id=sequencer_id).gain_q = float(value)
        # update value in the instrument
        if self.is_device_active():
            sequencer = self.device.sequencers[sequencer_id]
            getattr(sequencer, "gain_awg_path1")(float(value))

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

    @check_device_initialized
    def turn_off(self):
        """Stop the QBlox sequencer from sending pulses."""
        for seq_idx in range(self.num_sequencers):
            self.device.stop_sequencer(sequencer=seq_idx)

    @check_device_initialized
    def turn_on(self):
        """Turn on an instrument."""

    def clear_cache(self):
        """Empty cache."""
        self.cache = {}
        self.sequences = {}

    @check_device_initialized
    def reset(self):
        """Reset instrument."""
        self.clear_cache()
        self.device.reset()

    def upload_qpysequence(self, qpysequence: QpySequence, channel_id: ChannelID):
        """Upload the qpysequence to its corresponding sequencer.

        Args:
            qpysequence (QpySequence): The qpysequence to upload.
            port (str): The port of the sequencer to upload to.
        """
        sequencer = next((sequencer for sequencer in self.awg_sequencers if sequencer.identifier == channel_id), None)
        if sequencer is not None:
            logger.info("Sequence program: \n %s", repr(qpysequence._program))
            self.device.sequencers[sequencer.identifier].sequence(qpysequence.todict())
            self.sequences[sequencer.identifier] = qpysequence

    def upload(self, channel_id: ChannelID):
        """Upload all the previously compiled programs to its corresponding sequencers.

        This method must be called after the method ``compile`` in the compiler
        Args:
            port (str): The port of the sequencer to upload to.
        """
        sequencer = next((sequencer for sequencer in self.awg_sequencers if sequencer.identifier == channel_id), None)
        if sequencer is not None and sequencer.identifier in self.sequences:
            sequence = self.sequences[sequencer.identifier]
            logger.info("Uploaded sequence program: \n %s", repr(sequence._program))  # pylint: disable=protected-access
            self.device.sequencers[sequencer.identifier].sequence(sequence.todict())
            self.device.sequencers[sequencer.identifier].sync_en(True)

    def _set_nco(self, sequencer_id: int):
        """Enable modulation of pulses and setup NCO frequency."""
        if self.get_sequencer(sequencer_id=sequencer_id).hardware_modulation:
            self._set_hardware_modulation(
                value=self.get_sequencer(sequencer_id=sequencer_id).hardware_modulation, sequencer_id=sequencer_id
            )
            self._set_frequency(
                value=self.get_sequencer(sequencer_id=sequencer_id).intermediate_frequency, sequencer_id=sequencer_id
            )

    def _set_gain_imbalance(self, value: float | str | bool, sequencer_id: int):
        """Set I and Q gain imbalance of sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """

        self.get_sequencer(sequencer_id=sequencer_id).gain_imbalance = float(value)

        if self.is_device_active():
            self.device.sequencers[sequencer_id].mixer_corr_gain_ratio(float(value))

    def _set_phase_imbalance(self, value: float | str | bool, sequencer_id: int):
        """Set I and Q phase imbalance of sequencer.

         Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.get_sequencer(sequencer_id=sequencer_id).phase_imbalance = float(value)
        if self.is_device_active():
            self.device.sequencers[sequencer_id].mixer_corr_phase_offset_degree(float(value))

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
