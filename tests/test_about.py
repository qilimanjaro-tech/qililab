"""Unit tests for the `about` function."""

import platform
import sys

import pyvisa_py
import qblox_instruments
import qcodes
import qcodes_contrib_drivers
import qprogram
import qprogram_qblox
import qprogram_qdac
import qpysequence
import qililab as ql


def _expected_output() -> str:
    return (
        f"Platform info:             {platform.platform(aliased=True)}\n"
        f"Python version:            {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}\n"
        f"PyVISA version:            {pyvisa_py.__version__}\n"
        f"QCodes version:            {qcodes.__version__}\n"
        f"QCodes Contrib version:    {qcodes_contrib_drivers.__version__}\n"
        f"Qblox Instrument version:  {qblox_instruments.__version__}\n"
        f"Qpysequence version:       {qpysequence.__version__}\n"
        f"QProgram version:          {qprogram.__version__}\n"
        f"QProgram Qblox version:    {qprogram_qblox.__version__}\n"
        f"QProgram QDAC version:     {qprogram_qdac.__version__}\n"
    )


def test_about(capsys):
    ql.about()

    captured = capsys.readouterr().out
    assert captured == _expected_output()
    assert "Quantum Machines" not in captured
