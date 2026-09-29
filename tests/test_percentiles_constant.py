"""Tests for CONF_PERCENTILES constant usage."""
import pytest


class TestPercentilesConstant:
    """Verify CONF_PERCENTILES is used instead of hardcoded 'percentiles' string."""

    def test_conf_percentiles_exists(self):
        """CONF_PERCENTILES should be defined in const.py."""
        from custom_components.pure_energy_prices.const import CONF_PERCENTILES
        assert CONF_PERCENTILES == "percentiles"

    def test_sensor_uses_conf_percentiles(self):
        """sensor.py should import and use CONF_PERCENTILES."""
        source = open(
            "custom_components/pure_energy_prices/sensor.py"
        ).read()

        # CONF_PERCENTILES should be imported from const.py
        assert "CONF_PERCENTILES" in source, (
            "CONF_PERCENTILES is not imported/used in sensor.py"
        )

        # The hardcoded string "percentiles" should not be used as a dict key
        assert ".get(\"percentiles\"" not in source, (
            "Hardcoded 'percentiles' string still used as dict key in sensor.py"
        )

        # Verify it uses the constant in the .get() call
        assert ".get(CONF_PERCENTILES" in source, (
            "sensor.py should use .get(CONF_PERCENTILES, ...) not .get(\"percentiles\", ...)"
        )

    def test_percentiles_constant_in_const_py(self):
        """CONF_PERCENTILES should exist in const.py."""
        source = open(
            "custom_components/pure_energy_prices/const.py"
        ).read()

        assert "CONF_PERCENTILES = " in source or "CONF_PERCENTILES =" in source, (
            "CONF_PERCENTILES is not defined in const.py"
        )
