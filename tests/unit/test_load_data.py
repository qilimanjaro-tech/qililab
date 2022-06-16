"""Tests for the load function."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from qililab import load
from qililab.utils import Loop, plot

from ..data import experiment, results_one_loops, results_two_loops


@patch("qililab.utils.plot_results.plt.show")
@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda path: path == Path("results.yml"))
@patch("qililab.utils.load_data.open")
@patch("qililab.utils.load_data.yaml.safe_load", return_value=results_two_loops)
def test_load_results_two_loops(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock, mock_plt: MagicMock):
    """Test load Results class."""
    _, result = load(path="")
    mock_load.assert_called_once()
    mock_open.assert_called_once()
    mock_os.assert_called()
    assert result is not None
    assert isinstance(result.loop, Loop)
    plot(result=result, loop=result.loop)
    mock_plt.assert_called()


@patch("qililab.utils.plot_results.plt.show")
@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda path: path == Path("results.yml"))
@patch("qililab.utils.load_data.open")
@patch("qililab.utils.load_data.yaml.safe_load", return_value=results_one_loops)
def test_load_results_one_loop(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock, mock_plt: MagicMock):
    """Test load Results class."""
    _, result = load(path="")
    mock_load.assert_called_once()
    mock_open.assert_called_once()
    mock_os.assert_called()
    assert result is not None
    assert isinstance(result.loop, Loop)
    plot(result=result, loop=result.loop)
    mock_plt.assert_called()


@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda path: path == Path("experiment.yml"))
@patch("qililab.utils.load_data.open")
@patch("qililab.utils.load_data.yaml.safe_load", return_value=experiment)
def test_load_experiment(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock):
    """Test load Experiment class."""
    exp, _ = load(path="")
    mock_load.assert_called_once()
    mock_open.assert_called_once()
    mock_os.assert_called()
    assert exp is not None
    assert exp.loop is not None
    assert isinstance(exp.loop, Loop)
