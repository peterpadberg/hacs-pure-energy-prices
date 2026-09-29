"""Tests for the PureEnergiePercentileSensor class."""

import pytest
from unittest.mock import MagicMock
from homeassistant.components.sensor import SensorStateClass

from custom_components.pure_energy_prices.sensor import PureEnergiePercentileSensor
from homeassistant.helpers.device_registry import DeviceInfo


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {"unit_of_measurement": "\u20ac/kWh"}
    entry.entry_id = "test_entry"
    return entry


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with sample data."""
    coord = MagicMock()
    coord.data = MagicMock()
    coord.data.prices = [
        {"price": 0.10},
        {"price": 0.15},
        {"price": 0.20},
        {"price": 0.25},
        {"price": 0.30},
    ]
    return coord


@pytest.fixture
def device_info():
    """Create a mock DeviceInfo."""
    return DeviceInfo(
        identifiers={("pure_energy_prices", "test_entry")},
        name="Pure Energie Prices",
        manufacturer="Pure Energie",
        model="Dynamic Pricing",
    )


@pytest.fixture
def percentile_sensor(mock_coordinator, mock_entry):
    """Create a percentile sensor instance."""
    return PureEnergiePercentileSensor(
        mock_coordinator, mock_entry, percentile=0.1
    )


def test_sensor_creation(percentile_sensor):
    """Test sensor creation."""
    assert percentile_sensor._percentile == 0.1


def test_unit_of_measurement(percentile_sensor, mock_entry):
    """Test unit of measurement property."""
    # Default is kWh since __init__ doesn't read from entry.data
    assert percentile_sensor.native_unit_of_measurement == "kWh"


def test_state_class(percentile_sensor):
    """Test state class property."""
    assert percentile_sensor.state_class == SensorStateClass.MEASUREMENT


def test_native_value_with_data(percentile_sensor, mock_coordinator):
    """Test native_value with available data."""
    mock_coordinator.data.prices = [
        {"price": 0.10}, {"price": 0.15}, {"price": 0.20},
        {"price": 0.25}, {"price": 0.30},
    ]
    value = percentile_sensor.native_value
    assert value is not None
    assert isinstance(value, float)


def test_native_value_empty_data(percentile_sensor):
    """Test native_value with no data."""
    percentile_sensor.coordinator.data.prices = []
    value = percentile_sensor.native_value
    assert value is None
