"""config.py"""
# global configuration settings
import logging
import os

# Logging level from 0 (all) to 4 (errors) (see https://docs.python.org/3/library/logging.html#logging-levels)
LIBRARY_LOG_LEVEL = int(os.environ.get("LIBRARY_LOG_LEVEL", 1))

# Configuration for logging mechanism


class CustomHandler(logging.StreamHandler):
    """Custom handler for logging algorithm."""

    def format(self, record):
        """Format the record with specific format."""
        from qililab import __version__

        fmt = f"[qililab] [{__version__}|%(levelname)s|%(asctime)s]: %(message)s"
        return logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S").format(record)


# allocate logger object
logger = logging.getLogger(__name__)
logger.setLevel(LIBRARY_LOG_LEVEL)
logger.addHandler(CustomHandler())
