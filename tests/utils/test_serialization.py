import base64
import os

import dill
import numpy as np
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
from qililab.waveforms import Gaussian, IQPair, Square
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

    def test_deserialize_rejects_python_object_apply(self, tmp_path):
        # QILILAB-01: the unsafe loader honored !!python/object/apply (arbitrary code execution).
        marker = tmp_path / "should_not_exist"
        payload = f'!!python/object/apply:os.system ["touch {marker}"]'

        with pytest.raises(DeserializationError):
            deserialize(payload)
        # The marker must not exist: proves no code executed, not merely a late raise.
        assert not marker.exists()

        file_path = tmp_path / "attack.yml"
        file_path.write_text(payload, encoding="utf-8")
        with pytest.raises(DeserializationError):
            deserialize_from(str(file_path))
        assert not marker.exists()

    def test_deserialize_rejects_python_name(self):
        with pytest.raises(DeserializationError):
            deserialize("!!python/name:os.system")

    def test_deserialize_rejects_function_and_lambda_tags(self, tmp_path):
        # QILILAB-01: !function / !lambda run dill.loads on attacker base64.
        marker = tmp_path / "dill_marker"

        class _Boom:
            def __reduce__(self):
                return (os.system, (f"touch {marker}",))

        payload = base64.b64encode(dill.dumps(_Boom(), recurse=True)).decode("utf-8")

        with pytest.raises(DeserializationError):
            deserialize(f"!function {payload}")
        assert not marker.exists()

        with pytest.raises(DeserializationError):
            deserialize(f"!lambda {payload}")
        assert not marker.exists()

    def test_deserialize_rejects_gated_type_and_defaultdict(self):
        # QILILAB-01: !type / !defaultdict import an attacker-supplied name; allow-list is empty.
        with pytest.raises(DeserializationError):
            deserialize("!type os.system")
        with pytest.raises(DeserializationError):
            deserialize("!defaultdict {default_factory: os.system, items: {}}")

    def test_deserialize_preserves_data_and_class_tags(self):
        # Regression: the safe loader must keep every legitimate qililab round-trip working.
        assert isinstance(deserialize(serialize(Square(amplitude=1.0, duration=50)), Square), Square)
        assert isinstance(
            deserialize(serialize(Gaussian(amplitude=0.5, duration=20, num_sigmas=4)), Gaussian), Gaussian
        )
        pair = IQPair(I=Square(amplitude=0.5, duration=10), Q=Square(amplitude=0.5, duration=10))
        assert isinstance(deserialize(serialize(pair), IQPair), IQPair)

        array = deserialize(serialize(np.array([1.0, 2.0, 3.0])))
        assert isinstance(array, np.ndarray)
        np.testing.assert_array_equal(array, np.array([1.0, 2.0, 3.0]))
        assert deserialize(serialize((1, 2, 3))) == (1, 2, 3)
        assert deserialize(serialize(3 + 4j)) == 3 + 4j
        assert deserialize("a: 1\nb: [1, 2, 3]\n") == {"a": 1, "b": [1, 2, 3]}

    def test_deserialize_trust_code_opt_in(self):
        # The escape hatch restores the old unsafe behavior for trusted input.
        assert deserialize("!type os.system", trust_code=True) is os.system
