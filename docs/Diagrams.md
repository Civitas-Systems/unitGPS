---
type: reference
status: current
generation: Claude
last_updated: 2026-05-30
tags: [diagrams, architecture, overview]
---

# Diagrams

Mermaid diagrams of how UnitGPS works (render in GitHub and Obsidian). Companion to
[[METHODOLOGY]] and [[architecture]].

## End-to-end data flow

```mermaid
flowchart LR
  D[("Data Library + IPCC GWPs<br/>(xlsx / parquet)")] --> L["DataLoader<br/>load + synth reciprocals"]
  L --> G["UnitGraph<br/>MultiDiGraph"]
  U["User input<br/>source · target · modules · filters"] --> F["filter_graph<br/>(one rule)"]
  G --> F
  F --> P["pathfinding<br/>shortest paths"]
  P --> C["calculate<br/>product of edge values"]
  C --> A["Audit + result"]
  A --> R["Renderers<br/>stepper · GHG table · network"]
```

## GHG accounting (per result)

```mermaid
flowchart TB
  S["Source quantity<br/>e.g. 1 mmBTU anthracite"]
  S --> A["CO₂ route<br/>(must cross an EF)"]
  S --> B["CH₄ route<br/>(must cross an EF)"]
  S --> C["N₂O route<br/>(must cross an EF)"]
  A -->|"Mass × GWP"| EA["CO₂e"]
  B -->|"Mass × GWP"| EB["CO₂e"]
  C -->|"Mass × GWP"| EC["CO₂e"]
  EA --> T["Total CO₂e"]
  EB --> T
  EC --> T
```

## The one filter rule

```mermaid
flowchart TD
  E["An edge in the graph"] --> Q{"Set is<br/>infrastructure?<br/>(unit conv / magnitude)"}
  Q -->|yes| K["Keep (always)"]
  Q -->|no| M{"Matches every<br/>selected filter?<br/>(blank = exclude)"}
  M -->|no| X["Drop"]
  M -->|yes| Y{"Data Year ok?<br/>(blank = wildcard)"}
  Y -->|no| X
  Y -->|yes| K
```
