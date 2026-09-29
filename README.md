# Pure Energie Prices

Home Assistant integration for Pure Energie dynamic electricity and gas prices.

## Features

- **Multi-commodity support**: Electricity, gas, and redelivery
- **Per-entry multi-sensor**: Each config entry can create multiple sensor entities (import/export)
- **Percentile sensors**: Pre-calculated percentile prices from forecasted data
- **Price direction awareness**: Import adds costs, export subtracts return costs
- **Reconfiguration support**: Update options without reinstalling

## Configuration

### Setup

Add the integration through the Home Assistant UI. On first setup you configure:

- **API key**: Your Pure Energie API credentials
- **Double meter**: Enable split meter reading
- **Solar panels**: Enable solar panel integration

### Options

After setup, access options via the config entry options panel:

- **Horizon hours**: Forecast window (1-168 hours, default: 48)
- **Scan interval**: Update frequency in seconds (60-86400, default: 3600)
- **Added costs**: Costs to add to import prices
- **Return costs**: Costs to subtract from export prices
- **Solar panels toggle**: Enable/disable solar panel sensors
- **Percentile sensors**: Configure which percentile prices to display

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `base_url` | string | `https://api.pure-energie.com/energy-prices` | API base URL |
| `element_id` | int | 11480 | Main element identifier |
| `added_costs` | float | 0.0 | Additional costs for import |
| `business` | bool | False | Business mode flag |
| `electricity` | bool | True | Enable electricity sensors |
| `gas` | bool | False | Enable gas sensors |
| `redelivery` | bool | False | Enable redelivery sensors |
| `double_meter` | bool | True | Use double meter reading |
| `gas_element_id` | string | `gas_element_id` | Gas element identifier |
| `horizon_hours` | int | 48 | Forecast horizon in hours |
| `return_costs` | float | 0.0 | Return costs for export |
| `scan_interval` | int | 3600 | Update interval in seconds |
| `solar_panels` | bool | False | Enable solar panel sensors |
| `percentiles` | string | `0.05,0.1,0.2,0.4` | Percentile thresholds |

## Entities

### Electricity Sensors

Each config entry creates:

- **Electricity Import**: Current import price sensor
- **Electricity Export**: Export price sensor (when solar panels enabled)
- **Percentile Sensors**: Multiple percentile price sensors per direction

### Sensor Properties

| Property | Description |
|----------|-------------|
| Unique ID | `{config_entry.entry_id}_{commodity}_{direction}` |
| Name | `Pure Energie {Commodity}` |
| Unit | `€/kWh` (electricity), `€/m³` (gas) |
| State Class | `MEASUREMENT` |

## API Interaction

The integration fetches prices from the Pure Energie API using:

- `double_meter`: true/false
- `solar_panels`: true/false
- `commodity`: electricity, gas, or redelivery
- `current`: Current timestamp
- `business`: true/false
- `element_id`: Element identifier

## Error Handling

- Empty API responses handled gracefully
- JSON parse failures check for HTML-wrapped responses
- API errors logged; integration continues with stale data
- Setup continues even if initial API call fails

## Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_percentiles_constant.py -v
```

Test coverage includes:
- Sensor creation and configuration
- Unit of measurement properties
- State class validation
- Percentile constant usage
- Price adjustment by direction (import adds costs, export subtracts)
- Configuration defaults
- Version pin correctness

## Development

### Project Structure

```
pure-energie-prices/
├── custom_components/
│   └── pure_energy_prices/
│       ├── __init__.py          # Integration setup
│       ├── sensor.py            # Sensor entities
│       ├── coordinator.py       # Data fetcher
│       ├── config_flow.py       # Configuration flow
│       ├── const.py             # Constants
│       ├── manifest.json        # Integration metadata
│       └── brand/               # Brand assets
├── docs                         # Documentation
├── tests/
│   ├── conftest.py              # Test fixtures
│   └── test_*.py                # Test files
├── hacs.json                    # HACS configuration
├── pytest.ini                   # Pytest configuration
└── requirements.txt             # Dependencies
```

### Dependencies

- aiohttp
- voluptuous
- homeassistant
- astral

## License

[License information should be added]

## Support

For issues and feature requests, please use the [GitHub Issue Tracker](https://github.com/venraij/hacs-pure-energy-prices/issues).
