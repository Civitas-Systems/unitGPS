---
type: reference
status: current
generation: Claude
last_updated: 2026-05-30
tags: [reference, data, provenance, licensing]
---

# Provenance & licensing

## Sources
The Data Library is **curated by Dave** from authoritative sources:
- **U.S. EPA — GHG Emission Factors Hub** (stationary combustion, etc.)
- **U.S. EPA — eGRID** (regional electricity factors)
- **IPCC AR4 / AR5 / AR6** (Global Warming Potentials)
- **NIST SP 811 / SI** (unit conversions)

Every emission-factor result surfaces its agency, dataset, and release/updated dates in
the audit, so individual values are traceable. See [[References]], [[QA_NOTES]].

## Licensing
- **Code** — marked Proprietary (see `pyproject.toml`, `CITATION.cff`).
- **Reference data** — EPA, IPCC, and NIST materials are U.S. government works / publicly
  available; verify each source's specific attribution and reuse terms before
  redistributing data. The **curated compilation** (selection, cleaning, schema) is Dave's.

## Action for the data pipeline
As the automation pipeline finalises, record per-dataset: exact source URL, version/
vintage, retrieval date, and license terms — so each value is citation-complete. This is
the provenance half of the [[QA_NOTES]] forward framework.
