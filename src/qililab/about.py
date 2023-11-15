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

r"""
This module contains a function to display all the details of the Qililab installation.
"""
import platform
import sys
from subprocess import check_output  # nosec B404

import pyvisa_py
import qblox_instruments
import qcodes
import qcodes_contrib_drivers
import qibo
import qpysequence
from qm.version import __version__ as qm_version


def about():
    """
    Prints the information for Qililab installation.
    """
    print(check_output([sys.executable, "-m", "pip", "show", "qililab"]).decode())  # nosec B603
    print(f"Platform info:             {platform.platform(aliased=True)}")
    print(f"Python version:            {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")
    print(f"PyVISA version:            {pyvisa_py.__version__}")
    print(f"QCodes version:            {qcodes.__version__}")
    print(f"QCodes Contrib version:    {qcodes_contrib_drivers.__version__}")
    print(f"Qblox Instrument version:  {qblox_instruments.__version__}")
    print(f"Qpysequence version:       {qpysequence.__version__}")
    print(f"Quantum Machines version:  {qm_version}")
    print(f"Qibo version:              {qibo.__version__}")
