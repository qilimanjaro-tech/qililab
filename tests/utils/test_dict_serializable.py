""" Tests for DictSerializable protocol"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from qililab.utils import DictSerializable, from_dict


class A(DictSerializable):
    """Dummy class for testing"""

    def __init__(self, attr1: int) -> None:
        self.attr1: int = attr1
        self.attr2: list[str] = ["a", "b", "c"]
        self.attr3: set[float] = {0, 1, 2}
        self.attr4: tuple[B, ...] = (B(0), B(1), B(2))
        self.attr5: C = C()
        self.attr6: D = D()


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
        assert isinstance(origin_object.attr5, C)
        assert origin_object.attr5.uuid == origin_object.attr5.uuid
        assert isinstance(origin_object.attr6, D)
        assert origin_object.attr6.uuid == origin_object.attr6.uuid
