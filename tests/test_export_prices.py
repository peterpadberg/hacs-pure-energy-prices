"""Tests that export prices come from the redelivery price list."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


def _make_coordinator(commodity, direction):
    entry = MagicMock()
    entry.data = {"electricity": True, "solar_panels": True, "gas_element_id": 11481}
    with patch.object(PureEnergyCoordinator, "__init__", lambda self, *a, **k: None):
        coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
    coordinator._entry = entry
    coordinator._element_id = None
    coordinator._commodity = commodity
    coordinator._direction = direction
    coordinator.hass = MagicMock()
    return coordinator


async def _requested_params(coordinator):
    """Run _fetch_prices against a fake session and return the query params."""
    response = MagicMock()
    response.content_type = "application/json"
    response.read = AsyncMock(return_value=b'{"prices": []}')
    session = MagicMock()
    session.get = AsyncMock(return_value=response)
    with patch(
        "custom_components.pure_energy_prices.coordinator.async_get_clientsession",
        return_value=session,
    ):
        await coordinator._fetch_prices(datetime(2026, 10, 5, 19, 10))
    url = session.get.await_args.args[0]
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}


@pytest.mark.parametrize(
    ("commodity", "direction", "expected"),
    [
        ("electricity", "import", "electricity"),
        ("electricity", "export", "redelivery"),
        ("gas", "import", "gas"),
    ],
)
async def test_api_commodity_per_direction(commodity, direction, expected):
    coordinator = _make_coordinator(commodity, direction)
    params = await _requested_params(coordinator)
    assert params["commodity"] == expected


async def test_export_uses_electricity_element_id():
    coordinator = _make_coordinator("electricity", "export")
    params = await _requested_params(coordinator)
    assert params["element_id"] == "11480"
