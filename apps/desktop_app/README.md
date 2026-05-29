# Desktop variant (placeholder)

Planned: standalone executable that bundles the engine + a UI into a single
distributable. Two paths to evaluate:

**A. pywebview wrapper** — keep the Streamlit (or HTMX) app and load it in a
native window. Lowest implementation cost; reuses an existing UI variant.

**B. PyQt6 native** — fully native widgets. Highest control, biggest UI
work. Closer in spirit to the v0-v3 era of UnitGPS.

Packaged via PyInstaller, as in the earlier UnitGPS versions.

Not yet scaffolded.
