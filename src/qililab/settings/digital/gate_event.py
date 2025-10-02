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

from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from qililab.utils.serialization import DeserializationError, deserialize, serialize
from qililab.waveforms.iq_waveform import IQWaveform
from qililab.waveforms.waveform import Waveform

if TYPE_CHECKING:
    from qililab.typings.enums import Parameter


def _wf_to_mapping(wf: Waveform | IQWaveform) -> dict[str, Any]:
    """
    Convert an arbitrary Waveform/IQWaveform instance into a plain dict:
    {'kind': <tag or class name>, ...params...}
    We reuse your ruamel-based serialize() and strip the trailing newline.
    """
    txt = serialize(wf).strip()  # e.g. "!IQDrag {amplitude: 1.0, ...}"
    tag, _, payload = txt.partition(" ")  # tag is like "!IQDrag"
    kind = tag.lstrip("!") or wf.__class__.__name__
    params = deserialize(payload) if payload else {}
    # Flatten so 'kind' lives at the same level as the parameters
    return {"type": kind, **params}


def _mapping_to_wf(d: dict[str, Any]) -> Waveform | IQWaveform:
    """
    Convert {'kind': 'IQDrag', ...params...} back into a waveform instance
    by round-tripping through your deserialize() which already knows how
    to construct from tagged YAML.
    """
    # pull discriminator from several common keys if needed
    kind = d.get("kind") or d.get("type") or d.get("__type__")
    if not kind:
        raise TypeError("waveform dict must include a 'kind' (or 'type') key")

    # Remove the discriminator and dump the rest in flow style
    params = {k: v for k, v in d.items() if k not in {"kind", "type", "__type__"}}
    string = serialize(params)  # -> "{amplitude: 1.0, ...}"
    # Rebuild the tagged YAML that your deserialize() expects
    wf_yaml = f"!{kind} {string.strip()}\n"
    deserialized = deserialize(wf_yaml)
    if isinstance(deserialized, Waveform):
        return cast("Waveform", deserialized)
    if isinstance(deserialized, IQWaveform):
        return cast("IQWaveform", deserialized)
    raise TypeError("waveform must be Waveform/IQWaveform")


class GateEvent(BaseModel):
    """Settings for a single gate event. A gate event is an element of a gate schedule, which is the
    sequence of gate events that define what a gate does (the pulse events it consists of).

    A gate event is made up of GatePulseSettings, which contains pulse specific information, and extra arguments
    (bus and wait_time) which are related to the context in which the specific pulse in GatePulseSettings is applied

    Attributes:
        bus (str): bus through which the pulse is to be sent. The string has to match that of the bus alias in the runcard
        pulse (GatePulseSettings): settings of the bus to be launched
        wait_time (int): time to wait w.r.t gate start time (taken as 0) before launching the pulse
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bus: str
    waveform: Waveform | IQWaveform
    weights: IQWaveform | None = None
    phase: float = 0.0
    wait_time: int = 0
    options: dict | None = None

    @field_serializer("waveform")  # default is "always" → used by model_dump & model_dump_json
    def _serialize_waveform(self, waveform: Waveform | IQWaveform, _info):
        # Return a dict, not a string → nested object in model_dump()
        return _wf_to_mapping(waveform)

    @field_validator("waveform", mode="before")
    @classmethod
    def _load_waveform(cls, v):
        # Accept already-constructed objects
        if isinstance(v, (Waveform, IQWaveform)):
            return v
        # Accept the original tagged YAML string
        if isinstance(v, str):
            try:
                return deserialize(v, Waveform)
            except DeserializationError:
                return deserialize(v, IQWaveform)
        # Accept dicts (our JSON-friendly external shape)
        if isinstance(v, dict):
            return _mapping_to_wf(v)
        raise TypeError("waveform must be a Waveform/IQWaveform, tagged YAML string, or mapping")

    @field_serializer("weights")  # default is "always" → used by model_dump & model_dump_json
    def _serialize_weights(self, weights: IQWaveform, _info):
        # Return a dict, not a string → nested object in model_dump()
        return _wf_to_mapping(weights) if weights is not None else None

    @field_validator("weights", mode="before")
    @classmethod
    def _load_weights(cls, v):
        # Accept already-constructed objects
        if isinstance(v, IQWaveform):
            return v
        # Accept the original tagged YAML string
        if isinstance(v, str):
            return deserialize(v, IQWaveform)
        # Accept dicts
        if isinstance(v, dict):
            return _mapping_to_wf(v)
        raise TypeError("weights must be a IQWaveform, tagged YAML string, or mapping")

    def set_parameter(self, parameter: Parameter, value: float | str | bool):
        """Change a given parameter from settings. Will look up into subclasses.

        Args:
            parameter (Parameter): parameter to be set
            value (float | str | bool): value of the parameter
        """
        param = parameter.value
        if hasattr(self, param):
            setattr(self, param, value)
        else:
            setattr(self.waveform, param, value)

    def get_parameter(self, parameter: Parameter):
        """Get a parameter from settings. Will look up into subclasses.

        Args:
            parameter (Parameter): Parameter to get.
        """
        param = parameter.value
        if hasattr(self, param):
            return getattr(self, param)
        return getattr(self.waveform, param)
