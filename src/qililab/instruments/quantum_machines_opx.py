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
from __future__ import annotations

from typing import TYPE_CHECKING

from qm import DictQuaConfig, QmJob, QuantumMachine, SimulationConfig

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import QuantumMachinesOPXRuncardInstrument, RuncardInstrument
from qililab.settings.instruments.quantum_machines_opx_settings import (
    ControllerPort,
    IQElement,
    IQReadoutElement,
    OctavePort,
    OpxLFOutput,
    OpxRFInput,
    OpxRFOutput,
    OPXSettings,
    RFElement,
    RFReadoutElement,
    SingleElement,
)
from qililab.typings import QuantumMachinesDevice
from qililab.utils import hash_qua_program, merge_dictionaries

if TYPE_CHECKING:
    import numpy as np
    from qm.api.v2.job_api import JobApi
    from qm.jobs.running_qm_job import RunningQmJob
    from qm.program import Program


@InstrumentFactory.register(InstrumentType.QUANTUM_MACHINES_OPX)
class QuantumMachinesOPX(
    InstrumentWithChannels[
        QuantumMachinesDevice,
        OPXSettings,
        SingleElement | IQElement | IQReadoutElement | RFElement | RFReadoutElement,
        str
    ]
):
    _qm: QuantumMachine
    _qua_config: DictQuaConfig
    _compiled_program_cache: dict[str, str]
    _pending_set_intermediate_frequency: dict[str, float]

    def __init__(self, settings: OPXSettings | None = None):
        super().__init__(settings=settings)

        self.add_parameter(
            name="timeout",
            settings_field="timeout"
        )

        for channel in self.settings.channels:
            if isinstance(channel, RFElement):
                self.add_channel_parameter(
                    channel_id=channel.id,
                    name="intermediate_frequency",
                    settings_field="intermediate_frequency"
                )
            if isinstance(channel, RFReadoutElement):
                self.add_channel_parameter(
                    channel_id=channel.id,
                    name="time_of_flight",
                    settings_field="time_of_flight"
                )
                self.add_channel_parameter(
                    channel_id=channel.id,
                    name="smearing",
                    settings_field="smearing"
                )

    @classmethod
    def get_default_settings(cls) -> OPXSettings:
        return OPXSettings(
            alias="opx",
            outputs=[
                OpxLFOutput(port=0, connected_to=ControllerPort(controller="con1", port=1)),
                OpxLFOutput(port=1, connected_to=ControllerPort(controller="con1", port=2)),
                OpxLFOutput(port=2, connected_to=ControllerPort(controller="con1", port=3)),
                OpxLFOutput(port=3, connected_to=ControllerPort(controller="con1", port=4)),
                OpxRFOutput(
                    port=4,
                    connected_to=OctavePort(octave="octave1", port=1),
                    connection_i=ControllerPort(controller="con1", port=5),
                    connection_q=ControllerPort(controller="con1", port=6),
                ),
                OpxRFOutput(
                    port=5,
                    connected_to=OctavePort(octave="octave1", port=2),
                    connection_i=ControllerPort(controller="con1", port=7),
                    connection_q=ControllerPort(controller="con1", port=8),
                ),
                OpxRFOutput(
                    port=6,
                    connected_to=OctavePort(octave="octave1", port=3),
                    connection_i=ControllerPort(controller="con1", port=9),
                    connection_q=ControllerPort(controller="con1", port=10),
                ),
            ],
            inputs=[
                OpxRFInput(
                    port=1,
                    connected_to=OctavePort(octave="octave1", port=1),
                    connection_i=ControllerPort(controller="con1", port=1),
                    connection_q=ControllerPort(controller="con1", port=2),
                )
            ],
            channels=[
                SingleElement(id="single_0", output=0),
                SingleElement(id="single_1", output=1),
                IQElement(id="iq_0", output_i=2, output_q=3, intermediate_frequency=100e6, lo_frequency=10e9),
                RFElement(id="drive_q0", output=4, intermediate_frequency=100e6),
                RFElement(id="drive_q1", output=5, intermediate_frequency=100e6),
                RFReadoutElement(id="readout_q0", output=6, input=1, intermediate_frequency=100e6),
                RFReadoutElement(id="readout_q1", output=6, input=1, intermediate_frequency=100e6),
            ],
        )

    def to_runcard(self) -> RuncardInstrument:
        return QuantumMachinesOPXRuncardInstrument(settings=self.settings)

    def _set_output_lo_frequency(self, value: float, channel: str):
        self._qm.octave.set_lo_frequency(element=channel, lo_frequency=value)
        self._qm.calibrate_element(channel)

    def _set_output_gain(self, value: float, channel: str):
        self._qm.octave.set_rf_output_gain(element=channel, gain_in_db=value)

    def _set_intermediate_frequency(self, value: float, channel: str):
        self._qm.set_intermediate_frequency(element=channel, freq=value)

    def _set_output_offset(self, value: float, channel: str):
        input: str | tuple[str, str] = "single" if isinstance(self.settings.get_channel(channel), SingleElement) else ("I", "Q")
        offset: float | tuple[float, float] = value if input == "single" else (value, value)
        self._qm.set_output_dc_offset_by_element(element=channel, input=input, offset=offset)

    def _set_output_offset_i(self, value: float, channel: str):
        self._qm.set_output_dc_offset_by_element(element=channel, input="I", offset=value)

    def _set_output_offset_q(self, value: float, channel: str):
        self._qm.set_output_dc_offset_by_element(element=channel, input="Q", offset=value)

    def _set_input_offset_i(self, value: float, channel: str):
        self._qm.set_input_dc_offset_by_element(element=channel, output="out1", offset=value)

    def _set_input_offset_q(self, value: float, channel: str):
        self._qm.set_input_dc_offset_by_element(element=channel, output="out2", offset=value)

    def is_qm_open(self) -> bool:
        """Check whether or not the device is currently active.

        Returns:
            bool: Whether or not the device has been initialized.
        """
        return hasattr(self, "_qm") and self._qm is not None

    def run_octave_calibration(self):
        """Run calibration procedure for the buses with octaves, if any."""
        elements = {
            element.id for element in self.settings.channels if isinstance(element, (RFElement, RFReadoutElement))
        }
        for element in elements:
            self._qm.calibrate_element(element)

    @check_device_initialized
    def turn_on(self):
        if not self.is_qm_open():
            self._qm = self.device.open_qm(config=self._config, close_other_machines=False)
            self._compiled_program_cache = {}
            self._pending_set_intermediate_frequency = {}

            if self.settings.run_octave_calibration:
                self.run_octave_calibration()

    @check_device_initialized
    def turn_off(self):
        if self.is_qm_open():
            self._qm.close()
            del self._qm
            del self._compiled_program_cache
            del self._pending_set_intermediate_frequency

    @check_device_initialized
    def reset(self):
        pass

    @check_device_initialized
    def initial_setup(self):
        self._qua_config = self.settings.to_qua_config()

    def append_configuration(self, configuration: dict):
        """Update the `_config` dictionary by appending the configuration generated by compilation.

        Args:
            configuration (dict): Configuration dictionary to append to the existing configuration.

        Raises:
            ValueError: Raised if the `_config` dictionary does not exist.
        """
        merged_configuration = merge_dictionaries(self.settings.to_qua_config(), configuration)
        if self._qua_config != merged_configuration:
            self._qua_config = DictQuaConfig(**merged_configuration)
            # If we are already connected, reopen the connection with the new configuration
            if self.is_qm_open():
                self._qm.close()
                self._qm = self.device.open_qm(config=self._qua_config, close_other_machines=False)  # type: ignore[assignment]
                self._compiled_program_cache = {}
                self._pending_set_intermediate_frequency = {}

    def compile(self, program: Program) -> str:
        """Compiles and stores a given QUA program on the Quantum Machines instance,
        and returns a unique identifier associated with the compiled program.

        The method first generates a hash for the input QUA program. If this hash is not already present in
        the cache, it proceeds to compile the program using QM's compile method and stores the result in the cache
        indexed by the generated hash. This caching mechanism prevents recompiling the same program multiple times,
        thus optimizing performance.

        Args:
            program (Program): The QUA program to be compiled.

        Returns:
            str: A unique identifier (hash) for the compiled QUA program. This identifier can be used to retrieve the compiled program from the cache, or run it  with `run_compiled_program` method.
        """
        qua_program_hash = hash_qua_program(program=program)
        if qua_program_hash not in self._compiled_program_cache:
            self._compiled_program_cache[qua_program_hash] = self._qm.compile(program=program)
        return self._compiled_program_cache[qua_program_hash]

    def run_compiled_program(self, compiled_program_id: str) -> QmJob | JobApi:
        """Executes a previously compiled QUA program identified by its unique compiled program ID.

        This method submits the compiled program to the Quantum Machines (QM) execution queue and waits for
        its execution to complete. The execution of the program is managed by the QM's queuing system,
        which schedules and runs the job on the quantum hardware or simulator as per availability and queue status.

        Args:
            compiled_program_id (str): The unique identifier of the compiled QUA program to be executed. This ID should correspond to a program that has already been compiled and is present in the program cache.

        Returns:
            RunningQmJob: An object representing the running job. This object provides methods and properties to check the status of the job, retrieve results upon completion, and manage or investigate the job's execution.
        """
        # TODO: qm.queue.add_compiled() -> qm.add_compiled()
        pending_job = self._qm.queue.add_compiled(compiled_program_id)

        # TODO: job.wait_for_execution() is deprecated and will be removed in the future. Please use job.wait_until("Running") instead.
        job = pending_job.wait_for_execution()  # type: ignore[return-value, union-attr]
        if self._pending_set_intermediate_frequency:
            for bus, intermediate_frequency in self._pending_set_intermediate_frequency.items():
                job.set_intermediate_frequency(element=bus, freq=intermediate_frequency)  # type: ignore[union-attr]
                self._qm.calibrate_element(bus)
            self._pending_set_intermediate_frequency = {}

        return job

    def run(self, program: Program) -> RunningQmJob:
        """Runs the QUA Program.

        Creates, for every execution, an instance of a QuantumMachine class and executes the QUA program on it.
        After execution, the job generated by the Quantum Machines Manager is returned.

        Args:
            program (Program): QUA Program to be run on Quantum Machines instruments.

        Returns:
            job: Quantum Machines job.
        """

        return self._qm.execute(program)

    def get_acquisitions(self, job: QmJob | JobApi) -> dict[str, np.ndarray]:
        """Fetches the results from the execution of a QUA Program.

        Once the results have been fetched, they are returned wrapped in a QuantumMachinesResult instance.

        Args:
            job (QmJob): Job that provides the result handles.

        Returns:
            QuantumMachinesResult: Quantum Machines result instance.
        """
        result_handles_fetchers = job.result_handles
        result_handles_fetchers.wait_for_all_values(timeout=self.settings.timeout)
        results = {
            name: handle.fetch_all(flat_struct=True) for name, handle in job.result_handles if handle is not None
        }
        return {name: data for name, data in results.items() if data is not None}

    def simulate(self, program: Program) -> RunningQmJob:
        """Simulates the QUA Program.

        Creates, for every simulation, an instance of a QuantumMachine class and executes the QUA program on it.
        It returns the running job instance.

        Args:
            program (Program): QUA Program to be simulated on Quantum Machines instruments.

        Returns:
            job: Quantum Machines job.
        """
        return self._qm.simulate(program, SimulationConfig(40_000))
