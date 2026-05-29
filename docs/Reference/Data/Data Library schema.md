---
type: data
file: data/Data Library, 2025-10-18, 1960-2023.xlsx
sheet: Sheet1
rows_raw: 3635
rows_after_reciprocals: 6056
columns: 40
status: current
generation: Claude
last_updated: 2026-05-21
tags: [data, schema, xlsx]
related:
  - "[[DataLoader.load_data_library]]"
  - "[[Reciprocal edges]]"
  - "[[Unit graph]]"
  - "[[Glossary#Set]]"
---

# Data Library schema

The canonical conversion edge list. One row per `(Numerator, Denominator)` directed conversion plus rich metadata for filtering. After [[DataLoader.load_data_library|loading + reciprocal synthesis]], every row becomes one edge in the [[Unit graph]].

## File

- **Path:** `v0.5-Claude/data/Data Library, 2025-10-18, 1960-2023.xlsx`
- **Sheet:** `Sheet1` (only one — implicit when `pd.read_excel` is called without `sheet_name`)
- **Rows (raw):** 3,635
- **Rows (after reciprocal synthesis):** 6,056
- **Columns:** 40 (38 retained after `Numerator Alias` and `Denominator Alias` are dropped)

## Row distribution by Set

| Set | Raw rows | Reciprocals added | Final rows |
|-----|----------|-------------------|-----------|
| `Emission Factors` | 3,024 | +2,306 | 5,330 |
| `Unit Conversion` | 294 | 0 (not reciprocated) | 294 |
| `Magnitude Adjustment` | 192 | 0 (not reciprocated) | 192 |
| `Chemical Properties` | 63 | +63 | 126 |
| `Global Warming Potentials` | 62 | +52 | 114 (unused — GWPs come from IPCC file) |
| **Total** | **3,635** | **+2,421** | **6,056** |

Why some Sets aren't reciprocated: see [[Reciprocal edges#Why exclude Unit Conversion and Magnitude Adjustment?]].

## Columns (in source order)

### Core math / classification

| Column | Type | Description |
|--------|------|-------------|
| `Value` | float | The numerical conversion factor. Null rows are dropped at load time. |
| `Conversion` | str | Human-readable form: `"<Numerator> per <Denominator>"`. Regenerated for reciprocal rows. |
| `Set` | str | One of: `Unit Conversion`, `Magnitude Adjustment`, `Emission Factors`, `Chemical Properties`, `Global Warming Potentials`. See [[Glossary#Set]]. |

### Source/Target identifiers

| Column | Type | Description |
|--------|------|-------------|
| `Numerator` | str | Target unit. Becomes the **target** node of the graph edge. |
| `Numerator Alias` | str | DROPPED at load. Unused. |
| `Numerator Dimension` | str | E.g. `Energy`, `Weight`. See [[Glossary#Dimension]]. |
| `Numerator System` | str | E.g. `SI`, `imperial`. |
| `Denominator` | str | Source unit. Becomes the **source** node of the graph edge. |
| `Denominator Alias` | str | DROPPED at load. Unused. |
| `Denominator Dimension` | str | Same dimension types. |
| `Denominator System` | str | Same system types. |

### Filter columns (user-exposed in the UI)

| Column | Type | Description |
|--------|------|-------------|
| `eGRID` | str | EPA regional electricity grid identifier. |
| `Data Year` | float | Vintage year of the EF, or NaN if not time-varying. See [[Temporal scope]]. |
| `GHG` | str | Gas this row's EF is for (`CO2`, `CH4`, `N2O`, `SF6`, `CO2e`, etc.). Most non-EF rows have NaN here. |
| `Release Date` | datetime | When the source dataset was published. |
| `Version` | str | Dataset version identifier. |
| `Agency` | str | Source agency. Today mostly `EPA`; the data prep notebooks reference DESNZ, eGRID, Green-e, OWID, AIB, ORNL-TEDB sources slated for future inclusion. |
| `Dataset` | str | Specific dataset within the agency. |
| `Updated` | datetime | When the row was last revised. |
| `Scope` | float | GHG Protocol Scope (1, 2, or 3). |
| `Category` | str | Sub-category within Process or Scope. |

### Resource / vehicle / chemical metadata

| Column | Type | Description |
|--------|------|-------------|
| `Asset` | str | Generic asset type. |
| `Mode` | str | Transport mode for logistics EFs. |
| `Vehicle1`, `Vehicle2` | str | Vehicle taxonomy. |
| `Source-Vehicle Category` | str | Higher-level vehicle category. |
| `Source-Vehicle Type` | str | Specific vehicle type. |
| `Process1`, `Process2` | str | Process taxonomy (production, combustion, etc.). |
| `Source-Process Type` | str | Higher-level process category. |
| `Chemical1`, `Chemical2` | str | Chemical taxonomy. |
| `Source-Chemical Category` | str | E.g. `Coal`, `Natural Gas`, `Petroleum`. |
| `Source-Chemical Type` | str | E.g. `Anthracite`, `Bituminous`, `Distillate Fuel Oil`. |
| `Source-Material Type` | str | Material type for non-chemical EFs. |
| `Country` | str | ISO-3 country code for region-specific data. |
| `Location in File` | str | Pointer back into the source spreadsheet (sheet name + cell). Provenance trail. |
| `Property` | str | For Chemical Properties rows: name of the property (`Heating Value`, `Density`, etc.). |
| `Formula` | str | Chemical formula. |
| `IPCC Report` | str | Which IPCC report a GWP row belongs to. (Note: the actual GWPs we use come from the separate IPCC GWPs file, not this column.) |

## How the columns relate to the engine

| Engine function | Reads from these columns |
|-----------------|--------------------------|
| [[DataLoader.load_data_library]] | All of them; drops `*Alias`, filters null `Value`, reciprocates non-static rows. |
| [[DataLoader.get_units_attributes]] | `Numerator`, `Numerator Dimension`, `Numerator System` (and Denominator counterparts). |
| [[UnitGraph]] | Builds nodes from `Numerator` + `Denominator`; carries every column as edge attrs. |
| [[UnitGraph.filter_graph]] | Filters by any column in `search_parameters`. Special-cases `Set`, `Data Year`, and Chemical Properties columns. |
| [[calculate_conversion_factor]] | Reads `Value`. Categorizes other columns into `source_keys` (Agency, Dataset, ...) and `general_params` (everything else) for the audit. |

## Data quality notes

- **`Agency`** is mostly `EPA` today. The data-prep notebooks (`01-prep_classification`, `02-classification`, `03-network`) document plans to fold in DESNZ, eGRID, Green-e, OWID, AIB, and ORNL-TEDB datasets — those are partially loaded as of the 2025-10-18 file.
- **`Source-Chemical Category` is sometimes null** when `Source-Chemical Type` is set. The Streamlit engine loader propagates the category from type for such rows; see the loader cleanup step in [[app#Engine loading (cached)]].
- **Null `Data Year`** is common and intentional — Unit Conversions, Magnitude Adjustments, and most Chemical Properties don't have a meaningful vintage.

## Schema evolution

- **Renames between Data Library versions** have historically been backward-compatible (no column deletions). The reciprocal-synthesis code uses substring matching on `Numerator`/`Denominator` for column renames, so adding new columns like `Numerator FooBar` works as long as the substring is present.
- **Adding a new Set** is breaking — would need updating the exclusion list in [[DataLoader.load_data_library]] and the carve-outs in [[UnitGraph.filter_graph]].

## See also

[[DataLoader.load_data_library]] · [[Reciprocal edges]] · [[Unit graph]] · [[UnitGraph.filter_graph]] · [[Temporal scope]] · [[Glossary#Set]] · [[Glossary#Dimension]]
