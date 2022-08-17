"""__init__.py"""

from .config import __version__, logger
from .experiment import Experiment
from .platform import build_platform, save_platform
from .result import Results
from .utils.load_data import load
