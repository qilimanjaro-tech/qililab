import os

import pytest

from qililab.qprogram.qblox_compiler import QbloxCompiler
from qililab.utils.serialization import (
    DeserializationError,
    SerializationError,
    deserialize,
    deserialize_from,
    serialize,
    serialize_to,
)
from qililab.waveforms import Gaussian, Square


class TestSerialization:
    def test_serialization_of_not_registered_class_raises_error(self):
        compiler = QbloxCompiler()

        with pytest.raises(SerializationError):
            _ = serialize(compiler)

        with pytest.raises(SerializationError):
            serialize_to(compiler, "compiler.yml")

    def test_deserialization_with_wrong_yaml_raises_error(self):
        not_valid_yaml = "&id006 !QProgram"

        with pytest.raises(DeserializationError):
            _ = deserialize(not_valid_yaml)

        with open("not_valid_yaml.yml", "w", encoding="utf-8") as file:
            file.write(not_valid_yaml)
        with pytest.raises(DeserializationError):
            _ = deserialize_from("not_valid_yaml.yml")
        os.remove("not_valid_yaml.yml")

    # def test_deserialization_with_wrong_cls_raises_error(self):
    #     waveform = Square(amplitude=1.0, duration=2000)

    #     serialized = serialize(waveform)
    #     with pytest.raises(DeserializationError):
    #         _ = deserialize(serialized, Gaussian)

    #     serialize_to(waveform, "waveform.yml")
    #     with pytest.raises(DeserializationError):
    #         _ = deserialize_from("waveform.yml", Gaussian)
    #     os.remove("waveform.yml")
