"""Experiment class."""
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform


class Experiment:
    """Execution class"""

    platform: Platform
    execution: Execution

    def __init__(self, experiment_name: str, platform_name: str):
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, experiment_name=experiment_name)

    def execute(self):
        """Run execution."""
        return self.execution.execute()
