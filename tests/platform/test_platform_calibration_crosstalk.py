"""Tests for the static flux helpers using the crosstalk matrices in ``platform.calibration``."""

import re
from unittest.mock import MagicMock, patch

import pytest

from qililab.data_management import build_platform
from qililab.platform import Platform
from qililab.qprogram import Calibration, CrosstalkMatrix
from qililab.typings.enums import Parameter

AC_BUS = "drive"
DC_BUSES = ("qdac_bus_1", "qdac_bus_2")
NOT_SET = "Crosstalk matrix has not been set"


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


def not_inside(alias: str, matrix: CrosstalkMatrix) -> str:
    return re.escape(f"{alias} not inside crosstalk matrix\n{matrix}")


def written(mock: MagicMock) -> list[tuple[Parameter, float]]:
    return [(call.kwargs["parameter"], call.kwargs["value"]) for call in mock.call_args_list]


def assert_last_write(mock: MagicMock, parameter: Parameter, value: float):
    last_parameter, last_value = written(mock)[-1]
    assert last_parameter == parameter
    assert last_value == pytest.approx(value)


def reset(mocks: dict[str, MagicMock]):
    for mock in mocks.values():
        mock.reset_mock()


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

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, pytest.approx(ac.flux_to_bias({AC_BUS: 0.2})[AC_BUS]))]
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()

    def test_ac_and_dc_buses_only_write_their_own_matrix(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc, ac = dc_matrix(), ac_matrix()
        platform.set_calibration(calibration_with(dc=dc, ac=ac))

        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)
        reset(bus_mocks)

        platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.3)
        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, pytest.approx(ac.flux_to_bias({AC_BUS: 0.3})[AC_BUS]))]
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()
        reset(bus_mocks)

        platform.set_parameter(alias="qdac_bus_2", parameter=Parameter.FLUX, value=0.1)
        expected = dc.flux_to_bias({"qdac_bus_1": 0.2, "qdac_bus_2": 0.1})
        bus_mocks[AC_BUS].assert_not_called()
        assert written(bus_mocks["qdac_bus_1"]) == [(Parameter.VOLTAGE, pytest.approx(expected["qdac_bus_1"]))]
        assert written(bus_mocks["qdac_bus_2"]) == [(Parameter.VOLTAGE, pytest.approx(expected["qdac_bus_2"]))]

    def test_qblox_bus_uses_dc_matrix_without_ac_matrix(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc = CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.4}})
        platform.set_calibration(calibration_with(dc=dc))

        platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.2)

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, pytest.approx(dc.flux_to_bias({AC_BUS: 0.2})[AC_BUS]))]

    def test_platform_crosstalk_replaces_dc_matrix(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        platform_matrix = CrosstalkMatrix.from_buses(
            buses={
                "qdac_bus_1": {"qdac_bus_1": 0.5, "qdac_bus_2": 0.3},
                "qdac_bus_2": {"qdac_bus_1": 0.3, "qdac_bus_2": 0.5},
            }
        )
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        platform.set_crosstalk(platform_matrix)

        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)

        expected = platform_matrix.flux_to_bias({"qdac_bus_1": 0.2, "qdac_bus_2": 0.0})
        assert written(bus_mocks["qdac_bus_1"]) == [(Parameter.VOLTAGE, pytest.approx(expected["qdac_bus_1"]))]
        assert written(bus_mocks["qdac_bus_2"]) == [(Parameter.VOLTAGE, pytest.approx(expected["qdac_bus_2"]))]

    def test_qblox_platform_crosstalk_replaces_dc_matrix_for_qdac_buses(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        platform_matrix = CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.25}})
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        platform.set_crosstalk(platform_matrix)

        with pytest.raises(ValueError, match=not_inside("qdac_bus_1", platform_matrix)):
            platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.1)

        for mock in bus_mocks.values():
            mock.assert_not_called()

    def test_ac_matrix_replaces_platform_crosstalk_on_qblox_buses(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        ac = ac_matrix()
        platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.25}}))
        platform.set_calibration(calibration_with(ac=ac))

        platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.2)

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, pytest.approx(ac.flux_to_bias({AC_BUS: 0.2})[AC_BUS]))]

    def test_bus_not_in_chosen_matrix_raises(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc = dc_matrix()
        platform.set_calibration(calibration_with(dc=dc))

        with pytest.raises(ValueError, match=not_inside(AC_BUS, dc)):
            platform.set_parameter(alias=AC_BUS, parameter=Parameter.FLUX, value=0.3)

        assert AC_BUS not in platform.flux_parameter
        bus_mocks[AC_BUS].assert_not_called()

    def test_failed_write_keeps_stored_flux_in_sync(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc = dc_matrix()
        platform.set_calibration(calibration_with(dc=dc))
        bus_mocks["qdac_bus_1"].side_effect = [RuntimeError("write failed"), None, None]

        with pytest.raises(RuntimeError, match="write failed"):
            platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.4)
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == 0.4

        platform.set_parameter(alias="qdac_bus_2", parameter=Parameter.FLUX, value=0.1)

        expected = dc.flux_to_bias({"qdac_bus_1": 0.4, "qdac_bus_2": 0.1})
        assert_last_write(bus_mocks["qdac_bus_1"], Parameter.VOLTAGE, expected["qdac_bus_1"])
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == 0.4

    def test_calibration_without_crosstalk_raises(self, platform: Platform):
        platform.set_calibration(Calibration())

        with pytest.raises(ValueError, match=f"^{NOT_SET}$"):
            platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)
        with pytest.raises(ValueError, match=f"^{NOT_SET}$"):
            platform.set_flux_to_zero()
        with pytest.raises(ValueError, match=f"^{NOT_SET}$"):
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

    def test_set_flux_to_zero_default_skips_replaced_matrix(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.25}}))

        platform.set_flux_to_zero()

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, 0.0)]
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()

    def test_set_flux_to_zero_validates_every_bus_before_writing(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        dc = dc_matrix()
        platform.set_calibration(calibration_with(dc=dc))
        platform.set_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX, value=0.2)
        reset(bus_mocks)

        with pytest.raises(ValueError, match=not_inside(AC_BUS, dc)):
            platform.set_flux_to_zero(bus_list=["qdac_bus_1", AC_BUS])

        for mock in bus_mocks.values():
            mock.assert_not_called()
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == 0.2

    def test_set_bias_to_zero_with_ac_and_dc(self, platform: Platform, bus_mocks: dict[str, MagicMock]):
        dc = dc_matrix()
        dc.set_offset({"qdac_bus_1": 0.05, "qdac_bus_2": -0.03})
        platform.set_calibration(calibration_with(dc=dc, ac=ac_matrix()))
        for alias in (AC_BUS, *DC_BUSES):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.2)
        reset(bus_mocks)

        platform.set_bias_to_zero()

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, 0.0)]
        for alias in DC_BUSES:
            assert written(bus_mocks[alias]) == [(Parameter.VOLTAGE, 0.0)]
        assert platform.get_parameter(alias=AC_BUS, parameter=Parameter.FLUX) == pytest.approx(0.0)
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == pytest.approx(0.05)
        assert platform.get_parameter(alias="qdac_bus_2", parameter=Parameter.FLUX) == pytest.approx(-0.03)

    def test_set_bias_to_zero_part_of_a_matrix_before_any_flux_set(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        platform.set_calibration(calibration_with(dc=dc_matrix()))

        platform.set_bias_to_zero(bus_list=["qdac_bus_1"])

        assert_last_write(bus_mocks["qdac_bus_1"], Parameter.VOLTAGE, 0.0)
        assert platform.get_parameter(alias="qdac_bus_1", parameter=Parameter.FLUX) == pytest.approx(0.0)

    def test_set_bias_to_zero_with_bus_list_keeps_other_matrix(
        self, platform: Platform, bus_mocks: dict[str, MagicMock]
    ):
        platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac_matrix()))
        for alias in (AC_BUS, *DC_BUSES):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.2)
        reset(bus_mocks)

        platform.set_bias_to_zero(bus_list=[AC_BUS])

        assert written(bus_mocks[AC_BUS]) == [(Parameter.OFFSET_OUT0, 0.0)]
        for alias in DC_BUSES:
            bus_mocks[alias].assert_not_called()
            assert platform.get_parameter(alias=alias, parameter=Parameter.FLUX) == 0.2


class TestPartialOverlap:
    @pytest.mark.parametrize(
        ("platform_buses", "shared"),
        [(("qdac_bus_1",), "qdac_bus_1"), (("qdac_bus_1", "qdac_bus_2", AC_BUS), "qdac_bus_1, qdac_bus_2")],
    )
    def test_set_crosstalk_raises_on_partial_overlap_with_dc_matrix(
        self, platform: Platform, platform_buses: tuple[str, ...], shared: str
    ):
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        matrix = CrosstalkMatrix.from_buses(buses={a: {b: 1.0 if a == b else 0.1 for b in platform_buses} for a in platform_buses})

        with pytest.raises(
            ValueError,
            match=re.escape(
                f"platform.crosstalk and calibration.crosstalk_matrix share {shared} but not all their buses. "
                "Give both matrices the same buses, or no common buses."
            ),
        ):
            platform.set_crosstalk(matrix)

        assert platform.crosstalk is None

    def test_set_calibration_raises_on_partial_overlap_with_ac_matrix(self, platform: Platform):
        platform.set_crosstalk(
            CrosstalkMatrix.from_buses(
                buses={"qdac_bus_1": {"qdac_bus_1": 1.0, AC_BUS: 0.1}, AC_BUS: {"qdac_bus_1": 0.1, AC_BUS: 1.0}}
            )
        )

        calibration = calibration_with(ac=ac_matrix())
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"platform.crosstalk and calibration.crosstalk_matrix_ac share {AC_BUS} but not all their buses. "
                "Give both matrices the same buses, or no common buses."
            ),
        ):
            platform.set_calibration(calibration)

        assert platform.calibration is None

    def test_disjoint_matrices_are_accepted(self, platform: Platform):
        platform.set_crosstalk(dc_matrix())
        calibration = calibration_with(ac=ac_matrix())

        platform.set_calibration(calibration)

        assert platform.calibration is calibration


class TestWarnings:
    REPLACES_DC = "Both platform.crosstalk and platform.calibration hold crosstalk: platform.crosstalk replaces calibration.crosstalk_matrix."
    REPLACES_PLATFORM = (
        "Both platform.crosstalk and platform.calibration hold crosstalk: "
        "calibration.crosstalk_matrix_ac replaces platform.crosstalk on Qblox buses."
    )

    def test_set_crosstalk_warns_when_it_replaces_the_dc_matrix(self, platform: Platform):
        platform.set_calibration(calibration_with(dc=dc_matrix()))
        matrix = dc_matrix()

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(matrix)
            platform.set_crosstalk(matrix)

        logger.warning.assert_called_once_with(self.REPLACES_DC)

    def test_set_crosstalk_warns_when_the_ac_matrix_replaces_it(self, platform: Platform):
        platform.set_calibration(calibration_with(ac=ac_matrix()))

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={AC_BUS: {AC_BUS: 0.25}}))

        logger.warning.assert_called_once_with(self.REPLACES_PLATFORM)

    def test_set_crosstalk_with_the_calibration_dc_matrix_does_not_warn(self, platform: Platform):
        calibration = calibration_with(dc=dc_matrix(), ac=ac_matrix())
        platform.set_calibration(calibration)

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(calibration.crosstalk_matrix)

        logger.warning.assert_not_called()

    def test_set_crosstalk_without_calibration_crosstalk_does_not_warn(self, platform: Platform):
        platform.set_calibration(Calibration())

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_crosstalk(ac_matrix())

        logger.warning.assert_not_called()

    def test_set_calibration_warns_for_each_new_calibration(self, platform: Platform):
        platform.set_crosstalk(dc_matrix())
        first, second = calibration_with(dc=dc_matrix()), calibration_with(dc=dc_matrix())

        with patch("qililab.platform.platform.logger") as logger:
            platform.set_calibration(first)
            platform.set_calibration(first)
            platform.set_calibration(second)

        assert logger.warning.call_args_list == [((self.REPLACES_DC,),), ((self.REPLACES_DC,),)]

    def test_set_calibration_without_platform_crosstalk_does_not_warn(self, platform: Platform):
        with patch("qililab.platform.platform.logger") as logger:
            platform.set_calibration(calibration_with(dc=dc_matrix(), ac=ac_matrix()))

        logger.warning.assert_not_called()
