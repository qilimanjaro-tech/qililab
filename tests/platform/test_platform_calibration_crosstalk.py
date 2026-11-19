"""Tests for the static flux helpers using the crosstalk matrices in ``platform.calibration``."""

from unittest.mock import MagicMock, patch

import pytest

from qililab.data_management import build_platform
from qililab.platform import Platform
from qililab.qprogram import Calibration, CrosstalkMatrix
from qililab.typings.enums import Parameter

AC_BUS = "drive"
DC_BUSES = ("qdac_bus_1", "qdac_bus_2")


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    return build_platform(runcard="tests/runcards/qblox_and_qdac.yml")


@pytest.fixture(name="bus_mocks")
def fixture_bus_mocks(platform: Platform, monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    mocks = {alias: MagicMock() for alias in (AC_BUS, *DC_BUSES)}
    for alias, mock in mocks.items():
        monkeypatch.setattr(platform.get_element(alias=alias), "set_parameter", mock)
    return mocks


def dc_matrix() -> CrosstalkMatrix:
    return CrosstalkMatrix.from_buses(
        buses={
            "qdac_bus_1": {"qdac_bus_1": 1.0, "qdac_bus_2": 0.1},
            "qdac_bus_2": {"qdac_bus_1": 0.2, "qdac_bus_2": 1.0},
        }
    )


def ac_matrix() -> CrosstalkMatrix:
    return CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.5}})


def calibration_with(dc: CrosstalkMatrix | None = None, ac: CrosstalkMatrix | None = None) -> Calibration:
    calibration = Calibration()
    calibration.crosstalk_matrix = dc
    calibration.crosstalk_matrix_ac = ac
    return calibration


def written(mock: MagicMock) -> list[tuple[Parameter, float]]:
    return [(call.kwargs["parameter"], call.kwargs["value"]) for call in mock.call_args_list]


def assert_last_write(mock: MagicMock, parameter: Parameter, value: float):
    last_parameter, last_value = written(mock)[-1]
    assert last_parameter == parameter
    assert last_value == pytest.approx(value)


class TestMatrixChoice:
    def test_dc_only_calibration(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc = dc_matrix()
        platform.set_calibration(calibration_with(dc=dc))

        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)

        expected = dc.flux_to_bias({"qdac_bus_1": 0.2, "qdac_bus_2": 0.0})
        assert_last_write(bus_mocks["qdac_bus_1"], Parameter.VOLTAGE, expected["qdac_bus_1"])
        assert_last_write(bus_mocks["qdac_bus_2"], Parameter.VOLTAGE, expected["qdac_bus_2"])
        bus_mocks[AC_BUS].assert_not_called()
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == 0.2

    def test_ac_only_calibration(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        ac = ac_matrix()
        platform.set_calibration(calibration_with(ac=ac))

        platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.2)

        assert_last_write(bus_mocks[AC_BUS], Parameter.OFFSET_OUT0, ac.flux_to_bias({AC_BUS: 0.2})[AC_BUS])
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()

    def test_ac_and_dc_buses_only_write_their_own_matrix(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc, ac = dc_matrix(), ac_matrix()
        platform.set_calibration(calibration_with(dc=dc, ac=ac))

        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)
        for mock in bus_mocks.values():
            mock.reset_mock()

        platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.3)
        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, pytest.approx(ac.flux_to_bias({AC_BUS: 0.3})[AC_BUS]))]
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()
        for mock in bus_mocks.values():
            mock.reset_mock()

        platform.set_parameter(alias="qdac_bus_2", parameter=Parameter.FLUX, value=0.1)
        expected = dc.flux_to_bias({"qdac_bus_1": 0.2, "qdac_bus_2": 0.1})
        bus_mocks[AC_BUS].assert_not_called()
        assert written(bus_mocks["qdac_bus_1"]) == [(Parameter.VOLTAGE, pytest.approx(expected["qdac_bus_1"]))]
        assert written(bus_mocks["qdac_bus_2"]) == [(Parameter.VOLTAGE, pytest.approx(expected["qdac_bus_2"]))]

    def test_platform_crosstalk_wins_for_its_buses(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        platform_matrix = CrosstalkMatrix.from_buses(buses={"qdac_bus_1": {"qdac_bus_1": 0.25}})
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        platform.set_crosstalk(platform_matrix)

        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)

        assert written(bus_mocks["qdac_bus_1"]) == [
            (Parameter.VOLTAGE, pytest.approx(platform_matrix.flux_to_bias({"qdac_bus_1": 0.2})["qdac_bus_1"]))
        ]
        bus_mocks["qdac_bus_2"].assert_not_called()

    def test_calibration_fills_buses_missing_from_platform_crosstalk(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        dc = dc_matrix()
        platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.25}}))
        platform.set_calibration(calibration_with(dc=dc))

        platform.set_parameter(alias="qdac_bus_2", parameter=Parameter.FLUX, value=0.1)

        expected = dc.flux_to_bias({"qdac_bus_1": 0.0, "qdac_bus_2": 0.1})
        assert_last_write(bus_mocks["qdac_bus_2"], Parameter.VOLTAGE, expected["qdac_bus_2"])
        bus_mocks[AC_BUS].assert_not_called()

    def test_bus_in_both_calibration_matrices_raises(self, platform: Platform):
        ac = CrosstalkMatrix.from_buses(buses={"qdac_bus_1": {"qdac_bus_1": 0.5}})
        platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac))

        with pytest.raises(ValueError, match=r"qdac_bus_1 is inside both calibration\.crosstalk_matrix_ac and"):
            platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)

    def test_bus_in_both_calibration_matrices_uses_platform_crosstalk(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        ac = CrosstalkMatrix.from_buses(buses={"qdac_bus_1": {"qdac_bus_1": 0.5}})
        platform_matrix = CrosstalkMatrix.from_buses(buses={"qdac_bus_1": {"qdac_bus_1": 0.25}})
        platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac))
        platform.set_crosstalk(platform_matrix)

        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)

        assert_last_write(
            bus_mocks["qdac_bus_1"], Parameter.VOLTAGE, platform_matrix.flux_to_bias({"qdac_bus_1": 0.2})["qdac_bus_1"]
        )

    def test_bus_in_no_matrix_raises(self, platform: Platform):
        platform.set_calibration(calibration_with(dc=dc_matrix()))

        with pytest.raises(ValueError, match=f"{AC_BUS} not inside any crosstalk matrix"):
            platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.2)

    def test_failed_flux_set_is_not_stored(self, platform: Platform):
        platform.set_calibration(calibration_with(dc=dc_matrix()))

        with pytest.raises(ValueError, match=f"{AC_BUS} not inside any crosstalk matrix"):
            platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.3)

        assert AC_BUS not in platform.flux_parameter

    def test_calibration_without_crosstalk_raises(self, platform: Platform):
        platform.set_calibration(Calibration())

        with pytest.raises(ValueError, match="Crosstalk matrix has not been set"):
            platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)
        with pytest.raises(ValueError, match="Crosstalk matrix has not been set"):
            platform.set_flux_to_zero()
        with pytest.raises(ValueError, match="Crosstalk matrix has not been set"):
            platform.set_bias_to_zero()


class TestZeroHelpers:
    def test_set_flux_to_zero_uses_every_matrix(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac_matrix()))
        for alias in (AC_BUS, *DC_BUSES):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.2)

        platform.set_flux_to_zero()

        for alias in (AC_BUS, *DC_BUSES):
            assert platform.get_parameter(alias=alias, parameter=Parameter.FLUX) == 0.0
        assert_last_write(bus_mocks[AC_BUS], Parameter.OFFSET_OUT0, 0.0)
        for alias in DC_BUSES:
            assert_last_write(bus_mocks[alias], Parameter.VOLTAGE, 0.0)

    def test_set_flux_to_zero_with_bus_list(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac_matrix()))
        for alias in (AC_BUS, *DC_BUSES):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.2)

        platform.set_flux_to_zero(bus_list=[AC_BUS])

        assert platform.get_parameter(alias=AC_BUS, parameter=Parameter.FLUX) == 0.0
        for alias in DC_BUSES:
            assert platform.get_parameter(alias=alias, parameter=Parameter.FLUX) == 0.2

    def test_set_flux_to_zero_validates_every_bus_before_writing(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)
        for mock in bus_mocks.values():
            mock.reset_mock()

        with pytest.raises(ValueError, match=f"{AC_BUS} not inside any crosstalk matrix"):
            platform.set_flux_to_zero(bus_list=["qdac_bus_1", AC_BUS])

        for mock in bus_mocks.values():
            mock.assert_not_called()
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == 0.2

    def test_set_bias_to_zero_part_of_a_matrix_before_any_flux_set(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        platform.set_calibration(calibration_with(dc=dc_matrix()))

        platform.set_bias_to_zero(bus_list=["qdac_bus_1"])

        assert_last_write(bus_mocks["qdac_bus_1"], Parameter.VOLTAGE, 0.0)
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == pytest.approx(0.0)

    def test_set_bias_to_zero_with_ac_and_dc(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc = dc_matrix()
        dc.set_offset({"qdac_bus_1": 0.05, "qdac_bus_2": -0.03})
        platform.set_calibration(calibration_with(dc=dc, ac=ac_matrix()))
        for alias in (AC_BUS, *DC_BUSES):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.2)

        platform.set_bias_to_zero()

        assert_last_write(bus_mocks[AC_BUS], Parameter.OFFSET_OUT0, 0.0)
        for alias in DC_BUSES:
            assert_last_write(bus_mocks[alias], Parameter.VOLTAGE, 0.0)
        assert {parameter for parameter, _ in written(bus_mocks[AC_BUS])} == {Parameter.OFFSET_OUT0}
        for alias in DC_BUSES:
            assert {parameter for parameter, _ in written(bus_mocks[alias])} == {Parameter.VOLTAGE}
        assert platform.get_parameter(alias=AC_BUS, parameter=Parameter.FLUX) == pytest.approx(0.0)
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == pytest.approx(0.05)
        assert platform.get_parameter(alias="qdac_bus_2", parameter=Parameter.FLUX) == pytest.approx(-0.03)

    def test_set_bias_to_zero_with_bus_list_keeps_other_matrix(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac_matrix()))
        for alias in (AC_BUS, *DC_BUSES):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.2)
        for mock in bus_mocks.values():
            mock.reset_mock()

        platform.set_bias_to_zero(bus_list=[AC_BUS])

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, 0.0)]
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()
            assert platform.get_parameter(alias=alias, parameter=Parameter.FLUX) == 0.2


class TestWarnings:
    def test_set_crosstalk_warns_once_when_calibration_has_crosstalk(self, platform: Platform):
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        matrix = ac_matrix()

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(matrix)
            platform.set_crosstalk(matrix)

        logger.warning.assert_called_once()
        assert "calibration.crosstalk_matrix" in logger.warning.call_args.args[0]

    def test_set_crosstalk_without_calibration_crosstalk_does_not_warn(self, platform: Platform):
        platform.set_calibration(Calibration())

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(ac_matrix())

        logger.warning.assert_not_called()

    def test_set_crosstalk_with_the_calibration_matrix_does_not_warn(self, platform: Platform):
        calibration = calibration_with(dc=dc_matrix())
        platform.set_calibration(calibration)

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(calibration.crosstalk_matrix)

        logger.warning.assert_not_called()

    def test_set_calibration_warns_once_when_platform_crosstalk_is_set(self, platform: Platform):
        platform.set_crosstalk(dc_matrix())
        calibration = calibration_with(ac=ac_matrix())

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_calibration(calibration)
            platform.set_calibration(calibration)

        logger.warning.assert_called_once()
        assert "crosstalk_matrix_ac first for Qblox buses" in logger.warning.call_args.args[0]

    def test_set_calibration_warns_again_for_a_new_calibration(self, platform: Platform):
        platform.set_crosstalk(dc_matrix())
        first, second = calibration_with(dc=dc_matrix()), calibration_with(dc=dc_matrix())

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_calibration(first)
            platform.set_calibration(second)
            platform.set_calibration(second)

        assert logger.warning.call_count == 2

    def test_set_calibration_without_platform_crosstalk_does_not_warn(self, platform: Platform):
        with patch("qililab.platform.platform.logger") as logger:
            platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac_matrix()))

        logger.warning.assert_not_called()
