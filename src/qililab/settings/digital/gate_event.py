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


def _split_tag_and_payload(txt: str) -> tuple[str, str]:
    """
    Split a serialized scalar beginning with '!Tag' from its payload. Works for both
    flow-style and block-style dumps.

    Examples:
      "!IQDrag {amp: 1.0}\n"     -> ("!IQDrag", "{amp: 1.0}\n")
      "!IQPair\nI: !Gauss ...\n" -> ("!IQPair", "I: !Gauss ...\n")
    """
    s = txt.strip()
    if not s.startswith("!"):
        return "", s
    parts = s.split(None, 1)  # split on any whitespace
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _to_external(obj: Any) -> Any:
    """
    Convert nested objects into a JSON-friendly structure:
    - Waveform/IQWaveform  -> {"type": "<tag>", ...params...} (recursively)
    - Lists/Tuples/Dicts   -> walked recursively
    - Other scalars        -> unchanged
    """
    if isinstance(obj, (Waveform, IQWaveform)):
        # Serialize to YAML to recover the tag and parameters
        txt = serialize(obj)
        tag, payload = _split_tag_and_payload(txt)
        kind = tag.lstrip("!") or obj.__class__.__name__
        params = deserialize(payload) if payload else {}
        # Critically: recursively normalize nested values (e.g., I,Q in IQPair)
        params = _to_external(params)
        return {"type": kind, **params}

    if isinstance(obj, dict):
        return {k: _to_external(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_to_external(v) for v in obj]

    return obj


def _from_external(obj: Any) -> Any:
    """
    Inverse of _to_external:
    - {"type": "...", ...} -> real Waveform/IQWaveform (recursively fixing nested)
    - Lists/Tuples/Dicts   -> walked recursively
    """
    # A nested waveform mapping?
    if isinstance(obj, dict) and any(k in obj for k in ("type", "kind", "__type__")):
        kind = obj.get("kind") or obj.get("type") or obj.get("__type__")
        if not kind:
            raise TypeError("waveform dict must include a 'type' (or 'kind'/'__type__') key")

        # Recurse into params first so nested waveforms become real objects,
        # which ensures serialize(params) re-creates nested !Tags.
        params = {k: _from_external(v) for k, v in obj.items() if k not in {"kind", "type", "__type__"}}

        param_txt = serialize(params).strip()
        # Accept either flow or block style for params
        if param_txt.startswith("{"):
            wf_yaml = f"!{kind} {param_txt}\n"
        else:
            wf_yaml = f"!{kind}\n{param_txt}\n"

        return deserialize(wf_yaml)

    # Generic container recursion
    if isinstance(obj, dict):
        return {k: _from_external(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_from_external(v) for v in obj]
    return obj


def _wf_to_mapping(wf: Waveform | IQWaveform) -> dict[str, Any]:
    """Waveform/IQWaveform -> external mapping (handles nested, e.g., IQPair)."""
    mapped = _to_external(wf)
    # Type checker assurance
    if not (isinstance(mapped, dict) and ("type" in mapped or "kind" in mapped or "__type__" in mapped)):
        raise TypeError("internal error: _to_external did not return a waveform mapping")
    # normalize discriminator key to 'type'
    if "type" not in mapped:
        mapped["type"] = mapped.pop("kind", mapped.pop("__type__", mapped.get("type")))
    return cast("dict[str, Any]", mapped)


def _mapping_to_wf(d: dict[str, Any]) -> Waveform | IQWaveform:
    """External mapping -> Waveform/IQWaveform (handles nested, e.g., IQPair)."""
    obj = _from_external(d)
    if isinstance(obj, Waveform):
        return cast("Waveform", obj)
    if isinstance(obj, IQWaveform):
        return cast("IQWaveform", obj)
    raise TypeError("waveform must be Waveform/IQWaveform after deserialization")


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
        if v is None:
            return None
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
