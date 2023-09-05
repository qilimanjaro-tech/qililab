# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This function contains all the fitting models used in experiment analysis."""
from abc import ABC, abstractmethod

import numpy as np

# pylint: disable=too-few-public-methods


class FittingModel(ABC):
    """Abstract Base Class defining a fitting model.

    An experiment analysis should inherit from a child of this class, such that the ``func`` method can be used
    to fit the experiment results.

    A class is used instead of a function to make sure the user can see the signature of the fitting function.
    """

    @staticmethod
    @abstractmethod
    def func(xdata: np.ndarray, *args):
        """The model function, func(x, …) used to fit the post-processed data.

        It must take the independent variable as the first argument and the parameters to fit as separate remaining
        arguments.

        Args:
            xdata (np.ndarray): independent variable
            *args: parameters to fit

        Returns:
            np.ndarray: model function evaluated at xdata
        """


class Cos(FittingModel):
    """Cosine model function."""

    @staticmethod
    def func(xdata: np.ndarray, amplitude: float, frequency: float, phase: float, offset: float) -> np.ndarray:  # type: ignore  # pylint: disable=arguments-differ
        """Cosine model function.

        It must take the independent variable as the first argument and the parameters to fit as separate remaining
        arguments.

        Args:
            xdata (ndarray): amplitude of the X gate
            amplitude (float): amplitude of the cosine function
            frequency (float): frequency in Hz (f, not omega!)
            phase (float): phase in rad
            offset (float): offset
        """
        return amplitude * np.cos(2 * np.pi * frequency * xdata + phase) + offset


class Exp(FittingModel):
    """Exponential model function."""

    @staticmethod
    def func(xdata: np.ndarray, amplitude: float, rate: float, offset: float) -> np.ndarray:  # type: ignore  # pylint: disable=arguments-differ
        """Exponential model function.

        It must take the independent variable as the first argument and the parameters to fit as separate remaining
        arguments.

        Args:
            xdata (ndarray): data of the x-axis
            amplitude (float): amplitude of the exponential function
            rate (float): rate of growth or decay
            offset (float): offset
        """
        return amplitude * np.exp(rate * xdata) + offset
