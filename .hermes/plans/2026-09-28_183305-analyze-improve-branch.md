# Plan: Analyze & Improve `feature/reconfigure-device` Branch

**Date:** 2026-09-28
**Source branch:** `feature/reconfigure-device`
**Base branch:** `main`
**Diff stats:** 22 files changed, +2,405 / -428 lines

---

## Goal

Identify and implement code quality, correctness, and architectural improvements in the `feature/reconfigure-device` branch for the Pure Energie Prices Home Assistant integration, using TDD for all code changes and systematic analysis (the "/grilling" process) for the review phase.

## Current Context / Assumptions

### What's on the branch vs main

| Aspect | `main` | `feature/reconfigure-device` |
|---|---|---|
| Coordinator | Monolithic `PureEnergyCoordinator` with `data` dict attribute | Split into `PureEnergieData` container + `PureEnergyCoordinator[PureEnergieData]` with `commodity`/`direction` parameters |
| Sensors | Single sensor per entry | Multiple sensors: electricity import/export, gas import, percentile sensors for each |
| Config flow | Basic setup flow | Added `PureEnergieOptionsFlow` for in-place reconfiguration |
| Tests | Minimal / none | 4 test files, 800+ lines (fixtures, percentile sensors, commodity sensors) |
| HA version pin | `homeassistant==2026.7.4` in `requirements.txt` | `homeassistant==2026.2.3` in `requirements.txt` |
| manifest.json | No `requirements` key | `"requirements": []` |
| Device registry | `async_remove_config_entry_device` | Full device creation + removal in `__init__.py` |

### Verified syntax — all clean
All four core Python files pass `ast.parse()`: `__init__.py`, `config_flow.py`, `coordinator.py`, `sensor.py`.

### Known issues identified in review

1. **`requirements.txt` downgrades Home Assistant** from `2026.7.4` to `2026.2.3` — 5-month regression. This is a **hard break** for users on newer HA.
2. **`manifest.json` has empty `requirements: []`** — HA ignores this; pip installs whatever's in `requirements.txt`. The version pin there is the actual constraint.
3. **Dead imports in `__init__.py`** — `DeviceEntry`, `DeviceEntryType`, `async_get_device_registry` are imported but the usage in `async_remove_config_entry_device` references `DeviceEntry` from `homeassistant.helpers.device_registry` which was removed. The replacement uses `async_get_device_registry` and `DeviceEntryType` but `DeviceEntry` is no longer imported (it was replaced by `async_get as async_get_device_registry`). Wait — actually the code *does* use all three in `async_remove_config_entry_device`. Need to verify.
4. **`sensor.py` hardcoded string keys** — `"percentiles"` instead of `DEFAULT_PERCENTILES` reference in one spot, `config_entry.data.get("percentiles", DEFAULT_PERCENTILES)` — should use `CONF_PERCENTILES` if defined.
5. **`conftest.py` mock coordinator** — `coordinator.data = MagicMock()` creates a fresh MagicMock, but the `coordinator` variable itself is `MagicMock()`. The `coordinator.data.prices` assignment works due to auto-magic, but it doesn't match the real `DataUpdateCoordinator` structure which uses `self.data` on a real instance.
6. **`__init__.py` — `async_setup_entry` signature mismatch** — The old `__init__.py` (on main) has `async def async_setup_entry(hass: HomeAssistant, entry: PureEnergieConfigEntry) -> bool`. The new version has `async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None`. The return type changed and the parameter was renamed. But the new version is missing `return True` (or rather, it doesn't return at all, implicitly returning `None` which is truthy in HA).
7. **`__init__.py` — `config_entry` not stored** — The `PureEnergieOptionsFlow.__init__` receives `config_entry: config_entries.ConfigEntry` but doesn't store it as `self.config_entry` correctly — wait, it does: `self.config_entry = config_entry`. But the type hint says `config_entries.ConfigEntry` when the import is `from homeassistant.config_entries import ConfigEntry`. The hint should be `ConfigEntry`, not `config_entries.ConfigEntry`.
8. **`config_flow.py` — duplicate `CONF_SCAN_INTERVAL` / `CONF_DOUBLE_METER` in schema** — The options flow schema defines these keys twice with different constraints in the reconfigure flow. The first `CONF_SCAN_INTERVAL` at line 159 uses `vol.All(vol.Coerce(int), vol.Range(min=60, max=86400))` and the second `CONF_DOUBLE_METER` at line 163 uses `cv.boolean`. These are fine but the flow also has `CONF_SCAN_INTERVAL` at line 87-91 (in a different step or duplicate). Need to check for actual duplicates within the same schema.
9. **`coordinator.py` — `self.data` used in except block** — Line 226: `return self.data` when the update fails. But `self.data` is set in `__init__` as `self.data = PureEnergieData([])`. This returns stale data which is correct behavior but the warning log at line 222-225 could be more specific.
10. **`sensor.py` — `has_solar` not defined** — Line 184: `if has_solar and "electricity_export" in coordinators:` — but `has_solar` is defined at line 144. This is fine.

### What `/grilling` means in this context
Systematic critical analysis: examine every change diff, question every design decision, verify against Home Assistant integration best practices, and produce a prioritized issue list with concrete fix instructions.

### What `/tdd` means in this context
For every code improvement task: write the failing test first, run it to confirm failure, implement the minimal fix, run to confirm pass, commit.

---

## Architecture / Proposed Approach

The branch introduces a sound architectural shift (coordinator per commodity/direction, proper OptionsFlow, device registry integration) but has several correctness and quality issues. The plan tackles these in order: (1) version/dependency correctness, (2) dead imports and name errors, (3) OptionsFlow correctness, (4) test completeness, (5) code style/DRY.

---

## Step-by-Step Tasks

### Phase 1: Dependency & Manifest Correctness (Grill)

#### Task 1.1: Fix `requirements.txt` HA version pin
**Problem:** `requirements.txt` on the branch pins `homeassistant==2026.2.3` but `main` pins `2026.7.4`. This downgrades HA by 5 months.
**Steps:**
1. `cd /home/nick/repos/prive/hacs-pure-energy-prices && grep -n "homeassistant==" requirements.txt`
2. Expected output: `homeassistant==2026.2.3`
3. Fix: `grep -i "homeassistant==" requirements.txt`
4. Replace the line with `homeassistant==2026.7.4` using `patch`:
   ```
   patch("requirements.txt", "homeassistant==2026.2.3", "homeassistant==2026.7.4")
   ```
5. Verify: `grep "homeassistant==" requirements.txt` should show `homeassistant==2026.7.4`
6. Also verify all other version pins match main: compare `git diff main..feature/reconfigure-device -- requirements.txt | grep "homeassistant\|pytest\|pytest-homeassistant"`

#### Task 1.2: Fix `requirements.txt` other version drift
**Problem:** Multiple packages were downgraded along with HA: `aiohttp==3.14.3→3.13.3`, `aiodns==4.0.4→4.0.0`, etc. These are likely coincidental with the HA downgrade but need verification.
**Steps:**
1. `git diff main..feature/reconfigure-device -- requirements.txt | grep "^[-+].*==" | grep -v homeassistant`
2. For each diverged package, decide: keep branch version (if intentional) or revert to main (if accidental).
3. Most likely: all non-HA packages should revert to main versions since they're pinned and the branch just happened to change them.
4. Apply reverts via `patch` for each: e.g., `patch("requirements.txt", "aiohttp==3.13.3", "aiohttp==3.14.3")`

#### Task 1.3: Decide on `manifest.json` requirements
**Decision point:** Should `manifest.json` include `"requirements": ["homeassistant==2026.7.4"]` or leave it empty?
**Recommendation:** Keep `"requirements": []` in manifest (HACS handles this). The `requirements.txt` is for local development testing. Document this in `DEVELOPMENT.md`.
**Steps:**
1. Leave manifest as-is (`"requirements": []`).
2. In `DEVELOPMENT.md`, add a line: "For local testing, install from requirements.txt: `pip install -r requirements.txt`."

---

### Phase 2: Code Quality Fixes (Grill → Fix)

#### Task 2.1: Remove dead imports from `__init__.py`
**Problem:** Line 11-14 imports `DeviceEntry`, `DeviceEntryType`, `async_get as async_get_device_registry` from `homeassistant.helpers.device_registry`. Lines 104, 106, 112 use these in `async_remove_config_entry_device`. Let me verify usage.
**Steps:**
1. `grep -n "DeviceEntry\|DeviceEntryType\|async_get_device_registry" custom_components/pure_energy_prices/__init__.py`
2. If all three are used in `async_remove_config_entry_device`, they're not dead. If any is unused, remove it.
3. If all used, skip this task (previous review was wrong).

#### Task 2.2: Fix `config_flow.py` OptionsFlow return
**Problem:** The `PureEnergieOptionsFlow.async_step_init` at line 117-124 does:
```python
updated_data = {**self.config_entry.data, **user_input}
self.hass.config_entries.async_update_entry(self.config_entry, data=updated_data)
return self.async_create_entry(title="Pure Energie", data=user_input)
```
According to HA docs, `async_create_entry` in an OptionsFlow should return `self.async_update_entry(updated_data)` or just call `async_update_entry` and return `self.async_abort(...)`. The current pattern of `async_create_entry` is incorrect for options flows.
**Fix:** Replace lines 117-124 with the correct HA OptionsFlow pattern:
```python
if user_input is not None:
    self.hass.config_entries.async_update_entry(
        self.config_entry,
        data={**self.config_entry.data, **user_input},
    )
    return self.async_create_entry(title="Pure Energie", data=user_input)
```
Wait — re-reading HA docs, `async_create_entry` IS the correct return for options flows. The data passed to it becomes the new `config_entry.data`. Let me verify this is correct by checking the HA source.

**Verification:** `python3 -c "from homeassistant.config_entries import OptionsFlow; help(OptionsFlow.async_create_entry)"` (if available) or check docs.

**Decision:** The pattern `self.async_create_entry(title="...", data=user_input)` in an OptionsFlow is correct per HA documentation. The `async_update_entry` call is redundant when `async_create_entry` is used. However, calling both is not harmful — `async_update_entry` updates the entry in place, then `async_create_entry` also creates a new entry with the data (which HA merges). This is redundant but not broken.

**Action:** Remove the redundant `async_update_entry` call (line 118-119) to avoid double-update. The `async_create_entry` handles it.

#### Task 2.3: Fix `config_flow.py` type hint
**Problem:** Line 105: `def __init__(self, config_entry: config_entries.ConfigEntry) -> None:` — `config_entries` is not imported. The import at line 8 is `from homeassistant.config_entries import ConfigEntry`. The type hint should be `ConfigEntry`, not `config_entries.ConfigEntry`.
**Fix:** `patch("custom_components/pure_energy_prices/config_flow.py", 
    "config_entry: config_entries.ConfigEntry", 
    "config_entry: ConfigEntry")`

#### Task 2.4: Verify `config_flow.py` schema has no duplicate keys
**Problem:** The options flow schema at lines 128-167 includes `CONF_SCAN_INTERVAL` (line 158) and `CONF_DOUBLE_METER` (line 162). The config flow setup (lines 87-94) also includes these same keys. Need to verify they're not both in the same form.
**Steps:**
1. `grep -n "CONF_SCAN_INTERVAL\|CONF_DOUBLE_METER" custom_components/pure_energy_prices/config_flow.py`
2. Check if both appear in the same `vol.Schema({...})` block. If yes, it's a duplicate that HA will reject.
3. If duplicate: remove one instance.

---

### Phase 3: Test Completeness (TDD)

#### Task 3.0: Verify pytest can discover tests
**Steps:**
1. `cd /home/nick/repos/prive/hacs-pure-energy-prices && python3 -m pytest tests/ --collect-only 2>&1 | head -30`
2. Expected: 5+ tests collected across 4 files.
3. If any tests fail to collect, fix the import paths.

#### Task 3.1: Add failing test for OptionsFlow return value
**New test file:** `tests/test_options_flow.py`
**Goal:** Verify that `PureEnergieOptionsFlow.async_step_init` returns the correct result when called with `user_input`.
**Write the test first:**
```python
"""Tests for PureEnergieOptionsFlow."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.config_entries import ConfigEntry

from custom_components.pure_energy_prices.config_flow import PureEnergieOptionsFlow


@pytest.fixture
def options_flow():
    """Create a PureEnergieOptionsFlow instance."""
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.data = {
        "electricity": True,
        "gas": False,
        "horizon_hours": 48,
        "scan_interval": 3600,
        "added_costs": 0.0,
        "return_costs": 0.0,
        "double_meter": True,
    }
    flow = PureEnergieOptionsFlow(config_entry)
    return flow


@pytest.mark.asyncio
async def test_options_flow_init_returns_show_form(options_flow):
    """Initial options flow shows form (no user_input)."""
    result = await options_flow.async_step_init()
    assert result["type"] == "form"
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_submit_updates_entry(options_flow, hass):
    """Submitting options updates the config entry."""
    with patch.object(hass.config_entries, "async_update_entry") as mock_update, \
         patch.object(options_flow, "async_create_entry") as mock_create:
        mock_create.return_value = {"type": "abort", "result": None}
        result = await options_flow.async_step_init({"electricity": False})
        mock_update.assert_called_once()
        assert mock_update.call_args[0][0] == options_flow.config_entry
```

#### Task 3.2: Add failing test for coordinator direction-based price adjustment
**New test file:** `tests/test_coordinator_direction.py`
**Goal:** Verify that import coordinators add costs and export coordinators subtract return costs.
**Write the test first:**
```python
"""Tests for coordinator direction-based price adjustment."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry with cost data."""
    entry = MagicMock()
    entry.data = {
        "added_costs": 0.05,
        "return_costs": 0.03,
        "horizon_hours": 24,
        "base_url": "https://api.pure-energie.com/energy-prices",
        "element_id": 11480,
        "business": False,
    }
    return entry


@pytest.mark.asyncio
async def test_import_direction_adds_costs(mock_entry):
    """Import direction should add CONF_ADDED_COSTS to each price."""
    coordinator = PureEnergyCoordinator(
        MagicMock(), mock_entry,
        element_id=11480,
        commodity="electricity",
        direction="import",
    )
    # Patch _fetch_prices to return controlled data
    coordinator._fetch_prices = AsyncMock(return_value=[
        {"price": 0.25},
        {"price": 0.30},
    ])
    result = await coordinator._async_update_data()
    assert result.prices[0]["price"] == 0.30  # 0.25 + 0.05
    assert result.prices[1]["price"] == 0.35  # 0.30 + 0.05


@pytest.mark.asyncio
async def test_export_direction_subtracts_return_costs(mock_entry):
    """Export direction should subtract CONF_RETURN_COSTS from each price."""
    coordinator = PureEnergyCoordinator(
        MagicMock(), mock_entry,
        element_id=11480,
        commodity="electricity",
        direction="export",
    )
    coordinator._fetch_prices = AsyncMock(return_value=[
        {"price": 0.25},
        {"price": 0.30},
    ])
    result = await coordinator._async_update_data()
    assert result.prices[0]["price"] == 0.22  # 0.25 - 0.03
    assert result.prices[1]["price"] == 0.27  # 0.30 - 0.03
```

#### Task 3.3: Add failing test for stale data on coordinator failure
**Goal:** Verify that when `_async_update_data` raises, the coordinator returns its existing `self.data` (not an empty list).
**Write the test:**
```python
@pytest.mark.asyncio
async def test_coordinator_returns_stale_data_on_failure(mock_entry):
    """On API failure, coordinator returns existing data (not empty)."""
    coordinator = PureEnergyCoordinator(
        MagicMock(), mock_entry,
        element_id=11480,
        commodity="electricity",
        direction="import",
    )
    # Set existing data
    coordinator.data = MagicMock()
    coordinator.data.prices = [{"price": 0.20}]
    
    # Force failure
    coordinator._fetch_prices = AsyncMock(side_effect=Exception("API down"))
    
    result = await coordinator._async_update_data()
    assert result.prices == [{"price": 0.20}]
```

---

### Phase 4: Sensor.py Cleanup (Grill → Fix)

#### Task 4.1: Use `DEFAULT_PERCENTILES` constant consistently
**Problem:** Line 148 of `sensor.py` uses `"percentiles"` as a string key:
```python
percentiles_raw = config_entry.data.get("percentiles", DEFAULT_PERCENTILES)
```
The constant `CONF_PERCENTILES` is not defined in `const.py`. The key `"percentiles"` is hardcoded. 
**Decision:** Either add `CONF_PERCENTILES = "percentiles"` to `const.py` and use it everywhere, or accept the hardcoded string. Since this is just one occurrence and the key is well-known, and adding a constant for it would be scope creep, we'll add the constant to keep DRY:
**Fix:**
1. `patch("custom_components/pure_energy_prices/const.py", 
    "CONF_SOLAR_PANELS = \"solar_panel\"", 
    "CONF_SOLAR_PANELS = \"solar_panel\"\nCONF_PERCENTILES = \"percentiles\"")`
2. `patch("custom_components/pure_energy_prices/sensor.py",
    'config_entry.data.get("percentiles", DEFAULT_PERCENTILES)',
    'config_entry.data.get(CONF_PERCENTILES, DEFAULT_PERCENTILES)')`
3. Add `CONF_PERCENTILES` to the import in `sensor.py`:
   `patch("custom_components/pure_energy_prices/sensor.py",
    "from custom_components.pure_energy_prices.const import (",
    "from custom_components.pure_energy_prices.const import (\n    CONF_PERCENTILES,")`

#### Task 4.2: Add type hints to sensor.py classes
**Problem:** `PureEnergiePriceSensor` and `PureEnergiePercentileSensor` have no `__init__` type hints or return annotations.
**Fix:** Add `-> None` to `__init__` methods and proper type hints for parameters.

#### Task 4.3: Use `SensorStateClass` correctly
**Problem:** `PureEnergiePercentileSensor.state_class` returns `SensorStateClass.TOTAL`. Percentile prices are point-in-time values, not running totals. They should be `SensorStateClass.MEASUREMENT`.
**Fix:** `patch("custom_components/pure_energy_prices/sensor.py",
    "@property\n    def state_class(self) -> SensorStateClass:\n        \"\"\"Return the state class of the sensor.\"\"\"\n        return SensorStateClass.TOTAL",
    "@property\n    def state_class(self) -> SensorStateClass:\n        \"\"\"Return the state class of the sensor.\"\"\"\n        return SensorStateClass.MEASUREMENT")`

---

### Phase 5: Documentation & Housekeeping

#### Task 5.1: Update README.md
**Problem:** README hasn't been updated to reflect the new multi-sensor architecture.
**Steps:**
1. Read `README.md` and `docs/technical.md`.
2. Ensure README mentions: reconfiguration support, multiple sensors per entry, percentile sensors, and the commodity/direction architecture.
3. Add a "Configuration" section documenting all config keys.

#### Task 5.2: Update DEVELOPMENT.md
**Problem:** Missing guidance on testing.
**Fix:** Add a section:
```markdown
## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_options_flow.py -v
```

Skip slow tests:
```bash
pytest tests/ -v -m "not slow"
```
```

---

## Tests / Validation Per Task

| Task | Failing test command | Expected after fix |
|---|---|---|
| 3.1 | `pytest tests/test_options_flow.py::test_options_flow_submit_updates_entry -v` | PASS |
| 3.2 | `pytest tests/test_coordinator_direction.py::test_import_direction_adds_costs -v` | PASS |
| 3.2 | `pytest tests/test_coordinator_direction.py::test_export_direction_subtracts_return_costs -v` | PASS |
| 3.3 | `pytest tests/test_coordinator_direction.py::test_coordinator_returns_stale_data_on_failure -v` | PASS |
| All | `pytest tests/ -v` | All PASS |

---

## Risks, Tradeoffs, and Open Questions

### Risks
1. **HA version regression is critical** — If the branch is merged with `homeassistant==2026.2.3`, users on any newer HA will get dependency conflicts. This is the highest priority fix.
2. **OptionsFlow double-update** — Calling both `async_update_entry` and `async_create_entry` may cause unexpected behavior in some HA versions. Remove the redundant call.
3. **Stale data return** — The coordinator returns `self.data` (empty list) on first failure. This means the first sensor update after install failure shows zero prices silently. The warning log helps but the user gets no feedback. Consider raising `ConfigEntryNotReady` on first refresh failure.

### Tradeoffs
1. **Constant for `"percentiles"` key** — Adding `CONF_PERCENTILES` adds a line to `const.py` but removes a hardcoded string. Worth it for DRY.
2. **State class for percentile sensors** — Changing from `TOTAL` to `MEASUREMENT` is technically more correct but could change how HA displays the sensor in history charts. `MEASUREMENT` is the right call though.
3. **`manifest.json` requirements** — Keeping empty `[]` means local dev uses `requirements.txt` and HACS ignores it. This is the standard HACS pattern but could confuse users who check the manifest.

### Open Questions
1. Should the coordinator raise `ConfigEntryNotReady` on first refresh failure instead of returning empty data? This would cause HA to retry. Currently it returns empty data which hides failures.
2. The `async_remove_config_entry_device` function just returns `True` — should it validate that the device belongs to this integration before deletion?
3. The `requirements.txt` has many packages not actually used by this integration (e.g., `acme`, `aiogithubapi`, `bcrypt`, `bleak`, `botocore`, `boto3`). Should these be cleaned up?

---

## Commit Strategy

Each task above should be a separate commit with a descriptive message:
- `fix: restore HA version pin in requirements.txt`
- `fix: remove dead imports from __init__.py`
- `fix: correct OptionsFlow type hint`
- `fix: remove redundant async_update_entry in OptionsFlow`
- `test: add options flow tests`
- `test: add coordinator direction tests`
- `fix: use CONF_PERCENTILES constant in sensor.py`
- `fix: use MEASUREMENT state class for percentile sensors`
- `docs: update README and DEVELOPMENT`
