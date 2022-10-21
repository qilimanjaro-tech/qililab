"""Run circuit experiment"""
import os
from pathlib import Path

from qiboconnection.api import API

from qililab import build_platform

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run(connection: API | None = None):
    """Load the platform 'sauron' from the DB."""
    platform = build_platform(name="sauron_vna")
    platform.connect()
    platform.close()


if __name__ == "__main__":
    run()
