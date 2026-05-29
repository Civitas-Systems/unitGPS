"""Data loading and preparation.

Loads the canonical Data Library xlsx and the IPCC GWPs xlsx, applies the
schema fixups Antigravity established (drop alias columns, drop null Values,
synthesize reciprocal edges for non-static rows), and returns DataFrames
ready for graph construction.

Ported from Antigravity/engine/data.py — behavior preserved verbatim.
"""

from __future__ import annotations

import pandas as pd


class DataLoader:
    """Load the Data Library and IPCC GWPs from disk."""

    def __init__(self, data_library_path: str, gwp_file_path: str) -> None:
        self.data_library_path = data_library_path
        self.gwp_file_path = gwp_file_path

    def load_data_library(self) -> pd.DataFrame:
        """Load the main Data Library and create reciprocals.

        Reciprocals are synthesized for every row whose ``Set`` is NOT one of
        ``Unit Conversion``, ``Magnitude Adjustment``, or ``Unit Conversions`` —
        i.e. emission factors and chemical properties get their inverse edges
        added so the graph is naturally bidirectional for those measurements.
        Static unit conversions already exist in both directions in the source.
        """
        if self.data_library_path.endswith(".parquet"):
            data = pd.read_parquet(self.data_library_path)
        else:
            data = pd.read_excel(self.data_library_path)

        data = data.drop(columns=["Numerator Alias", "Denominator Alias"], errors="ignore")
        data = data.loc[~data["Value"].isnull()]

        # Create reciprocals for non-unit-conversions
        sets_to_exclude = ["Unit Conversion", "Magnitude Adjustment", "Unit Conversions"]
        reciprocal = data[~data["Set"].isin(sets_to_exclude)].copy()

        new_column_names: dict[str, str] = {}
        for col in reciprocal.columns:
            if "Numerator" in col:
                new_column_names[col] = col.replace("Numerator", "Denominator")
            elif "Denominator" in col:
                new_column_names[col] = col.replace("Denominator", "Numerator")

        reciprocal = reciprocal.rename(columns=new_column_names)
        reciprocal["Conversion"] = reciprocal["Numerator"] + " per " + reciprocal["Denominator"]
        reciprocal["Value"] = 1 / reciprocal["Value"]

        combined_data = pd.concat([data, reciprocal], ignore_index=True)
        return combined_data

    def get_units_attributes(self, df: pd.DataFrame) -> dict:
        """Extract unique units and their dimensions/systems from the DataFrame.

        Returns ``{unit_name: {Unit Dimension, Unit System, Color}}`` where
        color is a dimension-keyed default suitable for graph visualization.
        """
        units_num = df[["Numerator", "Numerator Dimension", "Numerator System"]].rename(
            columns={
                "Numerator": "Unit",
                "Numerator Dimension": "Dimension",
                "Numerator System": "System",
            }
        )
        units_den = df[["Denominator", "Denominator Dimension", "Denominator System"]].rename(
            columns={
                "Denominator": "Unit",
                "Denominator Dimension": "Dimension",
                "Denominator System": "System",
            }
        )
        units_all = pd.concat([units_num, units_den]).drop_duplicates().dropna(subset=["Unit"])

        dimension_colors = {
            "Time": "black",
            "Area": "blue",
            "Length": "green",
            "Energy": "pink",
            "Volume": "orange",
            "Weight": "purple",
            "Power": "brown",
            "Logistics": "cyan",
        }

        attr_dict: dict[str, dict] = {}
        for _, row in units_all.iterrows():
            dim = row["Dimension"]
            sys_name = row["System"]
            color = dimension_colors.get(dim, "grey")
            attr_dict[row["Unit"]] = {
                "Unit Dimension": dim,
                "Unit System": sys_name,
                "Color": color,
            }
        return attr_dict

    def load_gwps(self) -> pd.DataFrame:
        """Load Global Warming Potentials data.

        The IPCC xlsx ``Data`` sheet ships with an ``Indicator`` column of the
        form ``"AR5-100"``; this method splits that into separate
        ``Assessment Report`` and ``Time Horizon`` columns and drops the
        long-form chemical name column.
        """
        gwps_data = pd.read_excel(self.gwp_file_path, sheet_name="Data")

        if "Indicator" in gwps_data.columns and "-" in str(gwps_data["Indicator"].iloc[0]):
            gwps_data[["Assessment Report", "Time Horizon"]] = gwps_data["Indicator"].str.split(
                "-", expand=True
            )
            gwps_data = gwps_data.drop(
                columns=["Indicator", "Long Chemical Name"], errors="ignore"
            )

        return gwps_data
