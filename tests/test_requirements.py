"""Test that HA version pin is correct."""
import subprocess
import pytest


def test_ha_version_pin_not_downgraded():
    """Requirements.txt should pin homeassistant >= the main branch version."""
    result = subprocess.run(
        ["git", "show", "main:requirements.txt"],
        capture_output=True, text=True,
        cwd="/home/nick/repos/prive/hacs-pure-energy-prices",
    )
    main_version = None
    for line in result.stdout.splitlines():
        if line.startswith("homeassistant=="):
            main_version = line.split("==")[1]
            break
    assert main_version is not None, "homeassistant not pinned in main"

    result2 = subprocess.run(
        ["cat", "requirements.txt"],
        capture_output=True, text=True,
        cwd="/home/nick/repos/prive/hacs-pure-energy-prices",
    )
    branch_version = None
    for line in result2.stdout.splitlines():
        if line.startswith("homeassistant=="):
            branch_version = line.split("==")[1]
            break
    assert branch_version is not None, "homeassistant not pinned in feature branch"

    # Branch version must be >= main version
    assert branch_version >= main_version, (
        f"HA version downgraded: main={main_version}, branch={branch_version}"
    )
