import os

import pytest

from qililab.qprogram.qblox_compiler import QbloxCompiler
from qililab.qprogram import Experiment
from qililab.utils.serialization import (
    DeserializationError,
    SerializationError,
    deserialize,
    deserialize_from,
    serialize,
    serialize_to,
)
from qililab.waveforms import Gaussian
from qililab.typings.enums import Parameter


class TestSerialization:
    @pytest.mark.xfail(reason="Fails because YAML is instantiated as unsafe.")
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

    def test_deserialization_with_wrong_cls_raises_error(self):
        serialized = "!Square {amplitude: 1.0, duration: 2000}\n"

        with pytest.raises(DeserializationError):
            _ = deserialize(serialized, Gaussian)

        with open("waveform.yml", "w", encoding="utf-8") as file:
            file.write(serialized)
        with pytest.raises(DeserializationError):
            _ = deserialize_from("waveform.yml", Gaussian)
        os.remove("waveform.yml")

    def test_experiment_with_set_parameter_serialization(self):
        experiment = Experiment(label="spectroscopy", description="Amplitude scan")
        experiment.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.AMPLITUDE, value=0.42)

        serialized = serialize(experiment)

        assert "!SetParameter" in serialized

        deserialize(serialized, Experiment)
