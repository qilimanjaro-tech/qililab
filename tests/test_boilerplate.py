import pytest

from boilerplate import BoilerPlate


@pytest.fixture
def boilerplate():
    """_summary_

    Returns:
        _type_: _description_
    """
    return BoilerPlate()


class TestBoilerPlate:
    """Unitary tests checking the Boilerplate initialization steps and values"""

    def test_boilerplate_constructor(self, boilerplate):
        """_summary_

        Args:
            boilerplate (_type_): _description_
        """
        assert isinstance(boilerplate, BoilerPlate)
