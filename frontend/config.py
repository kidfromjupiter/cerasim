"""CeraSim Frontend - Configuration and Constants"""

import sys
from pathlib import Path

# Add parent directory to Python path to import cerasim
sys.path.insert(0, str(Path(__file__).parent.parent))

from cerasim.config import SCENARIOS, SIM_DAYS, HOURS_PER_DAY

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "CeraSim — Supply Chain Simulator",
    "page_icon": "factory",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Custom CSS styling
STREAMLIT_CSS = """
<style>
    .main { padding: 2rem; }
    .stMetric { background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; }
</style>
"""

# Tab configuration
TABS = ["Summary", "Production", "Orders", "Financial", "Machines"]

# Session state defaults
SESSION_DEFAULTS = {
    "sim_results": None,
    "selected_scenario": "baseline",
}

# Export for convenience
__all__ = [
    "PAGE_CONFIG",
    "STREAMLIT_CSS",
    "TABS",
    "SESSION_DEFAULTS",
    "SCENARIOS",
    "SIM_DAYS",
    "HOURS_PER_DAY",
]
