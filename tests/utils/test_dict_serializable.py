""" Tests for DictSerializable protocol"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from qililab.utils import DictSerializable, from_dict
from qililab.utils.dict_serializable import DictSerializableFactory, is_dict_serializable_object


class A(DictSerializable):
    """Dummy class for testing"""

    def __init__(self, attr1: int) -> None:
        self.attr1: int = attr1
        self.attr2: list[str] = ["a", "b", "c"]
        self.attr3: set[float] = {0, 1, 2}
        self.attr4: tuple[B, ...] = (B(0), B(1), B(2))
        self.attr5: C = C()
        self.attr6: D = D()
        self.attr7: dict = {"key": 123}
        self.attr8: dict = {"type": "A", "key": 123}


class B(DictSerializable):
    """Dummy class for testing"""

    def __init__(self, attr: int) -> None:
        self.attr: int = attr


@dataclass
class C(DictSerializable):
    uuid: UUID = field(default_factory=uuid4, init=False)


@dataclass(frozen=True)
class D(DictSerializable):
    uuid: UUID = field(default_factory=uuid4, init=False)


class TestDictSerializable:
    """Unit tests for utils.dict_serializable module"""

    def test_dict_serializable(self):
        """Test that DictSerializable object is (de)serialized correctly."""
        origin_object = A(123)

        serialized_dictionary = origin_object.to_dict()
        assert "type" in serialized_dictionary
        assert "attributes" in serialized_dictionary

        deserialized_object = from_dict(serialized_dictionary)
        assert isinstance(deserialized_object, A)

        assert origin_object.attr1 == deserialized_object.attr1
        assert all(a == b for a, b in zip(origin_object.attr2, deserialized_object.attr2))
        assert all(a == b for a, b in zip(origin_object.attr3, deserialized_object.attr3))
        assert all(isinstance(obj, B) for obj in deserialized_object.attr4)
        assert all(a.attr == b.attr for a, b in zip(origin_object.attr4, deserialized_object.attr4))
        assert isinstance(deserialized_object.attr5, C)
        assert origin_object.attr5.uuid == origin_object.attr5.uuid
        assert isinstance(deserialized_object.attr6, D)
        assert origin_object.attr6.uuid == origin_object.attr6.uuid

        assert isinstance(deserialized_object.attr7, dict)
        assert origin_object.attr7["key"] == deserialized_object.attr7["key"]

        assert isinstance(deserialized_object.attr8, dict)
        assert origin_object.attr8["type"] == deserialized_object.attr8["type"]
        assert origin_object.attr8["key"] == deserialized_object.attr8["key"]

    @pytest.mark.parametrize(
        "obj, expected_result",
        [
            (C(), False),
            ({"key": 123}, False),
            ({"type": "C"}, False),
            ({"type": "C", "attributes": {"uuid": UUID("eadbecf6-4431-4b55-a861-88487b18296a")}}, True),
        ],
    )
    def test_is_dict_serializable_object(self, obj: object, expected_result: bool):
        """Test internal `is_dict_serializable_object` function."""
        result = is_dict_serializable_object(obj)
        assert result == expected_result

    def test_dict_serializable_factory(self):
        """Test internal `DictSerializableFactory`."""
        a_cls = DictSerializableFactory.get("A")
        assert issubclass(a_cls, DictSerializable)

        with pytest.raises(ValueError):
            _ = DictSerializableFactory.get("NotRegistered")
