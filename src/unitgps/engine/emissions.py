"""GHG emissions and high-level conversion wrappers.

The two public entry points (``determine_conversion`` and
``determine_ghg_emissions``) chain together filter_graph → pathfinding →
calculate, and return a single dict that the UI can render directly.
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd

from .calculate import AmbiguityError, calculate_conversion_factor
from .pathfinding import convert_path_to_edge_tuples, identify_conversion_path


def find_gwp(
    gwps_data: pd.DataFrame,
    ghg: str,
    assessment_report: str = "AR5",
    time_horizon: str = "100",
) -> float | None:
    """Look up the Global Warming Potential for a specific gas.

    Falls back to ``1.0`` for CO2 if the row is missing (CO2 is the reference
    gas — GWP is 1.0 by definition).
    """
    try:
        gwp_row = gwps_data.loc[
            (gwps_data["GHG"] == ghg)
            & (gwps_data["Assessment Report"] == assessment_report)
            & (gwps_data["Time Horizon"] == time_horizon)
        ]
        if gwp_row.empty:
            if ghg == "CO2":
                return 1.0
            return None
        return float(gwp_row["GWP"].values[0])
    except Exception:
        return None


def determine_ghg_emissions(
    graph_engine,
    search_parameters: dict,
    source: str,
    target: str,
    starting_value: float,
    gwps_data: pd.DataFrame,
    ghgs: Sequence[str] = ("CO2", "CH4", "N2O"),
    gwp_report: str = "AR5",
    gwp_horizon: str = "100",
    edge_picks: dict | None = None,
) -> dict:
    """Route each GHG independently, weight by GWP, and sum to CO2e.

    Returns:
        {
          'results': {ghg: {'Mass', 'GWP', 'CO2e', 'Path', 'Audit', 'Error'}},
          'total_co2e': float,
          'valid_calc': bool   # False if any GHG was ambiguous or CO2 failed
        }
    """
    emissions_results: dict = {}
    total_co2e = 0.0

    for ghg in ghgs:
        emissions_results[ghg] = {
            "Mass": None,
            "GWP": None,
            "CO2e": None,
            "Path": None,
            "Audit": None,
            "Error": None,
        }
        current_params = search_parameters.copy()
        current_params["GHG"] = ghg

        try:
            F = graph_engine.filter_graph(current_params, include_emission_factors=True)
            shortest_paths_nodes = identify_conversion_path(F, source, target)
            emissions_results[ghg]["Path"] = shortest_paths_nodes

            calc_results = calculate_conversion_factor(
                F,
                convert_path_to_edge_tuples(shortest_paths_nodes),
                starting_value,
                edge_picks=edge_picks,
            )
            if calc_results:
                emissions_results[ghg]["Mass"] = calc_results[0]["ultimate_value"]
                emissions_results[ghg]["Audit"] = calc_results[0]
        except AmbiguityError as e:
            emissions_results[ghg]["Error"] = "AmbiguityError"
            emissions_results[ghg]["Audit"] = e.args[0] if e.args else None
        except Exception as e:  # noqa: BLE001 — engine deliberately swallows per-GHG errors
            emissions_results[ghg]["Error"] = str(e)

    has_any_mass = any(emissions_results[g]["Mass"] is not None for g in ghgs)
    has_ambiguity = any(emissions_results[g]["Error"] == "AmbiguityError" for g in ghgs)

    for ghg in ghgs:
        mass = emissions_results[ghg]["Mass"]
        emissions_results[ghg]["GWP"] = find_gwp(
            gwps_data,
            ghg,
            assessment_report=gwp_report,
            time_horizon=gwp_horizon,
        )
        if mass is not None and emissions_results[ghg]["GWP"] is not None:
            val = mass * emissions_results[ghg]["GWP"]
            emissions_results[ghg]["CO2e"] = val
            total_co2e += val

    valid_global_calc = has_any_mass and not has_ambiguity
    if "CO2" in emissions_results and emissions_results["CO2"]["Mass"] is None:
        valid_global_calc = False

    return {
        "results": emissions_results,
        "total_co2e": total_co2e,
        "valid_calc": valid_global_calc,
    }


def determine_conversion(
    graph_engine,
    search_parameters: dict,
    source: str,
    target: str,
    starting_value: float,
    edge_picks: dict | None = None,
) -> dict:
    """High-level wrapper around filter_graph → pathfinding → calculate.

    Returns one of:
        {'status': 'success',           'data': [audit_dict, ...]}
        {'status': 'ambiguity_error',   'data': <details>}
        {'status': 'error',             'message': str}
    """
    current_params = search_parameters.copy()

    try:
        F = graph_engine.filter_graph(current_params, include_emission_factors=False)
        shortest_paths_nodes = identify_conversion_path(F, source, target)

        calc_results = calculate_conversion_factor(
            F,
            convert_path_to_edge_tuples(shortest_paths_nodes),
            starting_value,
            edge_picks=edge_picks,
        )
        if calc_results:
            return {"status": "success", "data": calc_results}
        return {"status": "error", "message": "No path found"}
    except AmbiguityError as e:
        return {"status": "ambiguity_error", "data": e.args[0] if e.args else None}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "message": str(e)}
