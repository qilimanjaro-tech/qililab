"""Tests for the load function."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

from qililab import load
from qililab.utils import Loop
from tests.data import experiment, results_one_loops, results_two_loops


@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda path: path == Path("results.yml"))
@patch("qililab.utils.load_data.open")
@patch("ruamel.yaml.YAML.load", return_value=deepcopy(results_two_loops))
def test_load_results_two_loops(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock):
    """Test load Results class."""
    _, result = load(path="", load_experiment=True)
    mock_load.assert_called_once()
    mock_open.assert_called_once()
    mock_os.assert_called()
    assert result is not None
    assert result.loops is not None
    assert isinstance(result.loops[0], Loop)


@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda path: path == Path("results.yml"))
@patch("qililab.utils.load_data.open")
@patch("ruamel.yaml.YAML.load", return_value=deepcopy(results_one_loops))
def test_load_results_one_loop(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock):
    """Test load Results class."""
    _, result = load(path="", load_experiment=True)
    mock_load.assert_called_once()
    mock_open.assert_called_once()
    mock_os.assert_called()
    assert result is not None
    assert result.loops is not None
    assert isinstance(result.loops[0], Loop)


@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda path: path == Path("experiment.yml"))
@patch("qililab.utils.load_data.open")
@patch("ruamel.yaml.YAML.load", return_value=deepcopy(experiment))
def test_load_experiment(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock):
    """Test load Experiment class."""
    exp, _ = load(path="", load_experiment=True)
    mock_load.assert_called_once()
    mock_open.assert_called_once()
    mock_os.assert_called()
    assert exp is not None
    assert exp.options is not None
    assert exp.options.loops is not None
    assert isinstance(exp.options.loops[0], Loop)


@patch("qililab.utils.load_data.os.path.exists", side_effect=lambda _: True)
@patch("qililab.utils.load_data.open", side_effect=lambda filepath, *args, **kwargs: filepath)
@patch(
    "ruamel.yaml.YAML.load",
    side_effect=lambda stream: deepcopy(results_one_loops if stream.name.endswith("results.yml") else experiment),
)
def test_load_experiment_and_results(mock_load: MagicMock, mock_open: MagicMock, mock_os: MagicMock):
    """Test load Experiment class."""
    exp, results = load(path="", load_experiment=True)
    mock_load.assert_called()
    mock_open.assert_called()
    mock_os.assert_called()
    assert exp is not None
    assert exp.options is not None
    assert exp.options.loops is not None
    assert isinstance(exp.options.loops[0], Loop)
    assert exp.results is results
    assert results is not None
    assert results.loops is not None
    assert isinstance(results.loops[0], Loop)


@patch("qililab.utils.load_data.glob.glob", return_value=["one", "two"])
@patch("qililab.utils.load_data.os.path.getctime", return_value=0)
def test_load_without_path(mock_cttime: MagicMock, mock_glob: MagicMock):
    """Test load without path."""
    exp, results = load(load_experiment=True)
    mock_cttime.assert_called()
    mock_glob.assert_called()
    assert exp is None
    assert results is None
