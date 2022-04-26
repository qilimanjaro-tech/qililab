"""ExecutionBuilder class"""
from qililab.experiment.execution.execution import Execution
from qililab.platform import Platform
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform) -> Execution:
        """Build Execution class.

        Args:
            platform (Platform): Platform object.

        Returns:
            Execution: Execution object.
        """
        return Execution()
