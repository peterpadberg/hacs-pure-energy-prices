"""Tests for config flow default values — verify correct fallbacks."""

import re

from custom_components.pure_energy_prices.const import (
    CONF_RETURN_COSTS,
    DEFAULT_RETURN_COSTS,
    DEFAULT_ADDED_COSTS,
    CONF_ADDED_COSTS,
    DOMAIN,
    DEFAULT_DOUBLE_METER,
    CONF_DOUBLE_METER,
    DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SOLAR_PANELS,
    CONF_SOLAR_PANELS,
    DEFAULT_GAS_ELEMENT_ID,
    CONF_GAS_ELEMENT_ID,
)


class TestConfigFlowDefaults:
    """Verify correct default fallbacks in config_flow.py."""

    def _read_source(self):
        """Read config_flow.py source."""
        return open(
            "custom_components/pure_energy_prices/config_flow.py"
        ).read()

    def test_return_costs_uses_default_return_costs(self):
        """CONF_RETURN_COSTS should fall back to DEFAULT_RETURN_COSTS."""
        source = self._read_source()
        user_section_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_section_start:options_start]

        match = re.search(
            r'return_costs.*?DEFAULT_(\w+)',
            user_section,
            re.DOTALL,
        )
        assert match is not None, "return_costs default not found in coordinator.py"
        fallback_name = match.group(1)
        assert fallback_name == "RETURN_COSTS", (
            f"return_costs falls back to DEFAULT_{fallback_name}, "
            f"but should fall back to DEFAULT_RETURN_COSTS"
        )

    def test_added_costs_uses_default_added_costs(self):
        """Coordinator should use DEFAULT_ADDED_COSTS for added_costs."""
        source = self._read_source()
        match = re.search(
            r'added_costs.*?DEFAULT_(\w+)',
            source,
            re.DOTALL,
        )
        assert match is not None
        fallback_name = match.group(1)
        assert fallback_name == "ADDED_COSTS"

    def test_double_meter_fallback(self):
        """CONF_DOUBLE_METER should fall back to DEFAULT_DOUBLE_METER."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_step_start:options_start]

        match = re.search(
            r"CONF_DOUBLE_METER.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert match is not None
        fallback_name = match.group(1)
        assert fallback_name == "DOUBLE_METER"

    def test_scan_interval_fallback(self):
        """CONF_SCAN_INTERVAL should fall back to DEFAULT_SCAN_INTERVAL."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_step_start:options_start]

        match = re.search(
            r"CONF_SCAN_INTERVAL.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert match is not None
        fallback_name = match.group(1)
        assert fallback_name == "SCAN_INTERVAL"

    def test_gas_element_fallback(self):
        """CONF_GAS_ELEMENT_ID should fall back to DEFAULT_GAS_ELEMENT_ID."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_step_start:options_start]

        match = re.search(
            r"CONF_GAS_ELEMENT_ID.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert match is not None
        fallback_name = match.group(1)
        assert fallback_name == "GAS_ELEMENT_ID"

    def test_solar_panels_fallback(self):
        """CONF_SOLAR_PANELS should fall back to DEFAULT_SOLAR_PANELS."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_step_start:options_start]

        match = re.search(
            r"CONF_SOLAR_PANELS.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert match is not None
        fallback_name = match.group(1)
        assert fallback_name == "SOLAR_PANELS"

    def test_coordinator_return_costs_default(self):
        """Coordinator should use DEFAULT_RETURN_COSTS, not DEFAULT_ADDED_COSTS."""
        source = open("custom_components/pure_energy_prices/coordinator.py").read()
        match = re.search(
            r'return_costs.*?DEFAULT_(\w+)',
            source,
            re.DOTALL,
        )
        assert match is not None, "return_costs default not found in coordinator.py"
        fallback_name = match.group(1)
        assert fallback_name == "RETURN_COSTS", (
            f"return_costs falls back to DEFAULT_{fallback_name}, "
            f"but should fall back to DEFAULT_RETURN_COSTS"
        )

    def test_coordinator_added_costs_default(self):
        """Coordinator should use DEFAULT_ADDED_COSTS for added_costs."""
        source = open("custom_components/pure_energy_prices/coordinator.py").read()
        match = re.search(
            r'added_costs.*?DEFAULT_(\w+)',
            source,
            re.DOTALL,
        )
        assert match is not None
        fallback_name = match.group(1)
        assert fallback_name == "ADDED_COSTS"
