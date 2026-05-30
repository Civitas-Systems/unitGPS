"""UnitGPS engine — shared computational core.

Public API. UI variants under ``apps/`` should import only from here, never
from the internal modules directly.
"""

from .calculate import (
    AmbiguityError,
    calculate_conversion_factor,
    format_sig_figs,
    is_valid_parameter,
)
from .data import DataLoader
from .emissions import determine_conversion, determine_ghg_emissions, find_gwp
from .graph import UnitGraph
from .pathfinding import (
    convert_path_to_edge_tuples,
    identify_conversion_path,
    shortest_path_edges,
)

__all__ = [
    "AmbiguityError",
    "DataLoader",
    "UnitGraph",
    "calculate_conversion_factor",
    "convert_path_to_edge_tuples",
    "determine_conversion",
    "determine_ghg_emissions",
    "find_gwp",
    "format_sig_figs",
    "identify_conversion_path",
    "shortest_path_edges",
    "is_valid_parameter",
]
