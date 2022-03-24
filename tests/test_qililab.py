import pytest

from qililab import Qililab


@pytest.fixture
def qililab() -> Qililab:
    """Test that instantiates the Qililab class

    Returns:
        Qililab: Qililab dummy object
    """
    return Qililab()


class TestQililab:
    """Unitary tests checking the Qililab initialization steps and values"""

    def test_qililab_constructor(self, qililab: Qililab) -> None:
        """Test of the constructor of the Qililab class

        Args:
            qililab (Qililab): Qililab dummy object
        """
        assert isinstance(qililab, Qililab)
