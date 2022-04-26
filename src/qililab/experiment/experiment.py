"""Experiment class."""
from qililab.experiment.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform


class Experiment:
    """Execution class"""

    platform: Platform
    execution: Execution

    def __init__(self, platform_name: str):
        self.platform = PLATFORM_MANAGER_DB.build(name=platform_name)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform)
