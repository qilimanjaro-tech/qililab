"""Unit tests for the fitting models."""
import numpy as np

from qililab.experiment.portfolio import Cos, Exp


class TestFittingModels:
    """Unit tests for the fitting models."""

    def test_cos_func(self):
        """Test the cosine function."""
        xdata = np.linspace(0, 1, 100)
        amplitude = 9
        frequency = 1.23
        phase = 3.45
        offset = 5.67
        ydata = Cos.func(xdata, amplitude, frequency, phase, offset)
        assert np.allclose(ydata, amplitude * np.cos(2 * np.pi * frequency * xdata + phase) + offset)

    def test_exp_func(self):
        """Test the exponential function."""
        xdata = np.linspace(0, 100)
        amplitude = 10
        rate = 0.5
        offset = 5.67
        ydata = Exp.func(xdata, amplitude, rate, offset)
        assert np.allclose(ydata, amplitude * np.exp(rate * xdata) + offset)
