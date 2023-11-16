"""Unit tests for the `about` function."""
import io
import platform
import sys
from subprocess import check_output

import pyvisa_py
import qblox_instruments
import qcodes
import qcodes_contrib_drivers
import qibo
import qpysequence
from qm.version import __version__ as qm_version

import qililab as ql


def test_about():
    """Test that the `about` function prints the correct information."""
    capturedOutput = io.StringIO()
    sys.stdout = capturedOutput  # Redirect output
    ql.about()
    sys.stdout = sys.__stdout__  # Reset redirect

    expected_string = f"""{check_output([sys.executable, "-m", "pip", "show", "qililab"]).decode()}
Platform info:             {platform.platform(aliased=True)}
Python version:            {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}
PyVISA version:            {pyvisa_py.__version__}
QCodes version:            {qcodes.__version__}
QCodes Contrib version:    {qcodes_contrib_drivers.__version__}
Qblox Instrument version:  {qblox_instruments.__version__}
Qpysequence version:       {qpysequence.__version__}
Quantum Machines version:  {qm_version}
Qibo version:              {qibo.__version__}
"""

    assert expected_string == capturedOutput.getvalue()
