"""pytest fixtures shared across the engine test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_LIBRARY = DATA_DIR / "Data Library, 2025-10-18, 1960-2023.xlsx"
GWP_FILE = DATA_DIR / "IPCC GWPs AR4-AR6.xlsx"


@pytest.fixture(scope="session")
def data_paths() -> dict:
    """Return absolute paths to the two canonical xlsx files."""
    return {"data_library": str(DATA_LIBRARY), "gwp_file": str(GWP_FILE)}


@pytest.fixture(scope="session")
def loader(data_paths):
    from unitgps.engine import DataLoader

    return DataLoader(data_paths["data_library"], data_paths["gwp_file"])


@pytest.fixture(scope="session")
def combined_data(loader):
    """The Data Library with reciprocal edges synthesized — session-cached."""
    return loader.load_data_library()


@pytest.fixture(scope="session")
def node_attrs(loader, combined_data):
    return loader.get_units_attributes(combined_data)


@pytest.fixture(scope="session")
def gwps(loader):
    return loader.load_gwps()


@pytest.fixture(scope="session")
def graph(combined_data, node_attrs):
    """A built UnitGraph — session-cached so tests don't re-build ~3,600 edges."""
    from unitgps.engine import UnitGraph

    return UnitGraph(combined_data, node_attrs)


@pytest.fixture()
def empty_search_params() -> dict:
    """A neutral search-parameter dict that imposes no filters."""
    return {"Data Year": {"mode": "all", "values": []}}
