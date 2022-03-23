import pytest

from qililab import Qililab


@pytest.fixture
def qililab():
    """_summary_

    Returns:
        _type_: _description_
    """
    return Qililab()


class TestQililab:
    """Unitary tests checking the Qililab initialization steps and values"""

    def test_qililab_constructor(self, qililab):
        """_summary_

        Args:
            qililab (_type_): _description_
        """
        assert isinstance(qililab, Qililab)
