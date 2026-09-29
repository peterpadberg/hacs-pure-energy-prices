"""Tests for PureEnergiePriceSensor — sensor.py issues from branch review."""
import pytest
from unittest.mock import MagicMock
from homeassistant.components.sensor import SensorStateClass


class TestPureEnergiePriceSensorInit:
    """Test that PureEnergiePriceSensor can be instantiated with minimal args."""

    def test_init_accepts_two_args(self):
        """PureEnergiePriceSensor should work with just (coordinator, config_entry)."""
        # We test this by attempting to instantiate the class
        # with two args — if it raises TypeError, the test fails.
        from custom_components.pure_energy_prices.sensor import (
            PureEnergiePriceSensor,
        )

        coordinator = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_123"

        # This should NOT raise TypeError
        sensor = PureEnergiePriceSensor(coordinator, entry)
        assert sensor.coordinator is coordinator
        assert sensor.config_entry is entry

    def test_state_class_is_measurement(self):
        """Price sensors report point-in-time measurements, not running totals."""
        from custom_components.pure_energy_prices.sensor import (
            PureEnergiePriceSensor,
        )

        coordinator = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_123"

        sensor = PureEnergiePriceSensor(coordinator, entry)
        assert sensor.state_class is SensorStateClass.MEASUREMENT
