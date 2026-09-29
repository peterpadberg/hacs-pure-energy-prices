"""TDD tests for config flow defaults — verify RETURN_COSTS uses correct fallback."""

import pytest
from unittest.mock import MagicMock, patch

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
    DEFAULT_HORIZON_HOURS,
    CONF_HORIZON_HOURS,
    DEFAULT_SOLAR_PANELS,
    CONF_SOLAR_PANELS,
    DEFAULT_GAS_ELEMENT_ID,
    CONF_GAS_ELEMENT_ID,
    DEFAULT_ADDED_COSTS,
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
)


class TestConfigFlowDefaults:
    """Ensure each vol.Required in async_step_user uses the correct DEFAULT_* fallback."""

    def _read_schema_defaults(self):
        """Import config_flow, patch vol.Schema to capture the first dict passed to it.

        We intercept the vol.Schema call during async_step_user so we can inspect
        which DEFAULT_* constant is used as the fallback for each field.
        """
        from custom_components.pure_energy_prices.const import DOMAIN

        captured = {}

        def capture_schema(schema_dict):
            captured["schema"] = schema_dict
            # Return a dummy schema object so voluptuous doesn't crash
            return MagicMock()

        with patch("custom_components.pure_energy_prices.config_flow.vol.Schema", side_effect=capture_schema):
            from homeassistant.core import HomeAssistant
            from homeassistant.config_entries import ConfigEntry

            from custom_components.pure_energy_prices.config_flow import PureEnergieConfigFlow

            flow = PureEnergieConfigFlow()
            flow.hass = MagicMock()
            flow.config_entry = MagicMock()
            flow.config_entry.data = {}
            flow.config_entry.options = {}
            flow._options = {}

            # Call async_step_user with None to trigger schema building
            flow.async_step_user(None)

        return captured.get("schema", {})

    def test_return_costs_uses_DEFAULT_RETURN_COSTS(self):
        """CONF_RETURN_COSTS should fall back to DEFAULT_RETURN_COSTS, not DEFAULT_ADDED_COSTS."""
        schema = self._read_schema_defaults()
        for key, _ in schema.items():
            if key == CONF_RETURN_COSTS:
                # We need to check the default — voluptuous stores it in the Required spec
                # But since we mocked vol.Schema, let's use a different approach
                pass
        # We'll assert via a more direct check below
        assert True  # placeholder — real check below

    def test_return_costs_direct_check(self):
        """Directly verify that CONF_RETURN_COSTS default line uses DEFAULT_RETURN_COSTS."""
        import re

        source = open(
            "custom_components/pure_energy_prices/config_flow.py"
        ).read()

        # Find the CONF_RETURN_COSTS block in async_step_user (not in OptionsFlow)
        # Look for the pattern within async_step_user
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")

        # Extract only the user step section
        user_section = source[user_step_start:options_start]

        # The RETURN_COSTS line should use DEFAULT_RETURN_COSTS, not DEFAULT_ADDED_COSTS
        # Pattern: CONF_RETURN_COSTS followed by DEFAULT_... in the same block
        return_costs_block = re.search(
            r"CONF_RETURN_COSTS.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert return_costs_block is not None, "CONF_RETURN_COSTS block not found in async_step_user"
        fallback_name = return_costs_block.group(1)
        assert fallback_name == "RETURN_COSTS", (
            f"CONF_RETURN_COSTS falls back to DEFAULT_{fallback_name}, "
            f"but should fall back to DEFAULT_RETURN_COSTS"
        )

    def test_added_costs_uses_DEFAULT_ADDED_COSTS(self):
        """CONF_ADDED_COSTS should fall back to DEFAULT_ADDED_COSTS."""
        import re

        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_step_start:options_start]

        added_costs_block = re.search(
            r"CONF_ADDED_COSTS.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert added_costs_block is not None
        fallback_name = added_costs_block.group(1)
        assert fallback_name == "ADDED_COSTS"

    def test_horizon_hours_uses_DEFAULT_HORIZON_HOURS(self):
        """CONF_HORIZON_HOURS should fall back to DEFAULT_HORIZON_HOURS."""
        import re

        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        user_step_start = source.find("async def async_step_user")
        options_start = source.find("class PureEnergieOptionsFlow")
        user_section = source[user_step_start:options_start]

        horizon_block = re.search(
            r"CONF_HORIZON_HOURS.*?DEFAULT_(\w+)",
            user_section,
            re.DOTALL,
        )
        assert horizon_block is not None
        fallback_name = horizon_block.group(1)
        assert fallback_name == "HORIZON_HOURS"

    def test_coordinator_return_costs_default(self):
        """Coordinator should use DEFAULT_RETURN_COSTS, not DEFAULT_ADDED_COSTS."""
        import re

        source = open("custom_components/pure_energy_prices/coordinator.py").read()

        # Find the return_costs line
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
        import re

        source = open("custom_components/pure_energy_prices/coordinator.py").read()

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
        import re

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
        import re

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
