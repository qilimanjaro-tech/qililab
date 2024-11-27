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
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from qililab.settings.instruments.channel_settings import (
    ChannelSettings,
    FromIQInputMixin,
    FromSingleInputMixin,
    ToIQOutputMixin,
    ToSingleOutputMixin,
)
from qililab.settings.instruments.input_settings import InputSettings
from qililab.settings.instruments.instrument_settings import InstrumentSettings
from qililab.settings.instruments.output_settings import OutputSettings


class ControllerPort(BaseModel):
    controller: str
    port: int


class FemPort(BaseModel):
    controller: str
    fem: int
    port: int


TPortType = TypeVar("TPortType", ControllerPort, FemPort)


class OctavePort(BaseModel):
    octave: str
    port: int


class LFOutput(OutputSettings, Generic[TPortType]):
    connected_to: TPortType
    offset: float = Field(default=0.0, description="Output offset.")
    delay: int = Field(default=0, description="Output delay in ns.")


class RFOutput(OutputSettings, Generic[TPortType]):
    connected_to: OctavePort
    connection_i: TPortType
    connection_q: TPortType
    offset_i: float = Field(default=0.0)
    offset_q: float = Field(default=0.0)
    gain: float = Field(default=0.0, ge=-20, le=20, multiple_of=0.5, description="Output gain in dB.")
    lo_frequency: float = Field(default=10e9, ge=2e9, le=18e9)


class OpxLFOutput(LFOutput[ControllerPort]):
    pass


class Opx1000LFOutput(LFOutput[FemPort]):
    pass


class OpxRFOutput(RFOutput[ControllerPort]):
    pass


class Opx1000RFOutput(RFOutput[FemPort]):
    pass


class LFInput(InputSettings, Generic[TPortType]):
    connected_to: TPortType
    offset: float = Field(default=0.0, description="DC offset to the input.")
    gain: int = Field(default=0, description="Gain of the pre-ADC amplifier.")


class RFInput(InputSettings, Generic[TPortType]):
    connected_to: OctavePort
    connection_i: TPortType
    connection_q: TPortType
    offset_i: float = Field(default=0.0, description="DC offset to the I input.")
    offset_q: float = Field(default=0.0, description="DC offset to the Q input.")
    gain_i: int = Field(default=0, description="Gain of the pre-ADC amplifier of the I input.")
    gain_q: int = Field(default=0, description="Gain of the pre-ADC amplifier of the Q input.")
    lo_frequency: float = Field(default=10e9, ge=2e9, le=18e9)


class OpxLFInput(LFInput[ControllerPort]):
    pass


class Opx1000LFInput(LFInput[FemPort]):
    pass


class OpxRFInput(RFInput[ControllerPort]):
    pass


class Opx1000RFInput(RFInput[FemPort]):
    pass


class ReadoutElementMixin(BaseModel):
    time_of_flight: int = Field(default=0, ge=0)
    smearing: int = Field(default=0, ge=0)


class ModulatedElementMixin(BaseModel):
    intermediate_frequency: float


class OPXElement(ChannelSettings[str]):
    pass


class SingleElement(ToSingleOutputMixin, OPXElement):
    pass


class IQElement(ModulatedElementMixin, ToIQOutputMixin, OPXElement):
    lo_frequency: float
    mixer_correction: list[float] = Field(default=[1.0, 0.0, 0.0, 1.0])


class IQReadoutElement(ReadoutElementMixin, FromIQInputMixin, IQElement):
    pass


class RFElement(ModulatedElementMixin, ToSingleOutputMixin, OPXElement):
    pass


class RFReadoutElement(ReadoutElementMixin, FromSingleInputMixin, RFElement):
    pass


class OPXSettings(InstrumentSettings):
    timeout: int = Field(default=600, ge=0, description="Timeout for communicating with QOP in seconds.")
    run_octave_calibration: bool = Field(
        default=True,
        description="Flag to indicate if octave calibration should be run on creating a new Quantum Machine.",
    )
    outputs: list[OpxLFOutput | OpxRFOutput] = Field(...)
    inputs: list[OpxLFInput | OpxRFInput] = Field(...)
    elements: list[SingleElement | IQElement | IQReadoutElement | RFElement | RFReadoutElement] = Field(...)

    def to_qua_config(self):
        def add_controller(controller: str):
            if controller not in controllers:
                controllers[controller] = {"analog_outputs": {}, "analog_inputs": {}, "digital_outputs": {}}

        def add_octave(octave: str):
            if octave not in octaves:
                octaves[octave] = {"RF_outputs": {}, "RF_inputs": {}, "IF_outputs": {}}

        def add_controller_analog_output(controller: str, port: int, offset: float, delay: int):
            add_controller(controller=controller)
            if port not in controllers[controller]["analog_outputs"]:
                controllers[controller]["analog_outputs"][port] = {"offset": offset, "delay": delay}

        def add_octave_rf_output(output: OpxRFOutput):
            add_controller_analog_output(
                controller=output.connection_i.controller,
                port=output.connection_i.port,
                offset=output.offset_i,
                delay=0,
            )
            add_controller_analog_output(
                controller=output.connection_q.controller,
                port=output.connection_q.port,
                offset=output.offset_q,
                delay=0,
            )

            octave = output.connected_to.octave
            port = output.connected_to.port
            add_octave(octave=octave)
            if port not in octaves[octave]["RF_outputs"]:
                octaves[octave]["RF_outputs"][port] = {
                    "LO_frequency": output.lo_frequency,
                    "LO_source": "internal",
                    "gain": output.gain,
                    "output_mode": "always_on",
                    "input_attenuators": "OFF",
                    "I_connection": (output.connection_i.controller, output.connection_i.port),
                    "Q_connection": (output.connection_q.controller, output.connection_q.port),
                }

        def add_controller_analog_input(controller: str, port: int, offset: float, gain: int):
            add_controller(controller=controller)
            if port not in controllers[controller]["analog_inputs"]:
                controllers[controller]["analog_inputs"][port] = {"offset": offset, "gain_db": gain}

        def add_octave_rf_input(input: OpxRFInput):
            add_controller_analog_input(
                controller=input.connection_i.controller,
                port=input.connection_i.port,
                offset=input.offset_i,
                gain=input.gain_i,
            )
            add_controller_analog_input(
                controller=input.connection_q.controller,
                port=input.connection_q.port,
                offset=input.offset_q,
                gain=input.gain_q,
            )

            octave = input.connected_to.octave
            port = input.connected_to.port
            add_octave(octave=octave)
            if port not in octaves[octave]["RF_inputs"]:
                octaves[octave]["RF_inputs"][port] = {
                    "RF_source": "RF_in",
                    "LO_frequency": input.lo_frequency,
                    "LO_source": "internal",
                    "IF_mode_I": "direct",
                    "IF_mode_Q": "direct",
                }
            if "IF_out1" not in octaves[octave]["IF_outputs"]:
                octaves[octave]["IF_outputs"]["IF_out1"] = {
                    "port": (output.connection_i.controller, output.connection_i.port),
                    "name": "out1",
                }
            if "IF_out2" not in octaves[octave]["IF_outputs"]:
                octaves[octave]["IF_outputs"]["IF_out2"] = {
                    "port": (output.connection_q.controller, output.connection_q.port),
                    "name": "out2",
                }

        def add_single_element(element: SingleElement, connected_to: ControllerPort):
            elements[element.id] = {"singleInput": {"port": (connected_to.controller, connected_to.port)}}

        def add_iq_element(
            element: IQElement | IQReadoutElement, connection_i: ControllerPort, connection_q: ControllerPort
        ):
            mixer_name = f"mixer_{element.id}"
            mixers[mixer_name] = {
                "intermediate_frequency": element.intermediate_frequency,
                "lo_frequency": element.lo_frequency,
                "correction": element.mixer_correction,
            }

            elements[element.id] = {
                "mixInputs": {
                    "I": (connection_i.controller, connection_i.port),
                    "Q": (connection_q.controller, connection_q.port),
                    "lo_frequency": element.lo_frequency,
                    "mixer": mixer_name,
                },
                "intermediate_frequency": element.intermediate_frequency,
            }

            if isinstance(element, IQReadoutElement):
                elements[element.id]["time_of_flight"] = element.time_of_flight
                elements[element.id]["smearing"] = element.smearing

        def add_rf_element(element: RFElement | RFReadoutElement, connected_to: OctavePort):
            elements[element.id] = {
                "RF_inputs": {"port": (connected_to.octave, connected_to.port)},
                "intermediate_frequency": element.intermediate_frequency,
            }

            if isinstance(element, RFReadoutElement):
                elements[element.id]["time_of_flight"] = element.time_of_flight
                elements[element.id]["smearing"] = element.smearing

        controllers = {}
        octaves = {}
        elements = {}
        mixers = {}

        for output in self.outputs:
            if isinstance(output, OpxLFOutput):
                add_controller_analog_output(
                    controller=output.connected_to.controller,
                    port=output.connected_to.port,
                    offset=output.offset,
                    delay=output.delay,
                )
            if isinstance(output, OpxRFOutput):
                add_octave_rf_output(output=output)

        for input in self.inputs:
            if isinstance(input, OpxLFInput):
                pass

        for element in self.elements:
            if isinstance(element, SingleElement):
                connected_to = next(
                    output.connected_to
                    for output in self.outputs
                    if output.port == element.output and isinstance(output, LFOutput)
                )
                add_single_element(element=element, connected_to=connected_to)
            if isinstance(element, (IQElement, IQReadoutElement)):
                connection_i = next(
                    output.connected_to
                    for output in self.outputs
                    if output.port == element.output_i and isinstance(output, LFOutput)
                )
                connection_q = next(
                    output.connected_to
                    for output in self.outputs
                    if output.port == element.output_q and isinstance(output, LFOutput)
                )
                add_iq_element(element=element, connection_i=connection_i, connection_q=connection_q)
            if isinstance(element, (RFElement, RFReadoutElement)):
                connected_to = next(
                    output.connected_to
                    for output in self.outputs
                    if output.port == element.output and isinstance(output, RFOutput)
                )
                add_rf_element(element=element, connected_to=connected_to)

        return {
            "version": 1,
            "controllers": controllers,
            "octaves": octaves,
            "elements": elements,
            "mixers": mixers,
            "waveforms": {},
            "integration_weights": {},
            "pulses": {},
            "digital_waveforms": {},
        }
