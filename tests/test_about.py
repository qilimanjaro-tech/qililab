"""Unit tests for the `about` function."""
import importlib
import platform
import sys

import pyvisa_py
import qblox_instruments
import qcodes
import qcodes_contrib_drivers
import qpysequence
import qilisdk
import qililab as ql

about_module = importlib.import_module("qililab.about")


def _expected_base_output() -> str:
    return (
        f"Platform info:             {platform.platform(aliased=True)}\n"
        f"Python version:            {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}\n"
        f"PyVISA version:            {pyvisa_py.__version__}\n"
        f"QCodes version:            {qcodes.__version__}\n"
        f"QCodes Contrib version:    {qcodes_contrib_drivers.__version__}\n"
        f"Qblox Instrument version:  {qblox_instruments.__version__}\n"
        f"Qpysequence version:       {qpysequence.__version__}\n"
        f"QiliSDK version:           {qilisdk.__version__}\n"
    )


def test_about_without_quantum_machines(monkeypatch, capsys):
    def _qm_stub(*_args, **_kwargs):
        raise AssertionError("Quantum Machines functions should not be invoked in this scenario")

    monkeypatch.setattr(about_module, "qm_version", _qm_stub)

    ql.about()

    captured = capsys.readouterr().out
    assert captured == _expected_base_output()


def test_about_with_quantum_machines(monkeypatch, capsys):
    monkeypatch.setattr(about_module, "qm_version", "1.2.3")

    ql.about()

    captured = capsys.readouterr().out
    assert captured == _expected_base_output() + "Quantum Machines version:  1.2.3\n"
