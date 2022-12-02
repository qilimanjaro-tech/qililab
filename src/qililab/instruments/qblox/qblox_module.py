"""Qblox module class"""
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import numpy.typing as npt
from qpysequence.acquisitions import Acquisitions
from qpysequence.library import long_wait, set_awg_gain_relative, set_phase_rad
from qpysequence.program import Block, Loop, Program
from qpysequence.program.instructions import Play, Stop, Wait
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments.awg import AWG
from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule, PulseShape
from qililab.typings.enums import Parameter
from qililab.typings.instruments import Pulsar, QcmQrm


class QbloxModule(AWG):
    """Qblox Module class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    _MAX_BINS: int = 131072
    _NUM_SEQUENCERS: int = 4
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxModuleSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            sync_enabled (List[bool]): Enable synchronization over multiple instruments for each sequencer.
            num_bins (int): Number of bins
        """

        sync_enabled: List[bool]
        num_bins: List[int]

    settings: QbloxModuleSettings
    device: Pulsar | QcmQrm
    # Cache containing the last PulseSequence, nshots and repetition_duration used.
    _cache: Tuple[PulseBusSchedule, int, int] | None = None

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        self._map_outputs()
        for channel_id in range(self.num_sequencers):
            self._set_sync_enabled_one_channel(value=self.settings.sync_enabled[channel_id], channel_id=channel_id)
            self._set_nco(channel_id=channel_id)

    @property
    def module_type(self):
        """returns the qblox module type. Options: QCM or QRM"""
        return self.device.module_type()

    def run(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path):
        """Run execution of a pulse sequence.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse sequence.
        """
        self._check_cached_values(
            pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, path=path
        )
        self.start_sequencer()

    def _check_cached_values(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        path: Path,
        modI: npt.NDArray[np.float32] | None = None,
        modQ: npt.NDArray[np.float32] | None = None,
        waveforms: dict | None = None,
    ):
        """check if values are already cached and upload if not cached"""
        if (pulse_bus_schedule, nshots, repetition_duration) != self._cache:
            self._cache = (pulse_bus_schedule, nshots, repetition_duration)
            sequence = self._translate_pulse_bus_schedule(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                modI=modI,
                modQ=modQ,
            )
            self.upload(sequence=sequence, path=path, waveforms=waveforms)

    def _translate_pulse_bus_schedule(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        modI: npt.NDArray[np.float32] | None = None,
        modQ: npt.NDArray[np.float32] | None = None,
    ):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule, modI=modI, modQ=modQ)
        acquisitions = self._generate_acquisitions()
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule,
            waveforms=waveforms,
            nshots=nshots,
            repetition_duration=repetition_duration,
        )
        weights = self._generate_weights()
        return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)

    def _generate_program(
        self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms, nshots: int, repetition_duration: int
    ):
        """Generate Q1ASM program

        #     Args:
        #         pulse_sequence (PulseSequence): Pulse sequence.
        #         waveforms (Waveforms): Waveforms.

            Returns:
                Program: Q1ASM program.
        """
        # Define program's blocks
        program = Program()
        # bin_loop = Loop(
        #     name="binning", begin=0, end=int(self.num_bins[0])
        # )  # FIXME: get the channel instead of using the first
        avg_loop = Loop(name="average", begin=0, end=nshots)
        # bin_loop.append_block(block=avg_loop, bot_position=1)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=avg_loop)
        program.append_block(block=stop)
        timeline = pulse_bus_schedule.timeline
        if timeline[0].start != 0:  # TODO: Make sure that start time of Pulse is 0 or bigger than 4
            avg_loop.append_component(Wait(wait_time=int(timeline[0].start)))

        for i, pulse_event in enumerate(timeline):
            waveform_pair = waveforms.find_pair_by_name(pulse_event.pulse.label())
            wait_time = timeline[i + 1].start - pulse_event.start if (i < (len(timeline) - 1)) else self.final_wait_time
            avg_loop.append_component(set_phase_rad(rads=pulse_event.pulse.phase))
            # avg_loop.append_component(
            #     set_awg_gain_relative(gain_0=pulse_event.pulse.amplitude, gain_1=pulse_event.pulse.amplitude)
            # )
            avg_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=int(wait_time),
                )
            )
        self._append_acquire_instruction(loop=avg_loop, register=avg_loop.counter_register)
        avg_loop.append_block(long_wait(wait_time=repetition_duration - avg_loop.duration_iter), bot_position=1)
        return program

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "single", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        acquisitions = Acquisitions()
        acquisitions.add(name="single", num_bins=1, index=0)
        # acquisitions.add(name="binning", num_bins=int(self.num_bins[0]) + 1, index=1)  # binned acquisition
        return acquisitions

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

    def _append_acquire_instruction(self, loop: Loop, register: str):
        """Append an acquire instruction to the loop."""

    def start_sequencer(self):
        """Start sequencer and execute the uploaded instructions."""
        for seq_idx in range(self.num_sequencers):
            self.device.arm_sequencer(sequencer=seq_idx)
            self.device.start_sequencer(sequencer=seq_idx)

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        if channel_id > self.num_sequencers - 1:
            raise ValueError(
                f"the specified channel_id:{channel_id} is out of range. Number of sequencers is {self.num_sequencers}"
            )

        if parameter.value == Parameter.GAIN.value:
            self._set_gain(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.OFFSET_I.value:
            self._set_offset_i(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.OFFSET_Q.value:
            self._set_offset_q(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.FREQUENCIES.value:
            self._set_frequency(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.HARDWARE_MODULATION.value:
            self._set_hardware_modulation(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.SYNC_ENABLED.value:
            self._set_sync_enabled_one_channel(value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.NUM_BINS.value:
            self._set_num_bins(value=value, channel_id=channel_id)
            return

    def _set_num_bins(self, value: float | str | bool, channel_id: int):
        """set sync enabled for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if not isinstance(value, float) or not isinstance(value, int):
            raise ValueError(f"value must be a int or float. Current type: {type(value)}")
        if value > self._MAX_BINS:
            raise ValueError(f"Value {value} greater than maximum bins: {self._MAX_BINS}")
        self.settings.num_bins[channel_id] = int(value)

    def _set_sync_enabled_one_channel(self, value: float | str | bool, channel_id: int):
        """set sync enabled for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if not isinstance(value, bool):
            raise ValueError(f"value must be a bool. Current type: {type(value)}")
        self.settings.sync_enabled[channel_id] = value
        self.device.sequencers[channel_id].sync_en(value)

    def _set_hardware_modulation(self, value: float | str | bool, channel_id: int):
        """set hardware modulation

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if not isinstance(value, bool):
            raise ValueError(f"value must be a bool. Current type: {type(value)}")
        self.settings.hardware_modulation[channel_id] = value
        self.device.sequencers[channel_id].mod_en_awg(value)

    def _set_frequency(self, value: float | str | bool, channel_id: int):
        """set frequency

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        if not isinstance(value, float):
            raise ValueError(f"value must be a float. Current type: {type(value)}")
        self.settings.frequencies[channel_id] = value
        self.device.sequencers[channel_id].nco_freq(value)

    def _set_offset_q(self, value: float | str | bool, channel_id: int):
        """set offset Q

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        if not isinstance(value, float):
            raise ValueError(f"value must be a float. Current type: {type(value)}")
        self.settings.offset_q[channel_id] = value
        self.device.sequencers[channel_id].offset_awg_path1(value)

    def _set_offset_i(self, value: float | str | bool, channel_id: int):
        """set offset I

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        if not isinstance(value, float):
            raise ValueError(f"value must be a float. Current type: {type(value)}")
        self.settings.offset_i[channel_id] = value
        self.device.sequencers[channel_id].offset_awg_path0(value)

    def _set_gain(self, value: float | str | bool, channel_id: int):
        """set gain

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        if not isinstance(value, float):
            raise ValueError(f"value must be a float. Current type: {type(value)}")
        self.settings.gain[channel_id] = value
        self.device.sequencers[channel_id].gain_awg_path0(value)
        self.device.sequencers[channel_id].gain_awg_path1(value)

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        for seq_idx in range(self.num_sequencers):
            self.device.stop_sequencer(sequencer=seq_idx)

    def clear_cache(self):
        """Empty cache."""
        self._cache = None

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.clear_cache()
        self.device.reset()

    def upload(self, sequence: Sequence, path: Path, waveforms: dict | None = None):
        """Upload sequence to sequencer.

        Args:
            sequence (Sequence): Sequence object containing the waveforms, weights,
            acquisitions and program of the sequence.
        """

        obj = {
            "waveforms": sequence._waveforms.to_dict() if waveforms is None else waveforms,
            "weights": sequence._weights,
            "acquisitions": sequence._acquisitions.to_dict(),
            "program": repr(sequence._program),
        }

        # print(obj["program"])
        # print(obj["acquisitions"])
        # print(obj["waveforms"])

        file_path = str(path / f"{self.name.value}_sequence.yml")
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            json.dump(obj=obj, fp=file)

        for seq_idx in range(self.num_sequencers):
            self.device.sequencers[seq_idx].sequence(file_path)

    def _set_nco(self, channel_id: int):
        """Enable modulation of pulses and setup NCO frequency."""
        if self.settings.hardware_modulation[channel_id]:
            self._set_hardware_modulation(value=self.settings.hardware_modulation[channel_id], channel_id=channel_id)
            self._set_frequency(value=self.settings.frequencies[channel_id], channel_id=channel_id)

    def _map_outputs(self):
        """Disable all connections and map sequencer paths with output channels."""
        # Disable all connections
        for sequencer, out in itertools.product(self.device.sequencers, range(self._NUM_SEQUENCERS)):
            if hasattr(sequencer, f"channel_map_path{out % 2}_out{out}_en"):
                sequencer.set(f"channel_map_path{out % 2}_out{out}_en", False)
        for seq_idx in range(self.num_sequencers):
            self.device.sequencers[seq_idx].channel_map_path0_out0_en(True)
            self.device.sequencers[seq_idx].channel_map_path1_out1_en(True)

    def _generate_waveforms(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        modI: npt.NDArray[np.float32] | None = None,
        modQ: npt.NDArray[np.float32] | None = None,
    ):
        """Generate I and Q waveforms from a PulseSequence object.
        Args:
            pulse_bus_schedule (PulseBusSchedule): PulseSequence object.
        Returns:
            Waveforms: Waveforms object containing the generated waveforms.
        """
        waveforms = Waveforms()

        unique_pulses: List[Tuple[int, PulseShape]] = []

        for pulse_event in pulse_bus_schedule.timeline:
            if (pulse_event.duration, pulse_event.pulse.pulse_shape) not in unique_pulses:
                unique_pulses.append((pulse_event.duration, pulse_event.pulse.pulse_shape))
                if modI is None and modQ is None:
                    envelope = pulse_event.pulse.envelope(amplitude=1)
                    real = np.real(envelope)
                    imag = np.imag(envelope)
                if modI is not None and modQ is not None:
                    real = modI
                    imag = modQ
                waveforms.add_pair((real, imag), name=pulse_event.pulse.label())

        return waveforms

    @property
    def sync_enabled(self):
        """QbloxPulsar 'sync_enabled' property.

        Returns:
            bool: settings.sync_enabled.
        """
        return self.settings.sync_enabled

    @property
    def final_wait_time(self) -> int:
        """QbloxPulsar 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self._MIN_WAIT_TIME

    @property
    def num_bins(self):
        """QbloxPulsar 'num_bins' property.

        Returns:
            int: Number of bins used.
        """
        return self.settings.num_bins
