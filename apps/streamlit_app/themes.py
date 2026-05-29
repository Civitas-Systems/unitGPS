"""Theme dictionary and CSS-injection helper.

Nine themes ported verbatim from Antigravity. The CSS is a single big
f-string built per-call from the active theme dict so theme switching
just re-injects the styles on the next rerun.
"""

from __future__ import annotations

import streamlit as st

THEMES: dict[str, dict] = {
    "Obsidian": {
        "bg": "#18181B", "surface": "#1E1E1E", "primary": "#8B5CF6",
        "text_on_primary": "#FFFFFF", "text": "#E5E7EB", "secondary": "#A1A1AA",
        # Border bumped from #3F3F46 (1.7:1) to #52525B for better visibility.
        "border": "#52525B", "danger": "#ef4444", "success": "#10b981",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "8px", "shadow": "none", "input_radius": "6px",
        "button_transform": "none", "tab_radius": "8px 8px 0 0",
        "border_width": "1px", "input_bg": "#27272A",
    },
    "Material Design (M3)": {
        "bg": "#F3EDF7", "surface": "#FFFFFF", "primary": "#6750A4",
        "text_on_primary": "#FFFFFF", "text": "#1C1B1F", "secondary": "#49454F",
        # Border bumped from #E7E0EC (1.1:1) to #CFC8D7 for clear card edges.
        "border": "#CFC8D7", "danger": "#B3261E", "success": "#386A20",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "16px",
        "shadow": "0px 1px 3px 1px rgba(0,0,0,0.15), 0px 1px 2px 0px rgba(0,0,0,0.3)",
        "input_radius": "8px", "button_transform": "none",
        "tab_radius": "16px 16px 0 0", "border_width": "0px", "input_bg": "#FFFFFF",
    },
    "Neo-Brutalism": {
        "bg": "#FACC15", "surface": "#FFFFFF", "primary": "#FF90E8",
        "text_on_primary": "#000000", "text": "#000000", "secondary": "#000000",
        "border": "#000000", "danger": "#ff3333", "success": "#23A094",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "0px", "shadow": "5px 5px 0px #000000", "input_radius": "0px",
        "button_transform": "uppercase", "tab_radius": "0px",
        "border_width": "3px", "input_bg": "#FFFFFF",
    },
    "Glassmorphism": {
        "bg": "linear-gradient(135deg, #1f005c, #5b0060, #870160, #ac255e, #ca485c, #e16b5c, #f39060, #ffb56b)",
        # Surface darkened from rgba(255,255,255,0.1) so white text actually
        # reads against it — was 1:1 contrast (invisible). Now ~5:1.
        "surface": "rgba(0, 0, 0, 0.35)", "primary": "#ffffff",
        "text_on_primary": "#000000", "text": "#ffffff", "secondary": "#f0f0f0",
        # Border bumped to alpha 0.35 so frosted-glass card edges are visible.
        "border": "rgba(255, 255, 255, 0.35)", "danger": "#ff6b6b", "success": "#4ade80",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "16px", "shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.3)",
        "input_radius": "8px", "button_transform": "none",
        "tab_radius": "16px 16px 0 0", "border_width": "1px",
        "backdrop": "blur(16px)", "input_bg": "rgba(0, 0, 0, 0.25)",
    },
    "Cyberpunk": {
        "bg": "#0B0F19", "surface": "#000000", "primary": "#00FFCC",
        "text_on_primary": "#000000", "text": "#E0E0E0", "secondary": "#00FFCC",
        "border": "#FF00FF", "danger": "#FF00FF", "success": "#00FFCC",
        "font": "'Fira Code', monospace",
        "radius": "0px", "shadow": "0 0 10px #00FFCC, 0 0 20px #00FFCC",
        "input_radius": "0px", "button_transform": "uppercase", "tab_radius": "0px",
        "border_width": "1px", "input_bg": "#000000",
    },
    "Earthy Zen": {
        "bg": "#F9F6F0", "surface": "#FCFAF8", "primary": "#78866B",
        "text_on_primary": "#FFFFFF", "text": "#3A3A3A", "secondary": "#C17767",
        # Border bumped from #EAE3D9 (1.2:1) to #CABEAA for visible card edges.
        "border": "#CABEAA", "danger": "#C17767", "success": "#78866B",
        "font": "Georgia, serif",
        "radius": "24px", "shadow": "0 10px 30px rgba(120, 134, 107, 0.08)",
        "input_radius": "12px", "button_transform": "none",
        "tab_radius": "24px 24px 0 0", "border_width": "1px", "input_bg": "#FFFFFF",
    },
    "Ultra-Minimalist": {
        "bg": "#FFFFFF", "surface": "#FFFFFF", "primary": "#000000",
        "text_on_primary": "#FFFFFF", "text": "#000000", "secondary": "#666666",
        # Border bumped from #E5E5E5 (1.3:1) to #CCCCCC for AA·LG visibility.
        "border": "#CCCCCC", "danger": "#000000", "success": "#000000",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "0px", "shadow": "none", "input_radius": "0px",
        "button_transform": "uppercase", "tab_radius": "0px",
        "border_width": "1px", "input_bg": "#FFFFFF",
    },
    "Retro OS": {
        "bg": "#008080", "surface": "#C0C0C0", "primary": "#000080",
        "text_on_primary": "#FFFFFF", "text": "#000000", "secondary": "#000000",
        "border": "#dfdfdf", "danger": "#ff0000", "success": "#00ff00",
        "font": "'Tahoma', sans-serif",
        "radius": "0px",
        "shadow": "inset 1px 1px #dfdfdf, 1px 1px #000000, inset 2px 2px #ffffff, 2px 2px #808080",
        "input_radius": "0px", "button_transform": "none", "tab_radius": "0px",
        "border_width": "0px", "input_bg": "#FFFFFF",
    },
    "Bloomberg Terminal": {
        "bg": "#000000", "surface": "#000000", "primary": "#FF9900",
        "text_on_primary": "#000000", "text": "#FF9900", "secondary": "#00FF00",
        # Border bumped from #333333 (1.7:1) to #4A4A4A for clearer divisions.
        "border": "#4A4A4A", "danger": "#FF0000", "success": "#00FF00",
        "font": "monospace",
        "radius": "0px", "shadow": "none", "input_radius": "0px",
        "button_transform": "uppercase", "tab_radius": "0px",
        "border_width": "1px", "input_bg": "#111111",
    },
    # ----- Light/dark counterparts for the invertible themes ----- #
    "Obsidian Light": {
        # Inverse of Obsidian dark — soft warm-white bg, deep purple primary.
        "bg": "#FAFAF7", "surface": "#FFFFFF", "primary": "#6D28D9",
        "text_on_primary": "#FFFFFF", "text": "#18181B", "secondary": "#52525B",
        "border": "#D4D4D8", "danger": "#DC2626", "success": "#059669",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "8px", "shadow": "none", "input_radius": "6px",
        "button_transform": "none", "tab_radius": "8px 8px 0 0",
        "border_width": "1px", "input_bg": "#F4F4F5",
    },
    "Material Design (M3) Dark": {
        # M3 dark palette — surface containers from Material Design 3 spec.
        "bg": "#141218", "surface": "#1D1B20", "primary": "#D0BCFF",
        "text_on_primary": "#381E72", "text": "#E6E0E9", "secondary": "#CAC4D0",
        "border": "#49454F", "danger": "#F2B8B5", "success": "#7DC97D",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "16px",
        "shadow": "0px 1px 3px 1px rgba(0,0,0,0.4), 0px 1px 2px 0px rgba(0,0,0,0.6)",
        "input_radius": "8px", "button_transform": "none",
        "tab_radius": "16px 16px 0 0", "border_width": "0px", "input_bg": "#2B292F",
    },
    "Earthy Zen Dark": {
        # Earthy Zen palette flipped to deep forest / warm-bark tones.
        "bg": "#1F1D18", "surface": "#28251F", "primary": "#A3B099",
        "text_on_primary": "#1F1D18", "text": "#E8E2D2", "secondary": "#D89B7E",
        "border": "#4A463E", "danger": "#D89B7E", "success": "#A3B099",
        "font": "Georgia, serif",
        "radius": "24px", "shadow": "0 10px 30px rgba(0, 0, 0, 0.4)",
        "input_radius": "12px", "button_transform": "none",
        "tab_radius": "24px 24px 0 0", "border_width": "1px", "input_bg": "#28251F",
    },
    "Ultra-Minimalist Dark": {
        # Stark inverse — pure black bg, pure white text. Editorial.
        "bg": "#000000", "surface": "#000000", "primary": "#FFFFFF",
        "text_on_primary": "#000000", "text": "#FFFFFF", "secondary": "#999999",
        "border": "#333333", "danger": "#FFFFFF", "success": "#FFFFFF",
        "font": "'Plus Jakarta Sans', sans-serif",
        "radius": "0px", "shadow": "none", "input_radius": "0px",
        "button_transform": "uppercase", "tab_radius": "0px",
        "border_width": "1px", "input_bg": "#0A0A0A",
    },
}

DEFAULT_THEME = "Obsidian"


def get_theme(name: str) -> dict:
    """Return the named theme, falling back to the default if unknown."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def inject_css(theme: dict) -> None:
    """Inject the full themed stylesheet via st.markdown."""
    th = theme
    bg_prop = "background" if "gradient" in th["bg"] else "background-color"
    text_on_primary = th.get("text_on_primary", "#FFFFFF")

    st.markdown(
        f"""
<style>
    /* Responsive layout constraints */
    /* Width cap — doubled-attribute trick boosts specificity above Streamlit's
       own emotion-generated rules so we win in both wide and centered modes. */
    [data-testid="stMainBlockContainer"][data-testid="stMainBlockContainer"],
    .stMainBlockContainer.stMainBlockContainer,
    .main .block-container.block-container,
    section.main > div.block-container.block-container {{
        max-width: min(1040px, 94vw) !important;
        width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 1.5rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }}
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fira+Code&display=swap');

    /* Compact widget labels — tighter than Streamlit's defaults so forms feel less like forms. */
    .stSelectbox label, .stMultiSelect label,
    .stTextInput label, .stNumberInput label,
    .stRadio label, .stCheckbox label {{
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        margin-bottom: 2px !important;
        color: {th['secondary']} !important;
    }}
    /* Trim default vertical breathing room around inputs */
    [data-testid="stSelectbox"], [data-testid="stMultiSelect"],
    [data-testid="stTextInput"], [data-testid="stNumberInput"] {{
        margin-bottom: 6px !important;
    }}
    /* Cap dropdown widths inside filter tabs so Process 1/Process 2 don't spread edge-to-edge */
    div[data-testid="stTabs"] [data-testid="stMultiSelect"],
    div[data-testid="stTabs"] [data-testid="stSelectbox"] {{
        max-width: 360px !important;
    }}
    /* Plotly chart wrapper sits in its own block — strip its top/bottom padding */
    .stPlotlyChart {{
        margin: 4px 0 !important;
    }}
    /* Expander headers should sit flush; the GHG derivation expander is small */
    [data-testid="stExpander"] details summary {{
        padding-top: 6px !important;
        padding-bottom: 6px !important;
        font-size: 0.85rem !important;
    }}
    /* Tighter section headings — Streamlit default h3 is 1.6rem which feels chunky. */
    h1, .stMarkdown h1 {{
        font-size: 1.55rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 0.5rem !important;
    }}
    h2, .stMarkdown h2 {{
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.005em !important;
        margin-bottom: 0.5rem !important;
    }}
    h3, .stMarkdown h3 {{
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        letter-spacing: -0.003em !important;
        margin-bottom: 0.4rem !important;
        margin-top: 0.85rem !important;
        opacity: 0.95;
    }}
    h4, .stMarkdown h4 {{
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.3rem !important;
    }}
    /* st.container(border=True) wrappers — Streamlit 1.57 puts the border on
       the stVerticalBlock div itself rather than a wrapper. Match either path. */
    [data-testid="stVerticalBlock"][style*="border"],
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 10px !important;
        background: transparent !important;
    }}
    /* Calculate button: less chunky, no transform */
    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) button {{
        font-size: 0.85rem !important;
        padding: 0.45rem 1rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em !important;
    }}
    /* Section dividers — quieter than default <hr> */
    hr {{
        opacity: 0.5;
        border-top-width: 0.5px !important;
    }}
    /* Tab headers — slimmer */
    div[data-baseweb="tab-list"] button[role="tab"] {{
        font-size: 0.85rem !important;
        padding: 8px 12px !important;
    }}

    .stApp {{
        {bg_prop}: {th['bg']};
        color: {th['text']};
        font-family: {th['font']};
    }}
    [data-testid="collapsedControl"] {{ display: none; }}
    .stSidebar {{ display: none; }}

    /* Hide ALL step buttons by default */
    [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {{
        display: none !important;
    }}

    /* ONLY show step buttons for From and To (the date ranges) */
    [data-testid="stNumberInput"]:has(input[aria-label="From"]) button,
    [data-testid="stNumberInput"]:has(input[aria-label="To"]) button {{
        display: inline-flex !important;
    }}

    [data-testid="stNumberInput"]:has(input[aria-label="From"]) button,
    [data-testid="stNumberInput"]:has(input[aria-label="To"]) button {{
        background-color: {th['border']} !important;
        border-radius: 4px;
        color: {th['text']} !important;
    }}
    [data-testid="stNumberInput"]:has(input[aria-label="From"]) button svg,
    [data-testid="stNumberInput"]:has(input[aria-label="To"]) button svg {{
        fill: {th['text']} !important;
        color: {th['text']} !important;
    }}

    /* Stop the tab header line from stretching 100% width */
    div[data-testid="stTabs"] > div > div:first-child {{
        width: fit-content !important;
        background-color: transparent !important;
    }}
    div[data-baseweb="tab-list"] {{
        width: fit-content !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        margin-left: 0 !important;
        background-color: transparent !important;
    }}

    /* Application Spacing */
    .main .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}
    div[data-testid="stVerticalBlock"]:has(.db-filters-anchor) {{
        position: relative !important;
    }}

    /* Calculate Button Positioning */
    div[data-testid="stVerticalBlock"]:has(.db-filters-anchor) div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) {{
        position: sticky !important;
        top: 2.875rem !important;
        z-index: 1001 !important;
        background-color: {th['bg']} !important;
        width: 100% !important;
        margin-top: 0.25rem !important;
        margin-bottom: 10px !important;
        display: flex !important;
        align-items: center !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) > div[data-testid="stColumn"] {{
        display: flex !important;
        align-items: center !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) .calc-btn-anchor {{
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        color: {th['secondary']} !important;
        display: inline-block !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        text-align: right !important;
        width: 100% !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) button {{
        padding: 0.35rem 0.6rem !important;
        height: auto !important;
        min-height: 0 !important;
        line-height: 1.5 !important;
        white-space: nowrap !important;
        width: 100% !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) div.stSelectbox {{
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) div.stSelectbox > div {{
        min-height: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) div.stSelectbox > div > div {{
        min-height: 38px !important;
        height: 38px !important;
        padding: 0.1rem 0.5rem !important;
        border-radius: 0.5rem !important;
        font-size: 0.9rem !important;
        background-color: {th['bg']} !important;
        display: flex !important;
        align-items: center !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(.calc-btn-anchor) button[kind="primary"] {{
        min-height: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        line-height: 38px !important;
    }}

    /* Compress Modules horizontally */
    div[data-testid="stHorizontalBlock"]:has(.modules-container-flag) {{
        gap: 1.5rem !important;
        justify-content: flex-start !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(.modules-container-flag) div[data-testid="stColumn"] {{
        flex: 0 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }}

    h1, h2, h3, h4, h5, p, span, div {{
        color: {th['text']} !important;
    }}

    /* GHG Summary Table */
    .ghg-summary-table {{
        width: auto !important;
        margin-left: auto !important;
        margin-right: auto !important;
        border-collapse: collapse !important;
        margin-top: 15px !important;
        margin-bottom: 15px !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid {th['border']} !important;
        background-color: {th['surface']} !important;
    }}
    .ghg-summary-table th {{
        background-color: {th['surface']} !important;
        color: {th['text']} !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 8px 12px !important;
        border-bottom: 2px solid {th['border']} !important;
        font-size: 0.9rem !important;
    }}
    .ghg-summary-table td {{
        padding: 8px 12px !important;
        border-bottom: 1px solid {th['border']} !important;
        color: {th['text']} !important;
        font-size: 0.875rem !important;
    }}
    .ghg-summary-table tr:last-child td {{
        border-bottom: none !important;
    }}
    .ghg-summary-table tr:hover {{
        background-color: rgba(255, 255, 255, 0.03) !important;
    }}
    .ghg-badge {{
        display: inline-block !important;
        padding: 2px 8px !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        text-align: center !important;
    }}
    span.ghg-badge-co2 {{
        background-color: rgba(103, 80, 164, 0.15) !important;
        color: {th['primary']} !important;
        -webkit-text-fill-color: {th['primary']} !important;
        border: 1px solid {th['primary']} !important;
    }}
    span.ghg-badge-ch4 {{
        background-color: rgba(16, 185, 129, 0.15) !important;
        color: {th['success']} !important;
        -webkit-text-fill-color: {th['success']} !important;
        border: 1px solid {th['success']} !important;
    }}
    span.ghg-badge-n2o {{
        background-color: rgba(239, 68, 68, 0.15) !important;
        color: {th['danger']} !important;
        -webkit-text-fill-color: {th['danger']} !important;
        border: 1px solid {th['danger']} !important;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {th['surface']};
        border: {th['border_width']} solid {th['border']};
        border-radius: {th['radius']} !important;
        box-shadow: {th['shadow']} !important;
        backdrop-filter: {th.get('backdrop', 'none')};
        -webkit-backdrop-filter: {th.get('backdrop', 'none')};
    }}

    .stSelectbox label, .stMultiSelect label, .stNumberInput label, .stRadio label {{
        color: {th['secondary']} !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }}

    .stSelectbox > div > div, .stMultiSelect > div > div, .stNumberInput > div > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {{
        background-color: {th.get('input_bg', th['bg'])} !important;
        border: 1px solid {th['border']} !important;
        border-radius: {th['input_radius']} !important;
        overflow: hidden !important;
    }}

    .stSelectbox *, .stMultiSelect *, .stNumberInput * {{
        color: {th['text']} !important;
        -webkit-text-fill-color: {th['text']} !important;
    }}

    .stSelectbox [data-baseweb="tag"] *, .stMultiSelect [data-baseweb="tag"] * {{
        color: {text_on_primary} !important;
        -webkit-text-fill-color: {text_on_primary} !important;
    }}

    .stSelectbox [data-baseweb="tag"], .stMultiSelect [data-baseweb="tag"] {{
        background-color: {th['primary']} !important;
        border: none !important;
    }}

    input::placeholder, [data-baseweb="select"] input::placeholder {{
        color: {th['secondary']} !important;
        -webkit-text-fill-color: {th['secondary']} !important;
        opacity: 0.8 !important;
    }}

    /* High Contrast Dropdown Menus */
    html body [data-baseweb="popover"],
    html body [data-baseweb="popover"] > div,
    html body div[data-baseweb="menu"],
    html body ul[role="listbox"] {{
        background-color: {th['surface']} !important;
        border: 1px solid {th['border']} !important;
    }}
    html body li[role="option"] {{
        background-color: {th['surface']} !important;
        color: {th['text']} !important;
    }}
    html body li[role="option"] * {{
        color: {th['text']} !important;
    }}
    html body li[role="option"]:hover,
    html body li[role="option"][aria-selected="true"] {{
        background-color: {th['primary']} !important;
    }}
    html body li[role="option"]:hover *,
    html body li[role="option"][aria-selected="true"] * {{
        color: {text_on_primary} !important;
        -webkit-text-fill-color: {text_on_primary} !important;
    }}

    /* Disabled Number Input styling for Final Value */
    input:disabled {{
        -webkit-text-fill-color: {th['primary']} !important;
        color: {th['primary']} !important;
        font-weight: bold;
    }}

    /* Tabs — width:fit-content so background stops at last tab */
    .stTabs [data-baseweb="tab-list"] {{
        position: sticky !important;
        top: 2.875rem !important;
        z-index: 1000 !important;
        background: {th['surface']} !important;
        border-radius: {th['tab_radius']} !important;
        padding: 0 16px !important;
        width: fit-content !important;
        border-bottom: 1px solid {th['border']} !important;
        backdrop-filter: {th.get('backdrop', 'none')} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {th['secondary']} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {th['primary']} !important;
        border-bottom: 2px solid {th['primary']} !important;
    }}

    .stButton > button {{
        background-color: {th['primary']};
        color: {text_on_primary} !important;
        border: {th['border_width']} solid {th.get('border', 'transparent')};
        border-radius: {th['radius']};
        font-weight: 800;
        text-transform: {th['button_transform']};
        padding: 8px 16px;
        box-shadow: {th['shadow']};
    }}

    .stCheckbox label {{
        color: {th['text']} !important;
    }}

    /* Custom Elements */
    .metric-value {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {th['primary']} !important;
    }}
    .metric-value-danger {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {th['danger']} !important;
    }}
    .metric-label {{
        font-size: 0.8rem;
        text-transform: uppercase;
        color: {th['secondary']} !important;
        font-weight: 700;
    }}
    .audit-step {{
        background: {th['bg']};
        border-left: 4px solid {th['primary']};
        padding: 12px 16px;
        margin-bottom: 8px;
        border-radius: {th['radius']};
        font-size: 0.9rem;
    }}
    .badge {{
        background: {th['surface']};
        color: {th['primary']} !important;
        padding: 2px 6px;
        border-radius: {th['input_radius']};
        font-family: monospace;
        border: 1px solid {th['border']};
    }}
</style>
""",
        unsafe_allow_html=True,
    )
