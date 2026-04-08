import pytest

from qililab.core import Domain, Variable, requires_domain


class DummyWithDomain:
    def __init__(self):
        self.calls: list[Variable | None] = []

    @requires_domain("var", Domain.Time)
    def method(self, *, var: Variable | None = None):
        self.calls.append(var)
        return var


def test_requires_domain_adds_default_when_missing():
    dummy = DummyWithDomain()
    result = dummy.method()
    assert result is None
    assert dummy.calls == [None]


def test_requires_domain_validates_domain():
    dummy = DummyWithDomain()
    good = Variable("ok", domain=Domain.Time)
    assert dummy.method(var=good) is good

    bad = Variable("bad", domain=Domain.Frequency)
    with pytest.raises(ValueError, match="Expected domain QProgramDomain.Time"):
        dummy.method(var=bad)


# def test_domain_yaml_roundtrip():
#     class DummyNode:
#         value = "Frequency-2"

#     node = DummyNode()
#     domain = Domain.from_yaml(None, node)
#     assert domain is Domain.Frequency
