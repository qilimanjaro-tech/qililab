"""__init__.py"""
import copy

from .experiment import Experiment

settings = copy.deepcopy(Experiment.ExperimentSettings())
